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
    connecting: ['blink', 'connecting…'],
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

function clearCode() { codeEl.value = ''; updateEditor(); }

async function ping() {
  const url = baseUrl() + '/ping';
  log(`Pinging ${url}…`);
  setStatus('connecting');
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (res.ok) { log('Pong — DiMI is reachable.', 'ok'); setStatus('ok'); }
    else         { log(`HTTP ${res.status}`, 'err');         setStatus('err'); }
  } catch (e) { log(e.message, 'err'); setStatus('err'); }
}

async function send() {
  const code = codeEl.value.trim();
  if (!code) { log('Editor is empty.', 'dim'); return; }

  const url = baseUrl() + '/execute';
  log(`Sending to ${url}…`);
  sendBtn.disabled = true;
  sendBtn.textContent = 'Sending…';

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: code,
      signal: AbortSignal.timeout(10000),
    });
    const body = await res.text();
    if (res.ok) { log(`Accepted — ${body}`, 'ok');  setStatus('ok'); }
    else         { log(`Rejected (${res.status}) — ${body}`, 'err'); setStatus('err'); }
  } catch (e) {
    log(e.message, 'err');
    setStatus('err');
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send to DiMI';
  }
}

updateEditor();
log('Ready.', 'dim');