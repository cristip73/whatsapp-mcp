package main

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"go.mau.fi/whatsmeow"
	"go.mau.fi/whatsmeow/types/events"
	waLog "go.mau.fi/whatsmeow/util/log"
)

// ---------------------------------------------------------------------------------------------
// Fake client that behaves like whatsmeow where it matters: our Disconnect emits no event, a server
// close emits events.Disconnected, Connect sends one events.QR from another goroutine.

type fakeClient struct {
	mu              sync.Mutex
	handlers        map[uint32]func(any)
	nextID          uint32
	connected       bool
	session         bool
	connects        int
	disconnects     int // calls to Disconnect
	disconnectsLive int // calls to Disconnect while a socket was alive
	pairCalls       int
	codeSeq         int
	autoQR          bool
	connectErr      error
	pairBlock       bool
	callers         map[uint64]bool // goroutines that called Connect / Disconnect / PairPhone
}

func newFakeClient() *fakeClient {
	return &fakeClient{handlers: map[uint32]func(any){}, autoQR: true, callers: map[uint64]bool{}}
}

func goid() uint64 {
	buf := make([]byte, 64)
	buf = buf[:runtime.Stack(buf, false)]
	fields := strings.Fields(string(buf))
	id, _ := strconv.ParseUint(fields[1], 10, 64)
	return id
}

func (f *fakeClient) Connect() error {
	f.mu.Lock()
	f.callers[goid()] = true
	if f.connectErr != nil {
		f.mu.Unlock()
		return f.connectErr
	}
	if f.connected {
		f.mu.Unlock()
		return whatsmeow.ErrAlreadyConnected
	}
	f.connected = true
	f.connects++
	n := f.connects
	auto := f.autoQR
	f.mu.Unlock()
	if auto {
		go f.dispatch(&events.QR{Codes: []string{
			fmt.Sprintf("qr-%d-1", n), fmt.Sprintf("qr-%d-2", n), fmt.Sprintf("qr-%d-3", n),
			fmt.Sprintf("qr-%d-4", n), fmt.Sprintf("qr-%d-5", n), fmt.Sprintf("qr-%d-6", n)}})
	}
	return nil
}

func (f *fakeClient) Disconnect() {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.callers[goid()] = true
	f.disconnects++
	if f.connected {
		f.disconnectsLive++
	}
	f.connected = false // expected disconnect: no event, like whatsmeow
}

func (f *fakeClient) IsConnected() bool {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.connected
}

func (f *fakeClient) HasSession() bool {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.session
}

func (f *fakeClient) PairPhone(ctx context.Context, phone string, _ bool, _ whatsmeow.PairClientType, _ string) (string, error) {
	f.mu.Lock()
	f.callers[goid()] = true
	f.pairCalls++
	block := f.pairBlock
	connected := f.connected
	f.codeSeq++
	code := fmt.Sprintf("CODE-%04d", f.codeSeq)
	f.mu.Unlock()
	if block {
		<-ctx.Done()
		return "", ctx.Err()
	}
	if !connected {
		return "", errors.New("websocket not connected")
	}
	return code, nil
}

func (f *fakeClient) SendPasskeyConfirmation(context.Context) error { return nil }

func (f *fakeClient) AddEventHandler(fn func(any)) uint32 {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.nextID++
	f.handlers[f.nextID] = fn
	return f.nextID
}

func (f *fakeClient) RemoveEventHandler(id uint32) bool {
	f.mu.Lock()
	defer f.mu.Unlock()
	_, ok := f.handlers[id]
	delete(f.handlers, id)
	return ok
}

func (f *fakeClient) dispatch(evt any) {
	f.mu.Lock()
	hs := make([]func(any), 0, len(f.handlers))
	for _, h := range f.handlers {
		hs = append(hs, h)
	}
	f.mu.Unlock()
	for _, h := range hs {
		h(evt)
	}
}

func (f *fakeClient) serverClose() {
	f.mu.Lock()
	f.connected = false
	f.mu.Unlock()
	f.dispatch(&events.Disconnected{})
}

func (f *fakeClient) silentDrop() {
	f.mu.Lock()
	f.connected = false
	f.mu.Unlock()
}

func (f *fakeClient) pairSuccess() {
	f.mu.Lock()
	f.session = true
	f.mu.Unlock()
	f.dispatch(&events.PairSuccess{})
}

func (f *fakeClient) snapshot() (connects, disconnects, live, handlers int, connected bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.connects, f.disconnects, f.disconnectsLive, len(f.handlers), f.connected
}

// ---------------------------------------------------------------------------------------------

type harness struct {
	t    *testing.T
	f    *fakeClient
	pc   *pairingController
	done chan bool
	stop context.CancelFunc
}

func startHarness(t *testing.T, f *fakeClient, qrMode bool, qrOut func(string), tweak func(*pairingController)) *harness {
	t.Helper()
	pc := newPairingController(f, waLog.Noop, qrMode, qrOut, nil)
	pc.qrWait = 300 * time.Millisecond
	pc.reuseWindow = time.Second
	pc.socketCap = 3 * time.Second
	pc.watchEvery = 20 * time.Millisecond
	pc.pairTimeout = 300 * time.Millisecond
	pc.qrReopen = 50 * time.Millisecond
	pc.qrRetry = 100 * time.Millisecond
	pc.submitWait = 500 * time.Millisecond
	pc.replyWait = 2 * time.Second
	if tweak != nil {
		tweak(pc)
	}
	ctx, cancel := context.WithCancel(context.Background())
	h := &harness{t: t, f: f, pc: pc, done: make(chan bool, 1), stop: cancel}
	go func() { h.done <- pc.Run(ctx) }()
	waitFor(t, time.Second, "controller active", func() bool { return pc.active.Load() })
	t.Cleanup(func() {
		cancel()
		select {
		case <-h.done:
		case <-time.After(2 * time.Second):
			t.Errorf("Run did not return after cancel")
		}
	})
	return h
}

func waitFor(t *testing.T, d time.Duration, what string, cond func() bool) {
	t.Helper()
	deadline := time.Now().Add(d)
	for time.Now().Before(deadline) {
		if cond() {
			return
		}
		time.Sleep(5 * time.Millisecond)
	}
	t.Fatalf("timed out waiting for %s", what)
}

// request runs pc.Request with a hard test deadline, so a hang fails the test instead of blocking it.
func (h *harness) request(phone string) (pairResult, error) {
	h.t.Helper()
	type out struct {
		r   pairResult
		err error
	}
	ch := make(chan out, 1)
	go func() {
		r, err := h.pc.Request(phone)
		ch <- out{r, err}
	}()
	select {
	case o := <-ch:
		return o.r, o.err
	case <-time.After(5 * time.Second):
		h.t.Fatalf("Request(%s) blocked", phone)
		return pairResult{}, nil
	}
}

func (h *harness) mustCode(phone string) pairResult {
	h.t.Helper()
	r, err := h.request(phone)
	if err != nil {
		h.t.Fatalf("Request(%s): %v", phone, err)
	}
	return r
}

func (h *harness) status() map[string]any { return h.pc.Status() }

// ---------------------------------------------------------------------------------------------
// (a) many requests: one handler, no stray Disconnect, one goroutine owns the socket.

func TestManyRequestsNoPhantomDisconnects(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)

	phones := []string{"40722000111", "40722000111", "40722000222", "40722000222", "40722000111",
		"40733000333", "+40 733 000 333", "40722000111", "40722000222", "40722000222"}
	newCodes := 0
	for _, p := range phones {
		r := h.mustCode(p)
		if !r.reused {
			newCodes++
		}
		_, _, _, handlers, connected := f.snapshot()
		if handlers != 1 {
			t.Fatalf("after request for %s: %d event handlers registered, want 1", p, handlers)
		}
		if !connected {
			t.Fatalf("after request for %s: socket not connected", p)
		}
	}
	connects, _, live, _, _ := f.snapshot()
	if connects != newCodes {
		t.Fatalf("connects = %d, want one per new code (%d)", connects, newCodes)
	}
	if live != newCodes-1 {
		t.Fatalf("Disconnect on a live socket %d times, want %d (only to replace the socket for a new code)", live, newCodes-1)
	}
	// Nothing in the background touches the current socket afterwards.
	time.Sleep(300 * time.Millisecond)
	_, _, live2, handlers, connected := f.snapshot()
	if live2 != live || !connected || handlers != 1 {
		t.Fatalf("background activity after requests: live disconnects %d->%d, connected=%v, handlers=%d", live, live2, connected, handlers)
	}
	f.mu.Lock()
	owners := len(f.callers)
	f.mu.Unlock()
	if owners != 1 {
		t.Fatalf("Connect/Disconnect/PairPhone called from %d goroutines, want 1 (the controller)", owners)
	}
}

// (b) same number -> same code; other number -> new code; old code -> new code.

func TestSameNumberReusesCode(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)

	a1 := h.mustCode("40722000111")
	if a1.reused || a1.code == "" {
		t.Fatalf("first code: %+v", a1)
	}
	if st := h.status(); st["state"] != pairStateCodeIssued || st["last_event"] != "code issued" {
		t.Fatalf("status after first code: %v", st)
	}
	a2 := h.mustCode("40722000111")
	if !a2.reused || a2.code != a1.code {
		t.Fatalf("same number should reuse %s, got %+v", a1.code, a2)
	}
	b := h.mustCode("40722000222")
	if b.reused || b.code == a1.code {
		t.Fatalf("other number should get a new code, got %+v", b)
	}
	time.Sleep(h.pc.reuseWindow + 100*time.Millisecond)
	b2 := h.mustCode("40722000222")
	if b2.reused || b2.code == b.code {
		t.Fatalf("code older than the reuse window should be replaced, got %+v", b2)
	}
	if connects, _, _, _, _ := f.snapshot(); connects != 3 {
		t.Fatalf("connects = %d, want 3", connects)
	}
}

// (c) socket closed by server -> idle; next request gets a new code on a new socket.

func TestServerCloseGoesIdleThenNewCode(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)

	c1 := h.mustCode("40722000111")
	f.serverClose()
	waitFor(t, time.Second, "idle after server close", func() bool {
		st := h.status()
		return st["state"] == pairStateIdle && strings.HasPrefix(st["last_event"].(string), "login socket closed by server after")
	})
	if st := h.status(); st["code_age_sec"] != nil {
		t.Fatalf("code_age_sec should be null when idle: %v", st)
	}
	c2 := h.mustCode("40722000111")
	if c2.reused || c2.code == c1.code {
		t.Fatalf("after server close: want a new code, got %+v", c2)
	}
	if connects, _, _, _, _ := f.snapshot(); connects != 2 {
		t.Fatalf("connects = %d, want 2", connects)
	}
}

func TestSilentSocketLossGoesIdle(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	h.mustCode("40722000111")
	f.silentDrop()
	waitFor(t, time.Second, "idle after silent loss", func() bool {
		st := h.status()
		return st["state"] == pairStateIdle && strings.Contains(st["last_event"].(string), "without a close event")
	})
	if r := h.mustCode("40722000111"); r.reused {
		t.Fatalf("after silent loss: want a new code, got %+v", r)
	}
}

func TestSocketCapClosesSocket(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, func(pc *pairingController) { pc.socketCap = 200 * time.Millisecond })
	h.mustCode("40722000111")
	waitFor(t, 2*time.Second, "idle after cap", func() bool {
		st := h.status()
		return st["state"] == pairStateIdle && strings.Contains(st["last_event"].(string), "closed by bridge")
	})
	if _, _, _, _, connected := f.snapshot(); connected {
		t.Fatalf("socket still connected after the cap")
	}
}

// Stale Disconnected (from an older socket) must not mark the current socket closed.
func TestStaleDisconnectedIgnored(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	h.mustCode("40722000111")
	f.dispatch(&events.Disconnected{}) // socket still connected in the fake
	time.Sleep(100 * time.Millisecond)
	if st := h.status(); st["state"] != pairStateCodeIssued {
		t.Fatalf("stale Disconnected changed the state: %v", st)
	}
	if r := h.mustCode("40722000111"); !r.reused {
		t.Fatalf("code should still be reusable, got %+v", r)
	}
}

// (d) PairSuccess ends the loop with success; nothing disconnects the new session.

func TestPairSuccessEndsLoop(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	h.mustCode("40722000111")
	_, _, liveBefore, _, _ := f.snapshot()
	f.pairSuccess()
	select {
	case ok := <-h.done:
		if !ok {
			t.Fatalf("Run returned false after PairSuccess")
		}
		h.done <- ok // for Cleanup
	case <-time.After(time.Second):
		t.Fatalf("Run did not return after PairSuccess")
	}
	_, _, liveAfter, handlers, connected := f.snapshot()
	if liveAfter != liveBefore || !connected {
		t.Fatalf("controller disconnected after PairSuccess (live %d->%d, connected=%v)", liveBefore, liveAfter, connected)
	}
	if handlers != 0 {
		t.Fatalf("pairing handler still registered after success: %d", handlers)
	}
	if st := h.status(); st["last_event"] != "pair success" {
		t.Fatalf("last_event = %v", st["last_event"])
	}
	if _, err := h.pc.Request("40722000111"); !errors.Is(err, errPairingNotRunning) {
		t.Fatalf("Request after success: %v", err)
	}
}

func TestConnectedWithSessionCountsAsSuccess(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	h.mustCode("40722000111")
	f.mu.Lock()
	f.session = true
	f.mu.Unlock()
	f.dispatch(&events.Connected{})
	select {
	case ok := <-h.done:
		if !ok {
			t.Fatalf("Run returned false")
		}
		h.done <- ok
	case <-time.After(time.Second):
		t.Fatalf("Run did not return after Connected with a session")
	}
}

func TestPairErrorGoesIdle(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	h.mustCode("40722000111")
	f.silentDrop() // whatsmeow disconnects itself before PairError
	f.dispatch(&events.PairError{Error: errors.New("boom")})
	waitFor(t, time.Second, "idle after PairError", func() bool {
		st := h.status()
		return st["state"] == pairStateIdle && st["last_event"] == "pair error: boom"
	})
}

// (e) no path blocks forever.

func TestNoQRTimesOutAndRecovers(t *testing.T) {
	f := newFakeClient()
	f.autoQR = false
	h := startHarness(t, f, false, nil, nil)
	start := time.Now()
	if _, err := h.request("40722000111"); err == nil || !strings.Contains(err.Error(), "not ready") {
		t.Fatalf("want 'not ready' error, got %v", err)
	}
	if d := time.Since(start); d > time.Second {
		t.Fatalf("not-ready error took %v", d)
	}
	if _, _, _, _, connected := f.snapshot(); connected {
		t.Fatalf("socket left open after a failed request")
	}
	f.mu.Lock()
	f.autoQR = true
	f.mu.Unlock()
	if r := h.mustCode("40722000111"); r.code == "" {
		t.Fatalf("no code after recovery")
	}
}

func TestConnectErrorReturnsQuickly(t *testing.T) {
	f := newFakeClient()
	f.connectErr = errors.New("dial failed")
	h := startHarness(t, f, false, nil, nil)
	if _, err := h.request("40722000111"); err == nil || !strings.Contains(err.Error(), "dial failed") {
		t.Fatalf("want connect error, got %v", err)
	}
	if st := h.status(); st["state"] != pairStateIdle {
		t.Fatalf("state after connect error: %v", st)
	}
}

func TestPairPhoneHangIsBounded(t *testing.T) {
	f := newFakeClient()
	f.pairBlock = true
	h := startHarness(t, f, false, nil, nil)
	start := time.Now()
	if _, err := h.request("40722000111"); err == nil {
		t.Fatalf("want error from a hanging PairPhone")
	}
	if d := time.Since(start); d > time.Second {
		t.Fatalf("hanging PairPhone held the request for %v", d)
	}
	if st := h.status(); st["state"] != pairStateIdle {
		t.Fatalf("state after failed PairPhone: %v", st)
	}
}

func TestRequestWithoutLoopFailsFast(t *testing.T) {
	pc := newPairingController(newFakeClient(), waLog.Noop, false, nil, nil)
	start := time.Now()
	if _, err := pc.Request("40722000111"); !errors.Is(err, errPairingNotRunning) {
		t.Fatalf("got %v", err)
	}
	if time.Since(start) > 100*time.Millisecond {
		t.Fatalf("Request without a loop was slow")
	}
}

func TestCancelStopsRunAndClosesSocket(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	h.mustCode("40722000111")
	h.stop()
	select {
	case ok := <-h.done:
		if ok {
			t.Fatalf("Run returned true on cancel")
		}
		h.done <- ok
	case <-time.After(time.Second):
		t.Fatalf("Run did not stop on cancel")
	}
	if _, _, _, handlers, connected := f.snapshot(); connected || handlers != 0 {
		t.Fatalf("after cancel: connected=%v handlers=%d", connected, handlers)
	}
}

// Daemon mode: no socket and no QR until a request comes.
func TestDaemonModeIdleWithoutSocket(t *testing.T) {
	f := newFakeClient()
	h := startHarness(t, f, false, nil, nil)
	time.Sleep(200 * time.Millisecond)
	connects, _, _, handlers, connected := f.snapshot()
	if connects != 0 || connected {
		t.Fatalf("daemon mode opened a socket on its own (connects=%d)", connects)
	}
	if handlers != 1 {
		t.Fatalf("handlers = %d, want 1", handlers)
	}
	if st := h.status(); st["state"] != pairStateIdle || st["code_age_sec"] != nil {
		t.Fatalf("status: %v", st)
	}
}

// QR mode: socket opened on its own, QR shown through qrOut, reopened after the server closes it.
func TestQRModeShowsAndReopens(t *testing.T) {
	f := newFakeClient()
	var mu sync.Mutex
	var shown []string
	qrOut := func(code string) {
		mu.Lock()
		shown = append(shown, code)
		mu.Unlock()
	}
	count := func() int { mu.Lock(); defer mu.Unlock(); return len(shown) }
	h := startHarness(t, f, true, qrOut, nil)
	waitFor(t, time.Second, "first QR shown", func() bool { return count() == 1 })
	if st := h.status(); st["state"] != pairStateQRShown {
		t.Fatalf("state = %v", st["state"])
	}
	f.serverClose()
	waitFor(t, time.Second, "QR after reopen", func() bool { return count() == 2 })
	mu.Lock()
	defer mu.Unlock()
	if shown[0] != "qr-1-1" || shown[1] != "qr-2-1" {
		t.Fatalf("shown = %v", shown)
	}
	if _, _, _, handlers, _ := f.snapshot(); handlers != 1 {
		t.Fatalf("handlers = %d, want 1", handlers)
	}
}

// ---------------------------------------------------------------------------------------------
// Logger wrapper and pairing notes.

func TestPairingNoteHidesPhoneNumbers(t *testing.T) {
	cases := []struct {
		module, line, wantNote, wantEvent string
	}{
		{"Recv", `<notification from="s.whatsapp.net" id="1" type="link_code_companion_reg"><link_code_companion_reg jid="40722123456@s.whatsapp.net" stage="primary_hello"><x/></link_code_companion_reg></notification>`,
			"code pairing notification received from the phone (stage primary_hello)", "notification received"},
		{"Send", `<iq id="2" type="set" xmlns="md"><link_code_companion_reg jid="40722123456@s.whatsapp.net" stage="companion_hello"/></iq>`,
			"sent code pairing stage companion_hello", ""},
		{"Recv", `<iq from="s.whatsapp.net" type="result"><link_code_companion_reg><link_code_pairing_ref>x</link_code_pairing_ref></link_code_companion_reg></iq>`,
			"server answered the code pairing request", ""},
		{"Recv", `<stream:error code="515"/>`, "stream error code 515", ""},
		{"Recv", `<message from="40722123456@s.whatsapp.net"/>`, "", ""},
		{"Client", `Pairing step for 40722123456 done`, "Pairing step for ***456 done", ""},
		{"Client", `Unrelated debug line`, "", ""},
	}
	for _, c := range cases {
		note, evt := pairingNote(c.module, c.line)
		if note != c.wantNote || evt != c.wantEvent {
			t.Errorf("pairingNote(%s, %q) = (%q, %q), want (%q, %q)", c.module, c.line, note, evt, c.wantNote, c.wantEvent)
		}
		if strings.Contains(note, "40722123") {
			t.Errorf("phone number leaked in %q", note)
		}
	}
}

type recLogger struct {
	mu  *sync.Mutex
	buf *bytes.Buffer
}

func (r recLogger) w(level, msg string, args ...any) {
	r.mu.Lock()
	fmt.Fprintf(r.buf, level+" "+msg+"\n", args...)
	r.mu.Unlock()
}
func (r recLogger) Warnf(m string, a ...any)  { r.w("WARN", m, a...) }
func (r recLogger) Errorf(m string, a ...any) { r.w("ERROR", m, a...) }
func (r recLogger) Infof(m string, a ...any)  { r.w("INFO", m, a...) }
func (r recLogger) Debugf(m string, a ...any) {}
func (r recLogger) Sub(string) waLog.Logger   { return r }
func (r recLogger) String() string            { r.mu.Lock(); defer r.mu.Unlock(); return r.buf.String() }

func TestPairingLoggerOnlyWhileActive(t *testing.T) {
	rec := recLogger{mu: &sync.Mutex{}, buf: &bytes.Buffer{}}
	active := &atomic.Bool{}
	var got []string
	root := newPairingLogger(rec, active)
	root.onEvent = func(e string) { got = append(got, e) }
	recv := root.Sub("Recv")
	line := `<notification type="link_code_companion_reg"><link_code_companion_reg stage="primary_hello"/></notification>`
	recv.Debugf("%s", line)
	if rec.String() != "" {
		t.Fatalf("inactive wrapper logged: %q", rec.String())
	}
	active.Store(true)
	recv.Debugf("%s", line)
	if !strings.Contains(rec.String(), "INFO pairing: code pairing notification received") {
		t.Fatalf("active wrapper did not log the notification: %q", rec.String())
	}
	if len(got) != 1 || got[0] != "notification received" {
		t.Fatalf("onEvent = %v", got)
	}
}

func TestPairingLoggerMasksNumbersWhileActive(t *testing.T) {
	rec := recLogger{mu: &sync.Mutex{}, buf: &bytes.Buffer{}}
	active := &atomic.Bool{}
	l := newPairingLogger(rec, active)
	active.Store(true)
	l.Infof("Successfully paired %s", "40722123456:12@s.whatsapp.net")
	active.Store(false)
	l.Infof("Linked as %s", "40722123456@s.whatsapp.net")
	out := rec.String()
	if !strings.Contains(out, "Successfully paired ***456:12@s.whatsapp.net") {
		t.Fatalf("not masked while active: %q", out)
	}
	if !strings.Contains(out, "Linked as 40722123456@s.whatsapp.net") {
		t.Fatalf("masked while inactive (normal phase must be unchanged): %q", out)
	}
}
