"""HTML + JSON rendering for Mimi web dashboard v2."""
import json
from datetime import datetime, timedelta, timezone
from ..database import fetch_one, fetch_all
from .pwa import INSTALL_BANNER

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Dhaka")
except Exception:
    TZ = timezone(timedelta(hours=6))


def _q(sql, default=0):
    try:
        r = fetch_one(sql)
        return r[0] if r else default
    except Exception:
        return default


def gather():
    d = {
        "goals":     _q("SELECT COUNT(*) FROM goals"),
        "goals_a":   _q("SELECT COUNT(*) FROM goals WHERE status='active'"),
        "goals_p":   _q("SELECT COALESCE(AVG(progress),0) FROM goals WHERE status='active'"),
        "missions":  _q("SELECT COUNT(*) FROM missions"),
        "tasks_p":   _q("SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"),
        "tasks_c":   _q("SELECT COUNT(*) FROM tasks WHERE status='completed'"),
        "tasks_od":  _q("""SELECT COUNT(*) FROM tasks
                           WHERE status IN ('pending','in_progress')
                           AND due_date IS NOT NULL AND due_date < date('now')"""),
        "study_w":   _q("""SELECT COALESCE(SUM(duration_minutes),0)/60.0
                           FROM study_sessions WHERE study_date >= date('now','-6 days')"""),
        "study_t":   _q("""SELECT COALESCE(SUM(duration_minutes),0)
                           FROM study_sessions WHERE study_date=date('now')"""),
        "income":    _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='income'"),
        "expense":   _q("SELECT COALESCE(SUM(amount),0) FROM finance WHERE transaction_type='expense'"),
        "debts":     _q("SELECT COUNT(*) FROM debts WHERE status='active'"),
        "journal":   _q("SELECT COUNT(*) FROM journal"),
        "sleep_avg": _q("""SELECT COALESCE(AVG(duration_minutes),0)/60.0
                           FROM sleep WHERE sleep_date >= date('now','-6 days')"""),
    }
    d["balance"] = d["income"] - d["expense"]
    try:
        from ..xp import level_info
        lv = level_info()
        d["level"] = lv["level"]
        d["title"] = lv["title"]
        d["xp"] = lv["xp"]
        d["lvl_pct"] = lv["pct"]
    except Exception:
        d["level"] = 1; d["title"] = "-"; d["xp"] = 0; d["lvl_pct"] = 0
    d["life"] = round(
        d["goals_p"]*0.30 + min(100, d["study_w"]/7*100)*0.30
        + (d["tasks_c"]/max(1, d["tasks_c"]+d["tasks_p"]))*100*0.15
        + min(100, d["lvl_pct"])*0.25, 1)
    d["time"] = datetime.now(TZ).strftime("%H:%M:%S")
    d["date"] = datetime.now(TZ).strftime("%A, %d %b %Y")
    return d


def study_week():
    try:
        rows = fetch_all("""SELECT study_date, COALESCE(SUM(duration_minutes),0) AS m
                            FROM study_sessions
                            WHERE study_date >= date('now','-6 days')
                            GROUP BY study_date ORDER BY study_date""")
        return [{"d": r["study_date"], "m": r["m"]} for r in rows]
    except Exception:
        return []


def recent_tasks():
    try:
        rows = fetch_all("""SELECT id, title, due_date, priority, status
                            FROM tasks WHERE status IN ('pending','in_progress')
                            ORDER BY COALESCE(due_date,'9999') LIMIT 10""")
        return [dict(r) for r in rows]
    except Exception:
        return []


def recent_goals():
    try:
        rows = fetch_all("""SELECT id, title, progress, status, priority
                            FROM goals WHERE status='active'
                            ORDER BY id DESC LIMIT 5""")
        return [dict(r) for r in rows]
    except Exception:
        return []


def recent_journal():
    try:
        rows = fetch_all("""SELECT id, entry_date, title FROM journal
                            ORDER BY entry_date DESC LIMIT 5""")
        return [dict(r) for r in rows]
    except Exception:
        return []


def render_data_json():
    return json.dumps({
        "metrics": gather(),
        "study_week": study_week(),
        "tasks": recent_tasks(),
        "goals": recent_goals(),
        "journal": recent_journal(),
    }, default=str)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Mimi</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0f1115">
<meta name="mobile-web-app-capable" content="yes">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
<style>
  :root {
    --bg:#0f1115; --card:#181b22; --card2:#1f232b;
    --border:#262b35; --text:#e5e7eb; --dim:#9ca3af;
    --accent:#c084fc; --cyan:#22d3ee; --green:#4ade80;
    --yellow:#fbbf24; --red:#f87171; --blue:#60a5fa;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{background:var(--bg);color:var(--text);
    font-family:-apple-system,'Segoe UI',Roboto,sans-serif;
    font-size:15px;line-height:1.5}
  .wrap{max-width:900px;margin:0 auto;padding:20px 16px 80px}
  header{display:flex;align-items:center;justify-content:space-between;
    padding:14px 0;margin-bottom:14px;border-bottom:1px solid var(--border);
    flex-wrap:wrap;gap:8px}
  h1{font-size:20px;font-weight:600}
  h1 .ver{color:var(--dim);font-size:12px;margin-left:8px;font-weight:400}
  .clock{font-variant-numeric:tabular-nums;color:var(--accent);
    font-size:16px;font-weight:600}
  .clock .d{color:var(--dim);font-size:11px;display:block;text-align:right}
  .hero{background:linear-gradient(135deg,#2a1a4a,#1a2a3a);
    border:1px solid var(--border);border-radius:16px;padding:24px;
    margin-bottom:16px;text-align:center}
  .hero .big{font-size:52px;font-weight:800;
    background:linear-gradient(90deg,#c084fc,#22d3ee);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;line-height:1;font-variant-numeric:tabular-nums}
  .hero .sub{color:var(--dim);font-size:13px;margin-top:6px}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
    gap:12px;margin-bottom:16px}
  .card{background:var(--card);border:1px solid var(--border);
    border-radius:12px;padding:14px 16px;transition:border .2s}
  .card:hover{border-color:var(--accent)}
  .card h3{color:var(--dim);font-size:11px;font-weight:500;
    letter-spacing:.6px;text-transform:uppercase;margin-bottom:6px}
  .card .v{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums}
  .card .v.g{color:var(--green)} .card .v.r{color:var(--red)}
  .card .v.y{color:var(--yellow)} .card .v.a{color:var(--accent)}
  .card .s{color:var(--dim);font-size:11px;margin-top:4px}
  h2{font-size:13px;color:var(--dim);letter-spacing:.6px;
    text-transform:uppercase;margin:24px 0 10px;display:flex;
    align-items:center;justify-content:space-between}
  h2 button{background:var(--accent);color:#000;border:none;
    border-radius:8px;padding:6px 12px;font-size:12px;font-weight:600;
    cursor:pointer;letter-spacing:.4px}
  h2 button:hover{opacity:.85}
  .chart{background:var(--card);border:1px solid var(--border);
    border-radius:12px;padding:14px;display:flex;align-items:flex-end;
    gap:6px;height:160px}
  .bar-w{flex:1;background:linear-gradient(180deg,#22d3ee,#a855f7);
    border-radius:6px 6px 2px 2px;min-height:3px;position:relative;
    transition:height .4s ease}
  .bar-w span{position:absolute;bottom:-20px;left:0;right:0;
    text-align:center;font-size:10px;color:var(--dim)}
  .bar-w em{position:absolute;top:-18px;left:0;right:0;
    text-align:center;font-size:10px;color:var(--text);
    font-style:normal;font-variant-numeric:tabular-nums}
  ul.list{list-style:none}
  ul.list li{background:var(--card);border:1px solid var(--border);
    border-radius:10px;padding:10px 14px;margin-bottom:8px;
    display:flex;justify-content:space-between;align-items:center;
    gap:10px;font-size:14px}
  ul.list li .meta{color:var(--dim);font-size:12px;display:flex;
    align-items:center;gap:8px}
  .prio{font-size:10px;padding:2px 8px;border-radius:20px;
    background:var(--border);color:var(--text);text-transform:uppercase}
  .prio.high{background:#4a1a1a;color:#f87171}
  .prio.critical{background:#5a0e0e;color:#fca5a5}
  .prio.medium{background:#4a3f0e;color:#fbbf24}
  .prio.low{background:#0e3a2a;color:#4ade80}
  .act{background:transparent;border:1px solid var(--border);
    color:var(--text);border-radius:6px;padding:4px 10px;
    font-size:12px;cursor:pointer;font-weight:500}
  .act:hover{background:var(--border)}
  .act.ok{border-color:var(--green);color:var(--green)}
  .act.del{border-color:#3a1a1a;color:#f87171}
  .act.del:hover{background:#4a1a1a}
  .prog{height:6px;background:var(--border);border-radius:3px;
    overflow:hidden;margin-top:6px}
  .prog>i{display:block;height:100%;
    background:linear-gradient(90deg,#a855f7,#22d3ee)}
  footer{text-align:center;color:var(--dim);font-size:11px;
    margin-top:40px;padding-top:20px;border-top:1px solid var(--border)}
  .empty{color:var(--dim);font-style:italic;text-align:center;
    padding:16px;font-size:13px}
  .toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
    background:var(--card2);border:1px solid var(--accent);
    padding:12px 20px;border-radius:10px;font-size:13px;
    z-index:100;opacity:0;transition:opacity .3s;max-width:90%;
    text-align:center}
  .toast.show{opacity:1}
  .toast.err{border-color:var(--red)}
  .fab{position:fixed;bottom:20px;right:20px;background:var(--accent);
    color:#000;border:none;border-radius:50%;width:56px;height:56px;
    font-size:26px;cursor:pointer;box-shadow:0 4px 20px rgba(192,132,252,.4);
    font-weight:700;z-index:50}
  .fab:hover{transform:scale(1.05)}
  .modal{position:fixed;inset:0;background:rgba(0,0,0,.7);
    display:none;align-items:center;justify-content:center;z-index:200;
    padding:20px}
  .modal.show{display:flex}
  .modal .box{background:var(--card);border:1px solid var(--border);
    border-radius:16px;padding:20px;max-width:420px;width:100%;
    max-height:90vh;overflow-y:auto}
  .modal h3{margin-bottom:16px;color:var(--accent);font-size:16px}
  .modal label{display:block;color:var(--dim);font-size:12px;
    margin:10px 0 4px;text-transform:uppercase;letter-spacing:.5px}
  .modal input,.modal select,.modal textarea{width:100%;
    background:var(--bg);border:1px solid var(--border);
    color:var(--text);padding:10px 12px;border-radius:8px;
    font-size:14px;font-family:inherit}
  .modal input:focus,.modal select:focus,.modal textarea:focus{
    outline:none;border-color:var(--accent)}
  .modal textarea{resize:vertical;min-height:80px}
  .modal .row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .modal .btns{display:flex;gap:8px;margin-top:18px;justify-content:flex-end}
  .modal button{padding:10px 18px;border-radius:8px;border:none;
    font-weight:600;font-size:14px;cursor:pointer}
  .modal .primary{background:var(--accent);color:#000}
  .modal .cancel{background:var(--border);color:var(--text)}
  .tabs{display:flex;gap:4px;margin-bottom:10px}
  .tabs button{flex:1;background:var(--card);border:1px solid var(--border);
    color:var(--text);padding:8px;border-radius:8px;cursor:pointer;
    font-size:13px}
  .tabs button.active{background:var(--accent);color:#000;
    border-color:var(--accent);font-weight:600}
  @media (max-width:500px){
    .hero .big{font-size:44px}
    .card .v{font-size:18px}
    .modal .row{grid-template-columns:1fr}
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🤖 Agent Mimi <span class="ver">v7.0</span></h1>
    <div class="clock"><span id="t">--:--:--</span>
      <span class="d" id="d">loading</span></div>
  </header>

  <div class="hero">
    <div class="big" id="life">--</div>
    <div class="sub">Life Score · <span id="lvl">Lv1</span> ·
      <span id="xp">0 XP</span></div>
  </div>

  <div class="grid" id="cards"></div>

  <h2>Study · Last 7 Days</h2>
  <div class="chart" id="chart"></div>

  <h2>Open Tasks
    <button onclick="openModal('task')">+ Add Task</button>
  </h2>
  <ul class="list" id="tasks"></ul>

  <h2>Active Goals
    <button onclick="openModal('goal')">+ Add Goal</button>
  </h2>
  <ul class="list" id="goals"></ul>

  <h2>Recent Journal
    <button onclick="openModal('journal')">+ Add Entry</button>
  </h2>
  <ul class="list" id="journal"></ul>

  <footer>Agent Mimi · <span id="fetch">connecting</span></footer>
</div>

<button class="fab" onclick="openModal('task')" title="Add">+</button>

<div class="toast" id="toast"></div>

<div class="modal" id="modal">
  <div class="box">
    <h3 id="modal-title">Add Task</h3>
    <div class="tabs" id="modal-tabs">
      <button data-t="task">Task</button>
      <button data-t="goal">Goal</button>
      <button data-t="study">Study</button>
      <button data-t="journal">Journal</button>
    </div>
    <div id="modal-body"></div>
    <div class="btns">
      <button class="cancel" onclick="closeModal()">Cancel</button>
      <button class="primary" onclick="submitModal()">Save</button>
    </div>
  </div>
</div>

<script>
const fmt = n => (n||0).toLocaleString(undefined,{maximumFractionDigits:0});
const fmt1 = n => (n||0).toFixed(1);
let currentForm = 'task';

function clock(){
  const now = new Date();
  document.getElementById('t').textContent = now.toTimeString().slice(0,8);
  const days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  document.getElementById('d').textContent =
    days[now.getDay()]+' '+now.getDate()+' '+months[now.getMonth()];
}
setInterval(clock, 1000); clock();

function toast(msg, err=false){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (err?' err':'');
  setTimeout(()=>{ t.className='toast'; }, 2500);
}

const FORMS = {
  task: `
    <label>Title</label>
    <input id="f-title" placeholder="e.g. Finish report" autofocus>
    <label>Description</label>
    <input id="f-desc" placeholder="optional">
    <div class="row">
      <div><label>Due date</label><input id="f-due" type="date"></div>
      <div><label>Priority</label>
        <select id="f-prio">
          <option>low</option><option selected>medium</option>
          <option>high</option><option>critical</option>
        </select>
      </div>
    </div>`,
  goal: `
    <label>Title</label>
    <input id="f-title" placeholder="e.g. Learn Spanish" autofocus>
    <label>Description</label>
    <input id="f-desc" placeholder="optional">
    <div class="row">
      <div><label>Deadline</label><input id="f-due" type="date"></div>
      <div><label>Priority</label>
        <select id="f-prio">
          <option>low</option><option selected>medium</option>
          <option>high</option><option>critical</option>
        </select>
      </div>
    </div>`,
  study: `
    <label>Subject</label>
    <input id="f-subject" placeholder="e.g. Math" autofocus>
    <div class="row">
      <div><label>Date</label><input id="f-date" type="date"></div>
      <div><label>Duration (min)</label><input id="f-dur" type="number" min="0" value="30"></div>
    </div>
    <div class="row">
      <div><label>Questions</label><input id="f-q" type="number" min="0" value="0"></div>
      <div><label>Correct</label><input id="f-k" type="number" min="0" value="0"></div>
    </div>
    <label>Notes</label>
    <textarea id="f-notes" placeholder="optional"></textarea>`,
  journal: `
    <label>Title</label>
    <input id="f-title" placeholder="optional" autofocus>
    <label>Content</label>
    <textarea id="f-content" placeholder="What happened today?"></textarea>
    <div class="row">
      <div><label>Date</label><input id="f-date" type="date"></div>
      <div><label>Mood</label><input id="f-mood" placeholder="calm / happy / tired"></div>
    </div>`,
};

function openModal(kind='task'){
  currentForm = kind;
  document.getElementById('modal').classList.add('show');
  document.getElementById('modal-title').textContent =
    'Add ' + kind.charAt(0).toUpperCase() + kind.slice(1);
  document.getElementById('modal-body').innerHTML = FORMS[kind];
  document.querySelectorAll('#modal-tabs button').forEach(b=>{
    b.classList.toggle('active', b.dataset.t === kind);
  });
  // default date to today
  const dd = document.querySelector('#modal-body input[type=date]');
  if(dd && !dd.value){
    dd.value = new Date().toISOString().slice(0,10);
  }
  setTimeout(()=>{
    const f = document.querySelector('#modal-body input, #modal-body textarea');
    if(f) f.focus();
  }, 50);
}
function closeModal(){
  document.getElementById('modal').classList.remove('show');
}
document.getElementById('modal-tabs').addEventListener('click', e=>{
  if(e.target.dataset.t){
    openModal(e.target.dataset.t);
  }
});

async function submitModal(){
  const v = id => { const e = document.getElementById(id); return e ? e.value : ''; };
  let payload = {};
  let action = '';
  if(currentForm === 'task'){
    action = 'task_add';
    payload = { title: v('f-title'), description: v('f-desc'),
                due_date: v('f-due'), priority: v('f-prio') };
  } else if(currentForm === 'goal'){
    action = 'goal_add';
    payload = { title: v('f-title'), description: v('f-desc'),
                deadline: v('f-due'), priority: v('f-prio') };
  } else if(currentForm === 'study'){
    action = 'study_add';
    payload = { subject: v('f-subject'), study_date: v('f-date'),
                duration_minutes: v('f-dur'),
                questions_solved: v('f-q'), correct_answers: v('f-k'),
                notes: v('f-notes') };
  } else if(currentForm === 'journal'){
    action = 'journal_add';
    payload = { title: v('f-title'), content: v('f-content'),
                entry_date: v('f-date'), mood: v('f-mood') };
  }
  payload.action = action;
  const r = await fetch('/api/action', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const j = await r.json();
  if(j.ok){
    toast(j.message || 'Saved.');
    closeModal();
    load();
  } else {
    toast(j.error || 'Error', true);
  }
}

async function completeTask(id){
  if(!confirm('Mark task #' + id + ' as completed?')) return;
  const r = await fetch('/api/action', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'task_complete', id})
  });
  const j = await r.json();
  toast(j.message || (j.ok?'Done':'Error'), !j.ok);
  if(j.ok) load();
}
async function deleteTask(id){
  if(!confirm('Delete task #' + id + '?')) return;
  const r = await fetch('/api/action', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:'task_delete', id})
  });
  const j = await r.json();
  toast(j.message || (j.ok?'Deleted':'Error'), !j.ok);
  if(j.ok) load();
}

async function load(){
  try{
    const r = await fetch('/data.json', {cache:'no-store'});
    const j = await r.json();
    render(j);
    document.getElementById('fetch').textContent =
      'synced ' + new Date().toLocaleTimeString();
  }catch(e){
    document.getElementById('fetch').textContent = 'offline';
  }
}

function card(title, value, cls, sub){
  return `<div class="card"><h3>${title}</h3>
    <div class="v ${cls||''}">${value}</div>
    ${sub?`<div class="s">${sub}</div>`:''}</div>`;
}

function esc(s){
  return String(s).replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function render(j){
  const m = j.metrics;
  document.getElementById('life').textContent = fmt1(m.life);
  document.getElementById('lvl').textContent = 'Lv'+m.level+' '+m.title;
  document.getElementById('xp').textContent = fmt(m.xp)+' XP';

  document.getElementById('cards').innerHTML = [
    card('Goals', m.goals_a+' active', 'a', fmt1(m.goals_p)+'% avg'),
    card('Tasks', m.tasks_c+' done', 'g', m.tasks_p+' pending'),
    card('Overdue', m.tasks_od, m.tasks_od>0?'r':'g', m.tasks_od>0?'urgent':'clear'),
    card('Study 7d', fmt1(m.study_w)+'h', m.study_w>=7?'g':'y', 'today '+fmt(m.study_t)+'m'),
    card('Balance', '৳'+fmt(m.balance), m.balance>=0?'g':'r',
         'in '+fmt(m.income)+' · out '+fmt(m.expense)),
    card('Sleep avg', fmt1(m.sleep_avg)+'h', m.sleep_avg>=7?'g':'y', '7-day'),
    card('Debts', m.debts+' active', m.debts>0?'y':'g', 'outstanding'),
    card('Journal', m.journal, 'a', 'entries'),
  ].join('');

  const weeks = j.study_week || [];
  const chart = document.getElementById('chart');
  if(!weeks.length){
    chart.innerHTML = '<div class="empty">No study sessions in last 7 days</div>';
  } else {
    const max = Math.max(...weeks.map(w=>w.m), 1);
    chart.innerHTML = weeks.map(w=>{
      const h = Math.max(3, (w.m/max)*100);
      const day = w.d.slice(5);
      const hrs = (w.m/60).toFixed(1);
      return `<div class="bar-w" style="height:${h}%">
        <em>${hrs}h</em><span>${day}</span></div>`;
    }).join('');
  }

  const tl = document.getElementById('tasks');
  if(!j.tasks.length){
    tl.innerHTML = '<li class="empty">No open tasks</li>';
  } else {
    tl.innerHTML = j.tasks.map(t=>`
      <li>
        <span>${esc(t.title)}</span>
        <span class="meta">
          <span class="prio ${t.priority}">${t.priority}</span>
          ${t.due_date ? '<span>due '+t.due_date+'</span>' : ''}
          <button class="act ok" onclick="completeTask(${t.id})">✓</button>
          <button class="act del" onclick="deleteTask(${t.id})">✕</button>
        </span>
      </li>`).join('');
  }

  const gl = document.getElementById('goals');
  if(!j.goals.length){
    gl.innerHTML = '<li class="empty">No active goals</li>';
  } else {
    gl.innerHTML = j.goals.map(g=>`
      <li style="display:block">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
          <span>${esc(g.title)}</span>
          <span class="meta">${g.progress}%</span>
        </div>
        <div class="prog"><i style="width:${g.progress}%"></i></div>
      </li>`).join('');
  }

  const jl = document.getElementById('journal');
  if(!j.journal.length){
    jl.innerHTML = '<li class="empty">No journal entries</li>';
  } else {
    jl.innerHTML = j.journal.map(e=>`
      <li>
        <span>${esc(e.title || '(untitled)')}</span>
        <span class="meta">${e.entry_date}</span>
      </li>`).join('');
  }
}

// Close modal on ESC
document.addEventListener('keydown', e=>{
  if(e.key === 'Escape') closeModal();
});

// Close modal on backdrop
document.getElementById('modal').addEventListener('click', e=>{
  if(e.target.id === 'modal') closeModal();
});

load();
setInterval(load, 5000);
</script>
</body>
</html>"""


def render_page():
    html = PAGE
    if 'serviceWorker' not in html:
        html = html.replace('</body>', INSTALL_BANNER + '\n</body>', 1)
    return html


def render_static(name):
    return ("", "text/plain")
