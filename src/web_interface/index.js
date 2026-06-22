const codeEl   = document.getElementById('code');
const lnumsEl  = document.getElementById('lnums');
const metaEl   = document.getElementById('meta');
const logEl    = document.getElementById('log');
const dotEl    = document.getElementById('dot');
const statusEl = document.getElementById('status-text');
const sendBtn  = document.getElementById('send-btn');

function updateEditor() {
  const lines = codeEl.value.split('\n');
  lnumsEl.textContent = lines.map((_, i) => i + 1).join('\n');
  metaEl.textContent = `${lines.length} line${lines.length !== 1 ? 's' : ''}`;
}
document.getElementById('stop-btn').disabled = true;

codeEl.addEventListener('input', updateEditor);
codeEl.addEventListener('scroll', () => { lnumsEl.scrollTop = codeEl.scrollTop; });
codeEl.addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const s = codeEl.selectionStart;
    codeEl.value = codeEl.value.slice(0, s) + '  ' + codeEl.value.slice(codeEl.selectionEnd);
    codeEl.selectionStart = codeEl.selectionEnd = s + 2;
    updateEditor();
  }
});

function log(msg, type = '') {
  const t = new Date().toTimeString().slice(0, 8);
  const row = document.createElement('div');
  row.className = 'log-line';
  row.innerHTML = `<span class="log-time">${t}</span><span class="log-msg ${type}">${msg}</span>`;
  logEl.appendChild(row);
  logEl.scrollTop = logEl.scrollHeight;
}

function clearLog() { logEl.innerHTML = ''; }

function setStatus(state) {
  dotEl.className = 'dot';
  const map = {
    ok:         ['ok',    'connected'],
    err:        ['err',   'unreachable'],
    connecting: ['blink', 'connecting...'],
  };
  const [cls, txt] = map[state] || ['', 'disconnected'];
  if (cls) dotEl.classList.add(cls);
  statusEl.textContent = txt;
}

function baseUrl() {
  const ip   = document.getElementById('ip').value.trim();
  const port = document.getElementById('port').value.trim();
  return `http://${ip}:${port}`;
}

function baseAddress() {
  const ip   = document.getElementById('ip').value.trim();
  const port = document.getElementById('port').value.trim();
  return `${ip}:${port}`;
}

function clearCode() { codeEl.value = ''; updateEditor(); }

async function ping() {
  const url = baseUrl() + '/ping';
  log(`Pinging ${baseAddress()}...`);
  setStatus('connecting');
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (res.ok) { log('DiMI is reachable.', 'ok'); setStatus('ok'); }
    else         { log(`HTTP ${res.status}`, 'err');         setStatus('err'); }
  } catch (e) { log(e.message, 'err'); setStatus('err'); }
}

async function send() {
  const code = codeEl.value.trim();
  if (!code) { log('Editor is empty.', 'dim'); return; }

  const url = baseUrl() + '/execute';
  log(`Running on ${baseAddress()}...`);
  sendBtn.disabled = true;
  sendBtn.textContent = 'Running...';
  document.getElementById('stop-btn').disabled = false;

  currentAbort = new AbortController();

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: code,
      signal: currentAbort.signal,
    });

    const body = await res.text();

    if (res.ok) {
      setStatus('ok');
      body.split('\n').forEach(line => { if (line) log(line, 'ok'); });
    } else {
      body.split('\n').forEach(line => { if (line) log(line, 'err'); });
      setStatus('err');
    }
  } catch (e) {
    if (e.name !== 'AbortError') { log(e.message, 'err'); setStatus('err'); }
  } finally {
    currentAbort = null;
    sendBtn.disabled = false;
    sendBtn.textContent = 'Run on DiMI';
    document.getElementById('stop-btn').disabled = true;
  }
}

updateEditor();
log('Ready.', 'dim');

const divider  = document.getElementById('divider');
const rightCol = document.getElementById('right-col');

let dragging = false;

divider.addEventListener('mousedown', e => {
  dragging = true;
  divider.classList.add('dragging');
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';   // prevent text selection while dragging
  e.preventDefault();
});

document.addEventListener('mousemove', e => {
  if (!dragging) return;
  const main = document.querySelector('main');
  const mainRect = main.getBoundingClientRect();
  // right-col width = distance from cursor to right edge of main
  const newWidth = mainRect.right - e.clientX;
  rightCol.style.width = Math.min(10000, Math.max(200, newWidth)) + 'px';
});

document.addEventListener('mouseup', () => {
  if (!dragging) return;
  dragging = false;
  divider.classList.remove('dragging');
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
});

let currentAbort = null;

async function sendLine() {
  const input = document.getElementById('cli-input');
  const code = input.value.trim();
  if (!code) { log('Empty command.', 'dim'); return; }

  const url = baseUrl() + '/execute';
  log(`> ${code}`, 'dim');
  input.disabled = true;
  document.getElementById('stop-btn').disabled = false;

  currentAbort = new AbortController();

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: code,
      signal: currentAbort.signal,
    });
    const body = await res.text();
    const type = res.ok ? 'ok' : 'err';
    if (res.ok) setStatus('ok'); else setStatus('err');
    body.split('\n').forEach(line => { if (line) log(line, type); });
  } catch (e) {
    if (e.name !== 'AbortError') { log(e.message, 'err'); setStatus('err'); }
  } finally {
    currentAbort = null;
    input.disabled = false;
    input.value = '';
    input.focus();
    document.getElementById('stop-btn').disabled = true;
  }
}

async function stop() {
  // Abort whichever fetch is in flight
  if (currentAbort) { currentAbort.abort(); }

  const url = baseUrl() + '/stop';
  log('Stopping DiMI...', 'err');
  document.getElementById('stop-btn').disabled = true;
  try {
    await fetch(url, { method: 'POST', signal: AbortSignal.timeout(3000) });
    log('Stopped.', 'err');
    setStatus('err');
  } catch (e) {
    log(e.message, 'err');
    setStatus('err');
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = 'Run on DiMI';
  }
}

document.getElementById('cli-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') sendLine();
});