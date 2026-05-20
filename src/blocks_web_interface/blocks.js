/* ui helpers */
const metaEl    = document.getElementById('meta');
const logEl     = document.getElementById('log');
const dotEl     = document.getElementById('dot');
const statusEl  = document.getElementById('status-text');
const sendBtn   = document.getElementById('send-btn');
const previewEl = document.getElementById('preview');

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
    const map = { ok:['ok','connected'], err:['err','unreachable'], connecting:['blink','connecting...'] };
    const [cls, txt] = map[state] || ['','disconnected'];
    if (cls) dotEl.classList.add(cls);
    statusEl.textContent = txt;
}

const baseUrl     = () => `http://${document.getElementById('ip').value.trim()}:${document.getElementById('port').value.trim()}`;
const baseAddress = () => `${document.getElementById('ip').value.trim()}:${document.getElementById('port').value.trim()}`;

async function ping() {
    log(`Pinging ${baseAddress()}…`); setStatus('connecting');
    try {
        const res = await fetch(baseUrl() + '/ping', { signal: AbortSignal.timeout(3000) });
        res.ok ? (log('DiMI is reachable.','ok'), setStatus('ok')) : (log(`HTTP ${res.status}`,'err'), setStatus('err'));
    } catch(e) { log(e.message,'err'); setStatus('err'); }
}

async function send() {
    const code = generateLogo().trim();
    if (!code) { log('Nothing connected to the Start block.','dim'); return; }
    log(`Running on ${baseAddress()}…`);
    sendBtn.disabled = true; sendBtn.textContent = 'Running…';
    try {
        const res = await fetch(baseUrl() + '/execute', {
            method:'POST', headers:{'Content-Type':'text/plain'},
            body: code, signal: AbortSignal.timeout(10000),
        });
        const body = await res.text();
        if (res.ok) { setStatus('ok');  body.split('\n').forEach(l => l && log(l,'ok')); }
        else         { setStatus('err'); body.split('\n').forEach(l => l && log(l,'err')); }
    } catch(e) { log(e.message,'err'); setStatus('err'); }
    finally { sendBtn.disabled = false; sendBtn.textContent = 'Run on DiMI'; }
}

/* block registry */
const C = {
    motion:  '#4C97FF',
    pen:     '#59C059',
    looks:   '#9966FF',
    control: '#FFAB19',
    vars:    '#FF8C1A',
    print:   '#5CB1D6',
    proc:    '#FF6680',
    math:    '#5B67A5',
    logic:   '#5CA65C',
};

const NAMED_COLORS = [
    'black','red','green','yellow','blue','magenta','cyan','white',
    'gray','grey','darkred','darkgreen','darkblue','orange','pink','purple','brown',
];

const LOGO_BLOCKS = [

    /* start */
    { type:'logo_start', message0:'🚩  Start',
        nextStatement:null, colour:'#FFD500',
        tooltip:'Your program starts here. Connect blocks below.',
        toCode: () => '' },

    /* motion */
    { type:'logo_forward', message0:'move %1 steps forward',
        args0:[{type:'input_value',name:'STEPS',check:'Number'}],
        previousStatement:null, nextStatement:null, colour:C.motion,
        toCode: b => `fd ${val(b,'STEPS',50)}\n` },

    { type:'logo_backward', message0:'move %1 steps back',
        args0:[{type:'input_value',name:'STEPS',check:'Number'}],
        previousStatement:null, nextStatement:null, colour:C.motion,
        toCode: b => `bk ${val(b,'STEPS',50)}\n` },

    { type:'logo_left', message0:'turn left %1 degrees',
        args0:[{type:'input_value',name:'ANGLE',check:'Number'}],
        previousStatement:null, nextStatement:null, colour:C.motion,
        toCode: b => `lt ${val(b,'ANGLE',90)}\n` },

    { type:'logo_right', message0:'turn right %1 degrees',
        args0:[{type:'input_value',name:'ANGLE',check:'Number'}],
        previousStatement:null, nextStatement:null, colour:C.motion,
        toCode: b => `rt ${val(b,'ANGLE',90)}\n` },

    { type:'logo_home', message0:'go to home',
        previousStatement:null, nextStatement:null, colour:C.motion,
        toCode: () => `home\n` },

    /* control */
    { type:'logo_repeat',
        message0:'repeat %1 times', args0:[{type:'input_value',name:'TIMES',check:'Number'}],
        message1:'%1',              args1:[{type:'input_statement',name:'DO'}],
        previousStatement:null, nextStatement:null, colour:C.control,
        toCode: b => `repeat ${val(b,'TIMES',4)} [\n${stmts(b,'DO')}]\n` },

    { type:'logo_if',
        message0:'if %1', args0:[{type:'input_value',name:'COND', check: "Boolean"}],
        message1:'%1',        args1:[{type:'input_statement',name:'DO'}],
        previousStatement:null, nextStatement:null, colour:C.control,
        toCode: b => `if (${valExpr(b,'COND','false')}) [\n${stmts(b,'DO')}]\n` },

    { type:'logo_while',
        message0:'while %1', args0:[{type:'input_value',name:'COND', check: "Boolean"}],
        message1:'%1',           args1:[{type:'input_statement',name:'DO'}],
        previousStatement:null, nextStatement:null, colour:C.control,
        toCode: b => `while [${valExpr(b,'COND','true')}] [\n${stmts(b,'DO')}]\n` },

    /* variables */

    { type:'logo_make',
        message0:'set %1 to %2',
        args0:[
            {type:'field_input', name:'VAR', text:'x'},
            {type:'input_value', name:'VAL', text: "1", check: "Number",},
        ],
        previousStatement:null, nextStatement:null, colour:C.vars,
        toCode: b => {
            const v = b.getFieldValue('VAR') || 'x';
            return `make "${v} ${valExpr(b,'VAL','0')}\n`;
        }},
    { type:'logo_var_get',
        message0:'variable %1',
        args0:[{type:'field_input', name:'TEXT', text: "x"}],
        output:'Number', colour:C.vars,
        toCode: b => `:${valExpr(b,'TEXT','x')}` },

    /* print */
    { type:'logo_print_str',
        message0:'print %1',
        args0:[{type:'field_input', name:'TEXT', text:'hello'}],
        previousStatement:null, nextStatement:null, colour:C.print,
        toCode: b => `print [${b.getFieldValue('TEXT')}]\n` },

    // print expr
    { type:'logo_print_expr',
        message0:'print %1',
        args0:[{type:'input_value', name:'VAL'}],
        previousStatement:null, nextStatement:null, colour:C.print,
        toCode: b => `print ${valExpr(b,'VAL','0')}\n` },

    /* procedures */

    { type:'logo_proc_1arg_def',
        message0:'define %1 param %2',
        args0:[
            {type:'field_input', name:'NAME', text:'fun'},
            {type:'field_input', name:'PARAM', text:'x'},
        ],
        message1:'%1', args1:[{type:'input_statement', name:'BODY'}],
        colour:C.proc,
        toCode: b => {
            const name   = b.getFieldValue('NAME') || 'fun';
            const param = (b.getFieldValue('PARAM') || '').trim()
            const body   = stmts(b,'BODY');
            return `to ${name}${param ? " :" + param : ""}\n${body}end\n`;
        }},

    { type:'logo_proc_1arg_call',
        message0:'call %1 arg %2',
        args0:[
            {type:'field_input', name:'NAME', text:'fun'},
            {type:'input_value', name:'ARG'},
        ],
        previousStatement:null, nextStatement:null, colour:C.proc,
        toCode: b => {
            const name = b.getFieldValue('NAME') || 'fun';
            const arg  = valExpr(b,'ARG','');
            return `${name}${arg.toString() ? ' ' + arg : ''}\n`;
        }},

    /* math */
    { type:'logo_arith',
        message0:'%1 %2 %3',
        args0:[
            {type:'input_value', name:'A', check:'Number'},
            {type:'field_dropdown', name:'OP', options:[['+','+'],['-','-'],['×','*'],['÷','/'],['%','%']]},
            {type:'input_value', name:'B', check:'Number'},
        ],
        inputsInline: true,
        output:'Number', colour:C.math,
        toCode: b => `(${valExpr(b,'A','0')} ${b.getFieldValue('OP')} ${valExpr(b,'B','0')})` },

    // Unary minus
    { type:'logo_unary_minus',
        message0:'– %1',
        args0:[{type:'input_value', name:'VAL', check:'Number'}],
        output:'Number', colour:C.math,
        toCode: b => `(-${valExpr(b,'VAL','0')})` },

    // 1-arg math functions
    { type:'logo_math1',
        message0:'%1 ( %2 )',
        args0:[
            {type:'field_dropdown', name:'FN', options:[
                    ['sin','sin'],['cos','cos'],['tan','tan'],
                    ['arcsin','asin'],['arccos','acos'],['arctan','atan'],
                    ['abs','abs'],['sqrt','sqrt'],['random','rand'],
                    ['round','round'],['log','log'],
                ]},
            {type:'input_value', name:'VAL', check:'Number'},
        ],
        inputsInline: true,
        output:'Number', colour:C.math,
        toCode: b => `${b.getFieldValue('FN')} ${valExpr(b,'VAL','0')}` },

    // 2-arg math functions
    { type:'logo_math2',
        message0:'%1 ( %2 , %3 )',
        args0:[
            {type:'field_dropdown', name:'FN', options:[['mod','mod'],['power','pow']]},
            {type:'input_value', name:'A', check:'Number'},
            {type:'input_value', name:'B', check:'Number'},
        ],
        inputsInline: true,
        output:'Number', colour:C.math,
        toCode: b => `${b.getFieldValue('FN')} ${valExpr(b,'A','0')} ${valExpr(b,'B','0')}` },

    // Constants pi / e
    { type:'logo_const',
        message0:'%1',
        args0:[{type:'field_dropdown', name:'VAL', options:[['π (pi)','pi'],['e','e']]}],
        output:'Number', colour:C.math,
        toCode: b => b.getFieldValue('VAL') },

    /* logic */
    // Boolean literal
    { type:'logo_bool',
        message0:'%1',
        args0:[{type:'field_dropdown', name:'VAL', options:[['true','true'],['false','false']]}],
        output:'Boolean', colour:C.logic,
        toCode: b => b.getFieldValue('VAL') },

    // Comparison operators
    { type:'logo_compare',
        message0:'%1 %2 %3',
        args0:[
            {type:'input_value', name:'A'},
            {type:'field_dropdown', name:'OP', options:[
                    ['<','<'],['≤','<='],['=','=='],['≥','>='],['>',' >'],['≠','!='],
                ]},
            {type:'input_value', name:'B'},
        ],
        inputsInline: true,
        output:'Boolean', colour:C.logic,
        toCode: b => `(${valExpr(b,'A','0')} ${b.getFieldValue('OP').trim()} ${valExpr(b,'B','0')})` },

    // Boolean binary operators
    { type:'logo_logic_op',
        message0:'%1 %2 %3',
        args0:[
            {type:'input_value', name:'A', check:'Boolean'},
            {type:'field_dropdown', name:'OP', options:[['and','&&'],['or','||']]},
            {type:'input_value', name:'B', check:'Boolean'},
        ],
        inputsInline: true,
        output:'Boolean', colour:C.logic,
        toCode: b => `(${valExpr(b,'A','true')} ${b.getFieldValue('OP')} ${valExpr(b,'B','true')})` },

    // Boolean NOT
    { type:'logo_not',
        message0:'not %1',
        args0:[{type:'input_value', name:'VAL', check:'Boolean'}],
        output:'Boolean', colour:C.logic,
        toCode: b => `!${valExpr(b,'VAL','true')}` },
];

/* code generation */
let workspace;

function val(block, name, fallback) {
    const t = block.getInputTargetBlock(name);
    if (!t) return fallback;
    if (t.type === 'math_number') return t.getFieldValue('NUM');
    return fallback;
}

function valExpr(block, name, fallback) {
    const t = block.getInputTargetBlock(name);
    if (!t) return fallback;
    if (t.type === 'math_number') return t.getFieldValue('NUM');
    const code = blockToCode(t);
    return code !== '' ? code : fallback;
}

function stmts(block, name) {
    let code = '', child = block.getInputTargetBlock(name);
    while (child) { code += '  ' + blockToCode(child); child = child.getNextBlock(); }
    return code;
}

function blockToCode(block) {
    if (!block) return '';
    const def = LOGO_BLOCKS.find(d => d.type === block.type);
    return def ? def.toCode(block) : '';
}

/** Returns only the code chained to the Start hat; counts orphan stacks.
 *  Procedure definitions (logo_proc_def) are emitted first, unconditionally. */
function generateLogo() {
    if (!workspace) return '';
    const tops = workspace.getTopBlocks(true);
    const start = tops.find(b => b.type === 'logo_start');

    // Emit all procedure definitions regardless of connection
    let procCode = '';
    tops.filter(b => b.type === 'logo_proc_1arg_def').forEach(b => {
        procCode += blockToCode(b) + '\n';
    });

    // Emit blocks chained to start
    let mainCode = '';
    if (start) {
        let b = start.getNextBlock();
        while (b) { mainCode += blockToCode(b); b = b.getNextBlock(); }
    }

    return "to main\n" + mainCode + "end\n\n" + procCode;
}

function getOrphans() {
    if (!workspace) return 0;
    return workspace.getTopBlocks(true)
        .filter(b => b.type !== 'logo_start' && b.type !== 'logo_proc_1arg_def').length;
}

/* blockly init */
function initBlockly() {
    // Register blocks
    for (const def of LOGO_BLOCKS) {
        const { toCode, ...blockDef } = def;
        Blockly.Blocks[def.type] = { init() { this.jsonInit(blockDef); } };
    }

    const scratchTheme = Blockly.Theme.defineTheme('scratch', {
        base: Blockly.Themes.Classic,
        componentStyles: {
            workspaceBackgroundColour: 'transparent',
            toolboxBackgroundColour:   '#ffffff',
            toolboxForegroundColour:   '#1a1a1a',
            flyoutBackgroundColour:    '#f4f4f4',
            flyoutForegroundColour:    '#1a1a1a',
            flyoutOpacity:             1,
            scrollbarColour:           '#ccc',
            insertionMarkerColour:     '#333',
            insertionMarkerOpacity:    0.4,
            scrollbarOpacity:          0.5,
            cursorColour:              '#4C97FF',
        },
        fontStyle: {
            family: "'Helvetica Neue', Helvetica, Arial, sans-serif",
            weight: '700',
            size:    13,
        },
    });

    workspace = Blockly.inject('blockly-div', {
        toolbox:    document.getElementById('toolbox'),
        theme:      scratchTheme,
        renderer:   'zelos',   // ← Zelos = rounded Scratch-style corners
        grid:       { spacing: 24, length: 2, colour: '#ddd', snap: true },
        zoom:       { controls: true, wheel: true, startScale: 1.1, maxScale: 2.5, minScale: 0.4 },
        trashcan:   true,
        scrollbars: true,
    });

    // Pre-place the permanent Start hat block
    const startBlock = workspace.newBlock('logo_start');
    startBlock.initSvg();
    startBlock.render();
    startBlock.moveBy(60, 50);
    startBlock.setDeletable(false);
    startBlock.setMovable(true);

    // Live preview
    workspace.addChangeListener(() => {
        const code    = generateLogo().trim();
        const orphans = getOrphans();
        const total   = Math.max(0, workspace.getAllBlocks(false).length - 1); // exclude start hat
        metaEl.textContent = `${total} block${total !== 1 ? 's' : ''}`;

        if (code) {
            previewEl.innerHTML = esc(code) +
                (orphans ? `<div class="orphan-warn">⚠ ${orphans} disconnected stack${orphans>1?'s':''} will not run</div>` : '');
            previewEl.classList.add('has-code');
        } else {
            previewEl.innerHTML = 'Connect blocks to the 🚩 Start block…' +
                (orphans ? `<div class="orphan-warn">⚠ ${orphans} disconnected stack${orphans>1?'s':''} won't run</div>` : '');
            previewEl.classList.remove('has-code');
        }
    });

    function onResize() { Blockly.svgResize(workspace); }
    window.addEventListener('resize', onResize);
    onResize();
}

function clearBlocks() {
    if (!workspace) return;
    workspace.getAllBlocks(false).forEach(b => { if (b.type !== 'logo_start') b.dispose(false); });
}

function esc(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
}

/* draggable divider */
const divider  = document.getElementById('divider');
const rightCol = document.getElementById('right-col');
let dragging = false;

divider.addEventListener('mousedown', e => {
    dragging = true; divider.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
});
document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const r = document.querySelector('main').getBoundingClientRect();
    rightCol.style.width = Math.min(10000, Math.max(200, r.right - e.clientX)) + 'px';
    if (workspace) Blockly.svgResize(workspace);
});
document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false; divider.classList.remove('dragging');
    document.body.style.cursor = ''; document.body.style.userSelect = '';
});

/* Boot */
window.addEventListener('load', () => { initBlockly(); log('Ready.','dim'); });