/* ============================================================
   blocks.js — DiMI Logo Blocks Editor
   ============================================================ */

'use strict';

// ── 1. BLOCK-DEFINITIONEN ─────────────────────────────────────

Blockly.defineBlocksWithJsonArray([
  {
    type: 'logo_forward',
    message0: '⬆ vorwärts %1 Schritte',
    args0: [{ type: 'input_value', name: 'STEPS', check: 'Number' }],
    previousStatement: null, nextStatement: null,
    colour: '#4f86f7', tooltip: 'Roboter vorwärts bewegen',
  },
  {
    type: 'logo_back',
    message0: '⬇ zurück %1 Schritte',
    args0: [{ type: 'input_value', name: 'STEPS', check: 'Number' }],
    previousStatement: null, nextStatement: null,
    colour: '#4f86f7', tooltip: 'Roboter rückwärts bewegen',
  },
  {
    type: 'logo_right',
    message0: '↩ rechts %1 °',
    args0: [{ type: 'input_value', name: 'ANGLE', check: 'Number' }],
    previousStatement: null, nextStatement: null,
    colour: '#f4a942', tooltip: 'Nach rechts drehen',
  },
  {
    type: 'logo_left',
    message0: '↪ links %1 °',
    args0: [{ type: 'input_value', name: 'ANGLE', check: 'Number' }],
    previousStatement: null, nextStatement: null,
    colour: '#f4a942', tooltip: 'Nach links drehen',
  },
  {
    type: 'logo_repeat',
    message0: '🔁 wiederhole %1 mal',
    args0: [{ type: 'input_value', name: 'TIMES', check: 'Number' }],
    message1: '%1',
    args1: [{ type: 'input_statement', name: 'DO' }],
    previousStatement: null, nextStatement: null,
    colour: '#9b59b6', tooltip: 'Blöcke mehrfach ausführen',
  },
  {
    type: 'logo_penup',
    message0: '🖊 Stift hoch',
    previousStatement: null, nextStatement: null,
    colour: '#27ae60', tooltip: 'Stift anheben',
  },
  {
    type: 'logo_pendown',
    message0: '✏️ Stift runter',
    previousStatement: null, nextStatement: null,
    colour: '#27ae60', tooltip: 'Stift absenken',
  },
  {
    type: 'logo_procedure',
    message0: '📦 definiere %1',
    args0: [{ type: 'field_input', name: 'NAME', text: 'meineProzedur' }],
    message1: '%1',
    args1: [{ type: 'input_statement', name: 'BODY' }],
    colour: '#e74c3c', tooltip: 'Wiederverwendbare Prozedur definieren',
  },
  {
    type: 'logo_call_procedure',
    message0: '▶ aufrufen %1',
    args0: [{ type: 'field_input', name: 'NAME', text: 'meineProzedur' }],
    previousStatement: null, nextStatement: null,
    colour: '#e74c3c', tooltip: 'Prozedur aufrufen',
  },
]);


// ── 2. LOGO CODE GENERATOR ────────────────────────────────────

const Logo = new Blockly.Generator('Logo');
Logo.ORDER_ATOMIC = 0;
Logo.ORDER_NONE   = 99;

Logo.scrub_ = function (block, code, opt_thisOnly) {
  const next = block.nextConnection && block.nextConnection.targetBlock();
  return code + (opt_thisOnly ? '' : Logo.blockToCode(next));
};

function val(block, name, fallback) {
  return Logo.valueToCode(block, name, Logo.ORDER_NONE) || String(fallback);
}

Logo['logo_forward']  = b => `FORWARD ${val(b, 'STEPS', 50)}\n`;
Logo['logo_back']     = b => `BACK ${val(b, 'STEPS', 50)}\n`;
Logo['logo_right']    = b => `RIGHT ${val(b, 'ANGLE', 90)}\n`;
Logo['logo_left']     = b => `LEFT ${val(b, 'ANGLE', 90)}\n`;
Logo['logo_penup']    = () => 'PENUP\n';
Logo['logo_pendown']  = () => 'PENDOWN\n';

Logo['logo_repeat'] = function (b) {
  const n    = val(b, 'TIMES', 4);
  const body = Logo.statementToCode(b, 'DO') || '';
  const ind  = body.split('\n').map(l => l ? '  ' + l : '').join('\n');
  return `REPEAT ${n} [\n${ind}\n]\n`;
};

Logo['logo_procedure'] = function (b) {
  const name = b.getFieldValue('NAME').trim() || 'prozedur';
  const body = Logo.statementToCode(b, 'BODY') || '';
  const ind  = body.split('\n').map(l => l ? '  ' + l : '').join('\n');
  return `TO ${name}\n${ind}\nEND\n\n`;
};

Logo['logo_call_procedure'] = function (b) {
  return `${b.getFieldValue('NAME').trim() || 'prozedur'}\n`;
};

Logo['math_number'] = function (b) {
  return [String(b.getFieldValue('NUM')), Logo.ORDER_ATOMIC];
};


// ── 3. WORKSPACE ──────────────────────────────────────────────

const workspace = Blockly.inject('blocklyDiv', {
  toolbox: document.getElementById('toolbox'),
  grid: { spacing: 24, length: 4, colour: '#e0e0dc', snap: true },
  trashcan: true,
  zoom: { controls: true, wheel: true, startScale: 1.0, maxScale: 3, minScale: 0.3 },
  move: { scrollbars: true, drag: true, wheel: false },
  renderer: 'zelos',
  theme: Blockly.Theme.defineTheme('dimi', {
    name: 'dimi',
    base: Blockly.Themes.Classic,
    componentStyles: {
      workspaceBackgroundColour: '#f5f5f3',
      toolboxBackgroundColour:   '#ffffff',
      toolboxForegroundColour:   '#1a1a1a',
      flyoutBackgroundColour:    '#f5f5f3',
      flyoutForegroundColour:    '#1a1a1a',
      flyoutOpacity: 1,
      scrollbarColour: '#d8d8d4',
    },
  }),
});

// Intern den generierten Logo-Code vorhalten (für Send)
let currentLogoCode = '';

workspace.addChangeListener(() => {
  try {
    currentLogoCode = Logo.workspaceToCode(workspace) || '';
  } catch (e) {
    currentLogoCode = '';
  }
});


// ── 4. LOG ────────────────────────────────────────────────────

function log(msg, type = 'dim') {
  const body = document.getElementById('logBody');
  const line = document.createElement('div');
  line.className = 'log-line';

  const ts = new Date().toLocaleTimeString('de-CH', { hour12: false });
  line.innerHTML = `<span class="log-time">${ts}</span><span class="log-msg ${type}">${msg}</span>`;

  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}


// ── 5. STATUS DOT ─────────────────────────────────────────────

function setStatus(state, label) {
  const dot  = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  dot.className = 'dot ' + state;   // '', 'ok', 'err', 'blink'
  text.textContent = label;
}


// ── 6. ROBOT KOMMUNIKATION ────────────────────────────────────

function getRobotBase() {
  const ip   = document.getElementById('robotIp').value.trim()   || '192.168.1.1';
  const port = document.getElementById('robotPort').value.trim() || '8080';
  return `http://${ip}:${port}`;
}

async function ping() {
  setStatus('blink', 'Ping …');
  try {
    const r = await fetch(`${getRobotBase()}/ping`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) {
      setStatus('ok', 'Verbunden');
      log('Roboter erreichbar.', 'ok');
    } else {
      throw new Error(`HTTP ${r.status}`);
    }
  } catch (e) {
    setStatus('err', 'Nicht erreichbar');
    log(`Ping fehlgeschlagen: ${e.message}`, 'err');
  }
}

async function sendCode() {
  const code = currentLogoCode.trim();
  if (!code) {
    log('Keine Blöcke vorhanden — bitte erst Blöcke hinzufügen.', 'err');
    return;
  }

  const btn = document.getElementById('btnSend');
  btn.disabled    = true;
  btn.textContent = '⏳ Sende …';
  setStatus('blink', 'Sende …');
  log(`Sende ${code.split('\n').length} Zeile(n) …`, 'dim');

  try {
    const r = await fetch(`${getRobotBase()}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: code,
      signal: AbortSignal.timeout(10000),
    });

    const txt = await r.text();
    if (r.ok) {
      setStatus('ok', 'OK');
      log(`✓ ${r.status} — ${txt || '(keine Ausgabe)'}`, 'ok');
    } else {
      setStatus('err', 'Fehler');
      log(`✗ Serverfehler ${r.status}: ${txt}`, 'err');
    }
  } catch (e) {
    setStatus('err', 'Fehler');
    log(`✗ Senden fehlgeschlagen: ${e.message}`, 'err');
  } finally {
    btn.disabled    = false;
    btn.textContent = '▶ Ausführen';
  }
}


// ── 7. TOOLBAR BUTTONS ────────────────────────────────────────

document.getElementById('btnClear').addEventListener('click', () => {
  if (confirm('Gesamten Workspace leeren?')) {
    workspace.clear();
    log('Workspace geleert.', 'dim');
  }
});

document.getElementById('btnUndo').addEventListener('click', () => workspace.undo(false));
document.getElementById('btnRedo').addEventListener('click', () => workspace.undo(true));

document.getElementById('btnClearLog').addEventListener('click', () => {
  document.getElementById('logBody').innerHTML = '';
});

document.getElementById('btnSend').addEventListener('click', sendCode);
document.getElementById('btnPing').addEventListener('click', ping);


// ── 8. INIT ───────────────────────────────────────────────────

log('DiMI Blocks bereit.', 'dim');
ping();