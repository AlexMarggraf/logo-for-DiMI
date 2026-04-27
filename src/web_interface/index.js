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

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: code,
      signal: AbortSignal.timeout(10000),
    });

    const body = await res.text();

    if (res.ok) {
      setStatus('ok');
      // Print each output line as its own log entry
      body.split('\n').forEach(line => {
        if (line !== '') log(line, 'ok');
      });
    } else {
      body.split('\n').forEach(line => {
        if (line !== '') log(line, 'err');
      });
      setStatus('err');
    }
  } catch (e) {
    log(e.message, 'err');
    setStatus('err');
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = 'Run on DiMI';
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