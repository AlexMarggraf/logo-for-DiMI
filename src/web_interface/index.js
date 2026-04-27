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
    sendBtn.textContent = 'Send to DiMI';
  }
}