package main

// Pairing loop for a bridge that is not linked yet.
//
// One goroutine (pairingController.Run) owns the login websocket: it is the only code that calls
// Connect, Disconnect and PairPhone while the bridge is unlinked. whatsmeow events reach it through a
// single event handler, registered once and removed when Run returns, that only appends to a queue.
//
// This replaces the old loop built on client.GetQRChannel. Every GetQRChannel call registers its own
// event handler, and an "expected" Disconnect (ours) does not remove it (whatsmeow qrchan.go: the
// handler goes away only on a final event or when its codes run out). The orphaned handlers then
// started their own QR emitters on every new socket and, when their unread buffer filled or their codes
// ran out, called Disconnect on the CURRENT socket. That is gone here: there is one handler, it never
// calls the client, and nothing but Run touches the socket.

import (
	"context"
	"errors"
	"fmt"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"go.mau.fi/whatsmeow"
	"go.mau.fi/whatsmeow/types/events"
	waLog "go.mau.fi/whatsmeow/util/log"
)

// pairClient is the part of *whatsmeow.Client the pairing loop uses. Small on purpose, so tests can
// drive the loop with a fake.
type pairClient interface {
	Connect() error
	Disconnect()
	IsConnected() bool
	HasSession() bool // device store has an ID, i.e. the device is linked
	PairPhone(ctx context.Context, phone string, showPushNotification bool, clientType whatsmeow.PairClientType, clientDisplayName string) (string, error)
	SendPasskeyConfirmation(ctx context.Context) error
	AddEventHandler(fn func(evt any)) uint32
	RemoveEventHandler(id uint32) bool
}

// waPairClient adapts *whatsmeow.Client to pairClient.
type waPairClient struct{ *whatsmeow.Client }

func (c waPairClient) HasSession() bool { return c.Store.ID != nil }
func (c waPairClient) AddEventHandler(fn func(evt any)) uint32 {
	return c.Client.AddEventHandler(fn)
}

const (
	pairStateIdle       = "idle"        // no login socket
	pairStateConnecting = "connecting"  // socket being opened / open without a code
	pairStateCodeIssued = "code_issued" // a pairing code is out and its socket is alive
	pairStateQRShown    = "qr_shown"    // only with -qr / terminal: socket open, QR codes on stdout

	// The server sends 6 QR refs: 60s + 5 x 20s. whatsmeow documents that the server closes the
	// login socket after that. The code's own expiry on the server is unknown (pair-code.go).
	pairCodeNominalSec = 160
)

type pairResult struct {
	code   string
	reused bool
	ageSec int
}

type pairRequest struct {
	phone string
	resp  chan pairReply
}

type pairReply struct {
	res pairResult
	err error
}

// pairingController runs the unlinked phase. Create with newPairingController, start Run in one
// goroutine, call Request / Status from anywhere.
type pairingController struct {
	cli    pairClient
	log    waLog.Logger
	qrMode bool
	qrOut  func(code string) // prints a QR code; used only in qrMode

	// Timings (production values from newPairingController; tests shorten them).
	qrWait      time.Duration // max wait for the first QR event (= socket ready) after Connect
	reuseWindow time.Duration // a code younger than this, same number, live socket -> returned again
	socketCap   time.Duration // hard cap on one login socket's life
	watchEvery  time.Duration // watchdog tick
	pairTimeout time.Duration // max time for the PairPhone round trip
	qrReopen    time.Duration // qrMode: pause before opening the next socket after one closed
	qrRetry     time.Duration // qrMode: pause after a failed Connect
	submitWait  time.Duration // Request: max wait for the loop to take the request
	replyWait   time.Duration // Request: max wait for the answer
	pairDebug   *atomic.Bool  // turns on the pairing filter in pairingLogger

	requests chan pairRequest
	events   eventQueue
	active   atomic.Bool
	ctx      context.Context

	// Owned by the Run goroutine.
	socketOpen     bool
	socketOpenedAt time.Time
	gotQR          bool
	qrCodes        []string
	qrNextAt       time.Time
	qrFirst        bool
	reopenAt       time.Time
	succeeded      bool

	// Shared with Status (REST goroutines).
	mu          sync.Mutex
	state       string
	phone       string // digits only
	code        string
	codeAt      time.Time
	lastEvent   string
	lastEventAt time.Time
}

func newPairingController(cli pairClient, log waLog.Logger, qrMode bool, qrOut func(string), pairDebug *atomic.Bool) *pairingController {
	pc := &pairingController{
		cli:         cli,
		log:         log,
		qrMode:      qrMode,
		qrOut:       qrOut,
		qrWait:      20 * time.Second,
		reuseWindow: 120 * time.Second,
		socketCap:   10 * time.Minute,
		watchEvery:  2 * time.Second,
		pairTimeout: 25 * time.Second,
		qrReopen:    2 * time.Second,
		qrRetry:     15 * time.Second,
		submitWait:  20 * time.Second,
		replyWait:   55 * time.Second,
		pairDebug:   pairDebug,
		requests:    make(chan pairRequest),
		state:       pairStateIdle,
	}
	if pc.pairDebug == nil {
		pc.pairDebug = &atomic.Bool{}
	}
	pc.events.notify = make(chan struct{}, 1)
	pc.lastEvent = "bridge started (not linked)"
	pc.lastEventAt = time.Now()
	return pc
}

// ---------------------------------------------------------------------------------------------
// Event queue: the whatsmeow handler only appends here. Never blocks, never calls the client.

type eventQueue struct {
	mu     sync.Mutex
	items  []any
	notify chan struct{}
}

func (q *eventQueue) push(evt any) {
	switch evt.(type) {
	case *events.QR, *events.RotateADVSecret, *events.PairSuccess, *events.PairError,
		*events.Disconnected, *events.Connected, *events.ClientOutdated, *events.TemporaryBan,
		*events.ConnectFailure, *events.LoggedOut, *events.QRScannedWithoutMultidevice,
		*events.PairPasskeyRequest, *events.PairPasskeyConfirmation, *events.PairPasskeyError:
	default:
		return
	}
	q.mu.Lock()
	q.items = append(q.items, evt)
	q.mu.Unlock()
	select {
	case q.notify <- struct{}{}:
	default:
	}
}

func (q *eventQueue) drain() []any {
	q.mu.Lock()
	items := q.items
	q.items = nil
	q.mu.Unlock()
	return items
}

// ---------------------------------------------------------------------------------------------
// Public side (REST goroutines).

var errPairingNotRunning = errors.New("bridge is restarting after a logout; try again in about a minute")

// Request asks the loop for a pairing code. Bounded: never waits longer than submitWait + replyWait.
func (pc *pairingController) Request(phone string) (pairResult, error) {
	if !pc.active.Load() {
		return pairResult{}, errPairingNotRunning
	}
	req := pairRequest{phone: phone, resp: make(chan pairReply, 1)}
	select {
	case pc.requests <- req:
	case <-time.After(pc.submitWait):
		return pairResult{}, errors.New("pairing loop busy, try again")
	}
	select {
	case r := <-req.resp:
		return r.res, r.err
	case <-time.After(pc.replyWait):
		return pairResult{}, errors.New("pairing loop did not answer in time; run status, then try once more")
	}
}

// Status is the "pairing" object of /api/status.
func (pc *pairingController) Status() map[string]any {
	pc.mu.Lock()
	defer pc.mu.Unlock()
	now := time.Now()
	var codeAge any
	if pc.state == pairStateCodeIssued && !pc.codeAt.IsZero() {
		codeAge = int(now.Sub(pc.codeAt).Seconds())
	}
	return map[string]any{
		"state":              pc.state,
		"code_age_sec":       codeAge,
		"last_event":         pc.lastEvent,
		"last_event_age_sec": int(now.Sub(pc.lastEventAt).Seconds()),
	}
}

// noteEvent records a short status line (no personal data) for /api/status.
func (pc *pairingController) noteEvent(text string) {
	pc.mu.Lock()
	pc.lastEvent = text
	pc.lastEventAt = time.Now()
	pc.mu.Unlock()
}

func (pc *pairingController) setState(state string) {
	pc.mu.Lock()
	pc.state = state
	if state != pairStateCodeIssued {
		pc.code, pc.phone, pc.codeAt = "", "", time.Time{}
	}
	pc.mu.Unlock()
}

// ---------------------------------------------------------------------------------------------
// The loop.

// Run owns the login websocket until the device is linked (true) or ctx ends (false).
func (pc *pairingController) Run(ctx context.Context) bool {
	pc.ctx = ctx
	handlerID := pc.cli.AddEventHandler(pc.events.push)
	// Called from this goroutine, never from inside an event handler (whatsmeow client.go
	// RemoveEventHandler: doing it inside a handler deadlocks on eventHandlersLock).
	defer pc.cli.RemoveEventHandler(handlerID)
	pc.pairDebug.Store(true)
	defer pc.pairDebug.Store(false)
	pc.active.Store(true)
	defer pc.active.Store(false)

	if pc.qrMode {
		pc.log.Infof("Not linked. QR mode: QR codes are printed on stdout; a pairing code can also be requested via POST /api/pair")
	} else {
		pc.log.Infof("Not linked. Waiting for POST /api/pair (no login socket and no QR until then; start with -qr to print QR codes)")
	}

	tick := time.NewTicker(pc.watchEvery)
	defer tick.Stop()
	for {
		if pc.succeeded {
			return true
		}
		if pc.qrMode && !pc.socketOpen && !time.Now().Before(pc.reopenAt) {
			pc.openForQR()
			continue
		}
		select {
		case <-ctx.Done():
			pc.closeSocket("bridge shutting down")
			pc.log.Infof("pairing: loop stopped (shutdown), device not linked")
			return false
		case <-pc.events.notify:
			pc.processEvents()
		case req := <-pc.requests:
			res, err := pc.handleRequest(req.phone)
			req.resp <- pairReply{res: res, err: err}
		case <-tick.C:
			pc.watch()
		}
	}
}

func (pc *pairingController) processEvents() {
	for _, evt := range pc.events.drain() {
		pc.handleEvent(evt)
	}
}

func (pc *pairingController) socketAge() int {
	if pc.socketOpenedAt.IsZero() {
		return 0
	}
	return int(time.Since(pc.socketOpenedAt).Seconds())
}

// openSocket connects a fresh login socket. Caller makes sure no socket is open.
func (pc *pairingController) openSocket() error {
	pc.setState(pairStateConnecting)
	pc.gotQR = false
	pc.qrCodes = nil
	if err := pc.cli.Connect(); err != nil {
		pc.setState(pairStateIdle)
		pc.noteEvent("connect failed: " + errText(err))
		pc.log.Errorf("pairing: cannot open login socket: %v", err)
		return err
	}
	pc.socketOpen = true
	pc.socketOpenedAt = time.Now()
	return nil
}

// closeSocket is the only place that disconnects the login socket on purpose.
func (pc *pairingController) closeSocket(reason string) {
	wasOpen := pc.socketOpen
	if wasOpen || pc.cli.IsConnected() {
		pc.cli.Disconnect()
	}
	if wasOpen {
		msg := fmt.Sprintf("login socket closed by bridge (%s) after %ds", reason, pc.socketAge())
		pc.log.Infof("pairing: %s", msg)
		pc.noteEvent(msg)
	}
	pc.markClosed()
}

func (pc *pairingController) markClosed() {
	pc.socketOpen = false
	pc.gotQR = false
	pc.qrCodes = nil
	pc.setState(pairStateIdle)
	if pc.qrMode {
		pc.reopenAt = time.Now().Add(pc.qrReopen)
	}
}

func (pc *pairingController) openForQR() {
	if err := pc.openSocket(); err != nil {
		pc.reopenAt = time.Now().Add(pc.qrRetry)
	}
}

func digitsOnly(s string) string {
	var b strings.Builder
	for _, r := range s {
		if r >= '0' && r <= '9' {
			b.WriteRune(r)
		}
	}
	return b.String()
}

func (pc *pairingController) handleRequest(rawPhone string) (pairResult, error) {
	phone := digitsOnly(rawPhone)
	// Look at whatever happened since the last loop turn before deciding (a close event may be queued).
	pc.processEvents()
	if pc.succeeded {
		return pairResult{}, errors.New("already linked; nothing to pair")
	}

	pc.mu.Lock()
	state, curPhone, curCode, codeAt := pc.state, pc.phone, pc.code, pc.codeAt
	pc.mu.Unlock()
	if state == pairStateCodeIssued && pc.socketOpen && pc.cli.IsConnected() && phone != "" && phone == curPhone {
		age := time.Since(codeAt)
		if age < pc.reuseWindow {
			pc.log.Infof("pairing: code reused for a phone ending in %s (code age %ds, socket open %ds)", lastDigits(phone, 3), int(age.Seconds()), pc.socketAge())
			pc.noteEvent("code reused")
			return pairResult{code: curCode, reused: true, ageSec: int(age.Seconds())}, nil
		}
	}

	// A new code needs the whole window: fresh socket. This kills the previous code, if any.
	if pc.socketOpen || pc.cli.IsConnected() {
		pc.closeSocket("new code requested")
	}
	if err := pc.openSocket(); err != nil {
		return pairResult{}, fmt.Errorf("cannot open login websocket: %v", err)
	}
	if err := pc.waitSocketReady(); err != nil {
		if pc.succeeded {
			return pairResult{}, errors.New("already linked; nothing to pair")
		}
		pc.closeSocket("socket not ready")
		return pairResult{}, err
	}

	ctx, cancel := context.WithTimeout(pc.ctx, pc.pairTimeout)
	code, err := pc.cli.PairPhone(ctx, phone, true, whatsmeow.PairClientChrome, "Chrome (macOS)")
	cancel()
	if err != nil {
		pc.log.Errorf("pairing: code request failed for a phone ending in %s: %v", lastDigits(phone, 3), err)
		pc.noteEvent("pair code request failed: " + errText(err))
		pc.processEvents() // never close a socket that has just been linked
		if !pc.qrMode && !pc.succeeded && pc.socketOpen {
			pc.closeSocket("code request failed")
		}
		return pairResult{}, fmt.Errorf("pairing code request failed: %v", err)
	}
	now := time.Now()
	pc.mu.Lock()
	pc.state, pc.phone, pc.code, pc.codeAt = pairStateCodeIssued, phone, code, now
	pc.mu.Unlock()
	pc.log.Infof("pairing: code issued for a phone ending in %s (socket open %ds)", lastDigits(phone, 3), pc.socketAge())
	pc.noteEvent("code issued")
	return pairResult{code: code}, nil
}

// waitSocketReady waits for the first QR event on the socket just opened: whatsmeow's PairPhone doc
// says to wait for it before asking for a code (pair-code.go). Bounded by qrWait.
func (pc *pairingController) waitSocketReady() error {
	timer := time.NewTimer(pc.qrWait)
	defer timer.Stop()
	for !pc.gotQR {
		if pc.succeeded {
			return errors.New("already linked")
		}
		if !pc.socketOpen {
			return errors.New("login websocket closed before it was ready")
		}
		select {
		case <-pc.events.notify:
			pc.processEvents()
		case <-timer.C:
			return fmt.Errorf("login websocket not ready after %ds", int(pc.qrWait.Seconds()))
		case <-pc.ctx.Done():
			return errors.New("bridge shutting down")
		}
	}
	return nil
}

// watch catches what no event reports: a socket that died silently (whatsmeow's keepalive drops it
// with an "expected" Disconnect, which emits no event: keepalive.go + client.go onDisconnect), the
// 10-minute cap, and QR rotation in qrMode.
func (pc *pairingController) watch() {
	if !pc.socketOpen {
		return
	}
	if !pc.cli.IsConnected() && (pc.gotQR || time.Since(pc.socketOpenedAt) > pc.qrWait) {
		msg := fmt.Sprintf("login socket lost without a close event after %ds", pc.socketAge())
		pc.log.Warnf("pairing: %s", msg)
		pc.noteEvent(msg)
		pc.markClosed()
		return
	}
	if time.Since(pc.socketOpenedAt) >= pc.socketCap {
		pc.closeSocket(fmt.Sprintf("cap of %v", pc.socketCap))
		return
	}
	if pc.qrMode && len(pc.qrCodes) > 0 && !time.Now().Before(pc.qrNextAt) {
		pc.showNextQR()
	}
}

func (pc *pairingController) showNextQR() {
	if len(pc.qrCodes) == 0 || pc.qrOut == nil {
		return
	}
	timeout := 20 * time.Second
	if pc.qrFirst {
		timeout = 60 * time.Second
		pc.qrFirst = false
	}
	code := pc.qrCodes[0]
	pc.qrCodes = pc.qrCodes[1:]
	pc.qrNextAt = time.Now().Add(timeout)
	pc.qrOut(code)
}

func (pc *pairingController) handleEvent(raw any) {
	switch evt := raw.(type) {
	case *events.QR:
		if !pc.socketOpen {
			pc.log.Debugf("pairing: ignoring QR event with no login socket of ours")
			return
		}
		if !pc.gotQR {
			pc.gotQR = true
			pc.log.Infof("pairing: login socket ready (first QR from server, %d refs) after %ds", len(evt.Codes), pc.socketAge())
			if pc.qrMode {
				pc.setState(pairStateQRShown)
			}
		} else {
			pc.log.Infof("pairing: server sent %d new QR refs on the same socket", len(evt.Codes))
		}
		if pc.qrMode {
			pc.qrCodes = append([]string(nil), evt.Codes...)
			pc.qrFirst = true
			pc.showNextQR()
		}

	case *events.RotateADVSecret:
		for i, c := range pc.qrCodes {
			pc.qrCodes[i] = strings.Replace(c, evt.OldSecret, evt.NewSecret, 1)
		}

	case *events.PairSuccess:
		pc.log.Infof("pairing: PairSuccess, device linked (socket open %ds)", pc.socketAge())
		pc.noteEvent("pair success")
		pc.succeeded = true

	case *events.Connected:
		if pc.cli.HasSession() {
			// Linked and logged in on the post-pairing socket; PairSuccess may still be in flight.
			pc.log.Infof("pairing: connected with the new session")
			pc.noteEvent("pair success")
			pc.succeeded = true
		} else {
			pc.log.Warnf("pairing: Connected event without a linked device (unexpected)")
		}

	case *events.PairError:
		// whatsmeow has already disconnected (pair.go handlePairSuccess).
		pc.log.Errorf("pairing: PairError: %v", evt.Error)
		pc.noteEvent("pair error: " + errText(evt.Error))
		pc.markClosed()

	case *events.Disconnected:
		if !pc.socketOpen {
			return
		}
		if pc.cli.IsConnected() {
			// Late event from an older socket; the current one is alive.
			pc.log.Debugf("pairing: ignoring Disconnected for an older socket")
			return
		}
		msg := fmt.Sprintf("login socket closed by server after %ds", pc.socketAge())
		pc.log.Infof("pairing: %s", msg)
		pc.noteEvent(msg)
		pc.markClosed()

	case *events.ClientOutdated:
		pc.log.Errorf("pairing: server says this client version is outdated (update whatsmeow)")
		pc.noteEvent("client outdated")
		pc.closeSocket("client outdated")

	case *events.TemporaryBan:
		pc.log.Errorf("pairing: temporary ban from WhatsApp: %s", evt.String())
		pc.noteEvent("temporary ban: " + evt.String())
		pc.closeSocket("temporary ban")

	case *events.ConnectFailure:
		pc.log.Errorf("pairing: connect failure: reason %d (%s) %s", int(evt.Reason), evt.Reason.String(), evt.Message)
		pc.noteEvent(fmt.Sprintf("connect failure: %s", evt.Reason.String()))
		pc.closeSocket("connect failure")

	case *events.LoggedOut:
		pc.log.Warnf("pairing: logged out event while unlinked (%s)", evt.Reason.String())
		pc.noteEvent("logged out")
		pc.closeSocket("logged out")

	case *events.QRScannedWithoutMultidevice:
		pc.log.Warnf("pairing: QR scanned by a phone without multi-device")
		pc.noteEvent("qr scanned without multidevice")

	case *events.PairPasskeyRequest:
		pc.log.Warnf("pairing: passkey required, unsupported by this bridge (the phone asked for passkey pairing)")
		pc.noteEvent("passkey required (unsupported)")

	case *events.PairPasskeyConfirmation:
		if evt.SkipHandoffUX {
			// Same as whatsmeow's qrchan.go: confirm automatically when no user check is needed.
			if err := pc.cli.SendPasskeyConfirmation(pc.ctx); err != nil {
				pc.log.Errorf("pairing: automatic passkey confirmation failed: %v", err)
				pc.noteEvent("passkey confirmation failed")
			} else {
				pc.log.Infof("pairing: passkey confirmation sent automatically")
			}
		} else {
			pc.log.Warnf("pairing: passkey confirmation needs the user to compare a code; unsupported by this bridge")
			pc.noteEvent("passkey confirmation required (unsupported)")
		}

	case *events.PairPasskeyError:
		pc.log.Errorf("pairing: passkey error: %v", evt.Error)
		pc.noteEvent("passkey error: " + errText(evt.Error))
	}
}

func errText(err error) string {
	if err == nil {
		return "unknown"
	}
	s := redactNumbers(err.Error())
	if len(s) > 200 {
		s = s[:200]
	}
	return s
}

// ---------------------------------------------------------------------------------------------
// Logger wrapper: while unlinked, lets through (at INFO) the whatsmeow Debug lines that show pairing
// progress, without personal data. Sent/received XML is never copied as is (it carries the phone JID);
// only a fixed summary of the pairing stanzas is logged.

var (
	longDigits  = regexp.MustCompile(`\d{7,}`)
	stageAttr   = regexp.MustCompile(`stage="([a-z_]+)"`)
	codeAttr    = regexp.MustCompile(`code="([0-9]+)"`)
	reasonAttr  = regexp.MustCompile(`reason="([0-9]+)"`)
	typeAttr    = regexp.MustCompile(`type="([a-z_]+)"`)
	pairingWord = regexp.MustCompile(`(?i)pair|link_code|companion`)
)

func redactNumbers(s string) string {
	return longDigits.ReplaceAllStringFunc(s, func(m string) string { return "***" + m[len(m)-3:] })
}

func firstMatch(re *regexp.Regexp, s string) string {
	if m := re.FindStringSubmatch(s); len(m) > 1 {
		return m[1]
	}
	return "?"
}

// pairingNote turns one whatsmeow Debug line into a short pairing log line, or "" to skip it.
// event is the /api/status last_event to record, or "".
func pairingNote(module, line string) (note, event string) {
	trimmed := strings.TrimSpace(line)
	isXML := strings.HasPrefix(trimmed, "<")
	recv := strings.HasSuffix(module, "Recv")
	send := strings.HasSuffix(module, "Send")
	if isXML || recv || send {
		if !isXML {
			return "", ""
		}
		switch {
		case recv && strings.HasPrefix(trimmed, "<notification") && strings.Contains(trimmed, "link_code_companion_reg"):
			return fmt.Sprintf("code pairing notification received from the phone (stage %s)", firstMatch(stageAttr, trimmed)), "notification received"
		case recv && strings.HasPrefix(trimmed, "<notification") && strings.Contains(trimmed, "passkey"):
			return fmt.Sprintf("passkey notification received (type %s)", firstMatch(typeAttr, trimmed)), "passkey notification received"
		case recv && strings.HasPrefix(trimmed, "<iq") && strings.Contains(trimmed, "link_code_companion_reg"):
			return "server answered the code pairing request", ""
		case recv && strings.Contains(trimmed, "<pair-success"):
			return "pair-success received from server", ""
		case recv && strings.HasPrefix(trimmed, "<iq") && strings.Contains(trimmed, "<pair-device"):
			return "server sent pair-device (login refs)", ""
		case recv && strings.HasPrefix(trimmed, "<stream:error"):
			return fmt.Sprintf("stream error code %s", firstMatch(codeAttr, trimmed)), ""
		case recv && strings.HasPrefix(trimmed, "<failure"):
			return fmt.Sprintf("connect failure stanza, reason %s", firstMatch(reasonAttr, trimmed)), ""
		case send && strings.Contains(trimmed, "link_code_companion_reg"):
			return fmt.Sprintf("sent code pairing stage %s", firstMatch(stageAttr, trimmed)), ""
		}
		return "", ""
	}
	if pairingWord.MatchString(trimmed) {
		return redactNumbers(trimmed), ""
	}
	return "", ""
}

type pairingLogger struct {
	inner   waLog.Logger
	module  string
	active  *atomic.Bool
	onEvent func(string) // optional: records last_event
}

func newPairingLogger(inner waLog.Logger, active *atomic.Bool) *pairingLogger {
	return &pairingLogger{inner: inner, active: active}
}

// While unlinked, whatsmeow's own lines are passed with long digit runs masked (e.g. its
// "Successfully paired <phone>:<device>@s.whatsapp.net"). Linked: untouched.
func (l *pairingLogger) masked(msg string, args []any) (string, []any) {
	if l.active != nil && l.active.Load() {
		return "%s", []any{redactNumbers(fmt.Sprintf(msg, args...))}
	}
	return msg, args
}

func (l *pairingLogger) Warnf(msg string, args ...any) {
	m, a := l.masked(msg, args)
	l.inner.Warnf(m, a...)
}
func (l *pairingLogger) Errorf(msg string, args ...any) {
	m, a := l.masked(msg, args)
	l.inner.Errorf(m, a...)
}
func (l *pairingLogger) Infof(msg string, args ...any) {
	m, a := l.masked(msg, args)
	l.inner.Infof(m, a...)
}
func (l *pairingLogger) Debugf(msg string, args ...any) {
	if l.active != nil && l.active.Load() {
		if note, evt := pairingNote(l.module, fmt.Sprintf(msg, args...)); note != "" {
			l.inner.Infof("pairing: %s", note)
			if evt != "" && l.onEvent != nil {
				l.onEvent(evt)
			}
		}
	}
	l.inner.Debugf(msg, args...)
}
func (l *pairingLogger) Sub(module string) waLog.Logger {
	return &pairingLogger{inner: l.inner.Sub(module), module: module, active: l.active, onEvent: l.onEvent}
}
