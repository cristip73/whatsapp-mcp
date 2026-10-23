package main

import (
	"bytes"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"go.mau.fi/whatsmeow/types/events"
)

// Tests for POST /api/qr (QR on request, daemon mode) and phone_reached_bridge.

func qrHarness(t *testing.T, f *fakeClient, tweak func(*pairingController)) (*harness, string) {
	t.Helper()
	dir := t.TempDir()
	h := startHarness(t, f, false, nil, func(pc *pairingController) {
		pc.qrDir = dir
		pc.qrFirstTTL = 200 * time.Millisecond
		pc.qrNextTTL = 200 * time.Millisecond
		pc.socketCap = 10 * time.Second
		if tweak != nil {
			tweak(pc)
		}
	})
	return h, dir
}

func (h *harness) mustQR() qrResult {
	h.t.Helper()
	type out struct {
		r   qrResult
		err error
	}
	ch := make(chan out, 1)
	go func() {
		r, err := h.pc.RequestQR()
		ch <- out{r, err}
	}()
	select {
	case o := <-ch:
		if o.err != nil {
			h.t.Fatalf("RequestQR: %v", o.err)
		}
		return o.r
	case <-time.After(5 * time.Second):
		h.t.Fatalf("RequestQR blocked")
		return qrResult{}
	}
}

func qrImages(t *testing.T, dir string) []string {
	t.Helper()
	m, err := filepath.Glob(filepath.Join(dir, "pairing-qr-*.png"))
	if err != nil {
		t.Fatal(err)
	}
	return m
}

// (a) /api/qr twice -> same socket, current ref.
func TestQRTwiceSameSocket(t *testing.T) {
	f := newFakeClient()
	h, _ := qrHarness(t, f, func(pc *pairingController) { pc.qrFirstTTL = 5 * time.Second })
	q1 := h.mustQR()
	if q1.qr != "qr-1-1" || q1.refIndex != 1 || q1.refTotal != 6 || q1.refsLeft != 5 || q1.sameSocket {
		t.Fatalf("first QR: %+v", q1)
	}
	if q1.expiresIn < 4 || q1.expiresIn > 5 {
		t.Fatalf("expires_in_sec = %d, want about 5", q1.expiresIn)
	}
	if !strings.Contains(q1.textQR, "▀") && !strings.Contains(q1.textQR, "▄") && !strings.Contains(q1.textQR, "█") {
		t.Fatalf("text_qr has no half blocks")
	}
	q2 := h.mustQR()
	if q2.qr != q1.qr || !q2.sameSocket || q2.imagePath != q1.imagePath {
		t.Fatalf("second QR should be the same ref on the same socket: %+v", q2)
	}
	if connects, _, live, handlers, _ := f.snapshot(); connects != 1 || live != 0 || handlers != 1 {
		t.Fatalf("connects=%d live disconnects=%d handlers=%d, want 1/0/1", connects, live, handlers)
	}
	st := h.status()
	if st["state"] != pairStateQRShown || st["refs_left"] != 5 {
		t.Fatalf("status: %v", st)
	}
	if e, ok := st["qr_expires_in_sec"].(int); !ok || e < 1 {
		t.Fatalf("qr_expires_in_sec: %v", st["qr_expires_in_sec"])
	}
}

// Rotation by time: same socket, next ref, new image file (old one gone).
func TestQRRotatesByTime(t *testing.T) {
	f := newFakeClient()
	h, dir := qrHarness(t, f, nil)
	q1 := h.mustQR()
	time.Sleep(300 * time.Millisecond) // first ref lives 200 ms, second until 400 ms
	q2 := h.mustQR()
	if q2.qr != "qr-1-2" || q2.refIndex != 2 || q2.refsLeft != 4 || !q2.sameSocket {
		t.Fatalf("after rotation: %+v", q2)
	}
	if q2.imagePath == q1.imagePath {
		t.Fatalf("rotated ref reused the old image path")
	}
	if imgs := qrImages(t, dir); len(imgs) != 1 || imgs[0] != q2.imagePath {
		t.Fatalf("images on disk = %v, want only %s", imgs, q2.imagePath)
	}
}

// (b) refs used up (socket still open) or socket closed by server -> new socket.
func TestQRRefsUsedUpOpensNewSocket(t *testing.T) {
	f := newFakeClient()
	h, _ := qrHarness(t, f, func(pc *pairingController) {
		pc.qrFirstTTL = 50 * time.Millisecond
		pc.qrNextTTL = 50 * time.Millisecond
	})
	h.mustQR()
	time.Sleep(400 * time.Millisecond) // 6 refs x 50 ms
	q := h.mustQR()
	if q.qr != "qr-2-1" || q.sameSocket {
		t.Fatalf("after refs ran out: %+v", q)
	}
	if connects, _, _, handlers, _ := f.snapshot(); connects != 2 || handlers != 1 {
		t.Fatalf("connects=%d handlers=%d", connects, handlers)
	}
}

func TestQRServerCloseThenNewSocket(t *testing.T) {
	f := newFakeClient()
	h, dir := qrHarness(t, f, nil)
	h.mustQR()
	f.serverClose()
	waitFor(t, time.Second, "idle after server close", func() bool { return h.status()["state"] == pairStateIdle })
	if imgs := qrImages(t, dir); len(imgs) != 0 {
		t.Fatalf("images left after the QR socket closed: %v", imgs)
	}
	if _, ok := h.status()["qr_expires_in_sec"]; ok {
		t.Fatalf("qr_expires_in_sec shown while idle")
	}
	q := h.mustQR()
	if q.qr != "qr-2-1" || q.sameSocket {
		t.Fatalf("after server close: %+v", q)
	}
}

// (c) an active code -> QR takes over (code socket closed), and back.
func TestQRTakesOverFromCode(t *testing.T) {
	f := newFakeClient()
	h, dir := qrHarness(t, f, nil)
	c := h.mustCode("40722000111")
	q := h.mustQR()
	if !q.switched || q.sameSocket || q.qr != "qr-2-1" {
		t.Fatalf("QR after code: %+v", q)
	}
	if connects, _, live, _, connected := f.snapshot(); connects != 2 || live != 1 || !connected {
		t.Fatalf("connects=%d live disconnects=%d connected=%v, want 2/1/true", connects, live, connected)
	}
	if st := h.status(); st["state"] != pairStateQRShown || st["code_age_sec"] != nil {
		t.Fatalf("status after switch: %v", st)
	}
	// Code again for the same number: the old code died with its socket -> new code, QR images gone.
	c2 := h.mustCode("40722000111")
	if c2.reused || c2.code == c.code {
		t.Fatalf("code after QR: %+v", c2)
	}
	if imgs := qrImages(t, dir); len(imgs) != 0 {
		t.Fatalf("images left after switching to code: %v", imgs)
	}
}

// (d) PNG created (0600, valid PNG, 8 px per module + margin) and removed on PairSuccess; stale files
// from a previous run are removed at start.
func TestQRImageCreatedAndRemoved(t *testing.T) {
	f := newFakeClient()
	dir := t.TempDir()
	stale := filepath.Join(dir, "pairing-qr-1.png")
	if err := os.WriteFile(stale, []byte("old"), 0600); err != nil {
		t.Fatal(err)
	}
	h := startHarness(t, f, false, nil, func(pc *pairingController) { pc.qrDir = dir; pc.qrFirstTTL = 5 * time.Second })
	if _, err := os.Stat(stale); !os.IsNotExist(err) {
		t.Fatalf("stale image not removed at start")
	}
	q := h.mustQR()
	if filepath.Dir(q.imagePath) != dir || !strings.HasPrefix(filepath.Base(q.imagePath), "pairing-qr-") {
		t.Fatalf("image_path = %q", q.imagePath)
	}
	fi, err := os.Stat(q.imagePath)
	if err != nil {
		t.Fatal(err)
	}
	if fi.Mode().Perm() != 0600 {
		t.Fatalf("mode = %v, want 0600", fi.Mode().Perm())
	}
	data, _ := os.ReadFile(q.imagePath)
	img, err := png.Decode(bytes.NewReader(data))
	if err != nil {
		t.Fatalf("not a PNG: %v", err)
	}
	w := img.Bounds().Dx()
	if w != img.Bounds().Dy() || w%8 != 0 || w < (21+8)*8 {
		t.Fatalf("PNG %dx%d: want square, 8 px per module, at least version 1 + margin", w, img.Bounds().Dy())
	}
	// Corner pixel is the white margin.
	if r, g, b, _ := img.At(0, 0).RGBA(); r != 0xffff || g != 0xffff || b != 0xffff {
		t.Fatalf("corner not white")
	}
	f.pairSuccess()
	select {
	case ok := <-h.done:
		h.done <- ok
	case <-time.After(time.Second):
		t.Fatalf("Run did not return after PairSuccess")
	}
	if imgs := qrImages(t, dir); len(imgs) != 0 {
		t.Fatalf("images left after PairSuccess: %v", imgs)
	}
}

// (e) RotateADVSecret is applied to the ref being served and to the next ones.
func TestQRRotateADVSecretApplied(t *testing.T) {
	f := newFakeClient()
	h, _ := qrHarness(t, f, nil)
	q1 := h.mustQR()
	if q1.qr != "qr-1-1" {
		t.Fatalf("first QR: %+v", q1)
	}
	f.dispatch(&events.RotateADVSecret{OldSecret: "qr-1", NewSecret: "rot-1"})
	time.Sleep(30 * time.Millisecond)
	q2 := h.mustQR()
	if q2.qr != "rot-1-1" || !q2.sameSocket {
		t.Fatalf("served ref not rotated: %+v", q2)
	}
	if q2.imagePath == q1.imagePath {
		t.Fatalf("rotated ref kept the old image")
	}
	time.Sleep(250 * time.Millisecond)
	if q3 := h.mustQR(); q3.qr != "rot-1-2" {
		t.Fatalf("next ref not rotated: %+v", q3)
	}
}

// phone_reached_bridge: set by the phone's notification (through the logger), kept when later
// events overwrite last_event, reset by a new code and by PairSuccess.
func TestPhoneReachedBridge(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	if h.status()["phone_reached_bridge"] != false {
		t.Fatalf("initial phone_reached_bridge: %v", h.status())
	}
	h.mustCode("40722000111")
	root := newPairingLogger(recLogger{mu: &sync.Mutex{}, buf: &bytes.Buffer{}}, h.pc.pairDebug)
	root.onEvent = h.pc.loggerEvent
	root.Sub("Recv").Debugf("%s", `<notification from="s.whatsapp.net" type="link_code_companion_reg"><link_code_companion_reg stage="primary_hello"/></notification>`)
	if st := h.status(); st["phone_reached_bridge"] != true || st["last_event"] != "notification received" {
		t.Fatalf("after notification: %v", st)
	}
	f.serverClose() // overwrites last_event; the flag stays
	waitFor(t, time.Second, "idle", func() bool { return h.status()["state"] == pairStateIdle })
	if h.status()["phone_reached_bridge"] != true {
		t.Fatalf("flag lost after a later event: %v", h.status())
	}
	h.mustCode("40722000111")
	if h.status()["phone_reached_bridge"] != false {
		t.Fatalf("flag not reset by a new code: %v", h.status())
	}
	h.pc.loggerEvent("notification received")
	f.pairSuccess()
	select {
	case ok := <-h.done:
		h.done <- ok
	case <-time.After(time.Second):
		t.Fatalf("Run did not return after PairSuccess")
	}
	if h.status()["phone_reached_bridge"] != false {
		t.Fatalf("flag not reset by PairSuccess: %v", h.status())
	}
}
