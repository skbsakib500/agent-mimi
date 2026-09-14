"""iOS web app shell - HTML/CSS/JS as Python strings."""

CSS = r"""
:root {
  --bg:        #f2f2f7;
  --bg2:       #ffffff;
  --text:      #000000;
  --text2:     #3c3c43;
  --text3:     #8e8e93;
  --separator: rgba(60,60,67,0.29);
  --blue:      #007aff;
  --green:     #34c759;
  --red:       #ff3b30;
  --orange:    #ff9500;
  --purple:    #af52de;
  --pink:      #ff2d55;
  --teal:      #5ac8fa;
  --indigo:    #5856d6;
  --yellow:    #ffcc00;
  --blur-bg:   rgba(242,242,247,0.72);
  --nav-blur:  rgba(249,249,249,0.85);
  --card-r:    14px;
  --blur:      saturate(180%) blur(20px);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg:      #000000;
    --bg2:     #1c1c1e;
    --text:    #ffffff;
    --text2:   #ebebf5;
    --text3:   #8e8e93;
    --separator: rgba(84,84,88,0.65);
    --blur-bg: rgba(0,0,0,0.72);
    --nav-blur:rgba(28,28,30,0.85);
  }
}
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html, body {
  margin: 0; padding: 0;
  background: var(--bg); color: var(--text);
  font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', sans-serif;
  font-size: 17px; line-height: 1.35;
  -webkit-font-smoothing: antialiased;
  -webkit-user-select: none; user-select: none;
  overscroll-behavior-y: none;
  height: 100%;
  overflow: hidden;
}
#app { display: flex; flex-direction: column; height: 100vh; }

/* ─── NAV BAR (iOS large-title + small-title) ─── */
.navbar {
  position: sticky; top: 0; z-index: 100;
  background: var(--nav-blur);
  -webkit-backdrop-filter: var(--blur);
  backdrop-filter: var(--blur);
  border-bottom: 0.5px solid var(--separator);
  transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}
.navbar-top {
  display: flex; align-items: center; justify-content: space-between;
  height: 44px; padding: 0 8px;
}
.navbar-title-small {
  font-size: 17px; font-weight: 600;
  opacity: 0; transform: translateY(6px);
  transition: opacity 0.2s, transform 0.2s;
}
.navbar.condensed .navbar-title-small { opacity: 1; transform: translateY(0); }
.navbar.condensed .navbar-title-large { display: none; }
.navbar-btn {
  background: transparent; border: none; padding: 8px 10px;
  color: var(--blue); font-size: 17px; cursor: pointer;
  display: flex; align-items: center; gap: 4px;
}
.navbar-btn:active { opacity: 0.5; }
.navbar-title-large {
  font-size: 34px; font-weight: 700; padding: 4px 16px 12px;
  letter-spacing: -0.5px;
}
"""

CSS += r"""
/* ─── CONTENT AREA ─── */
.content {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 84px;
  scroll-behavior: smooth;
}
.screen { display: none; }
.screen.active {
  display: block;
  animation: screenIn 0.32s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes screenIn {
  from { opacity: 0; transform: translateX(12px); }
  to   { opacity: 1; transform: translateX(0); }
}

/* ─── CARDS ─── */
.card {
  background: var(--bg2);
  border-radius: var(--card-r);
  margin: 10px 16px;
  padding: 16px;
  box-shadow: 0 0.5px 0 var(--separator);
}
.card-press:active {
  transform: scale(0.98);
  transition: transform 0.12s;
}
.card-title {
  font-size: 12px; font-weight: 600; color: var(--text3);
  text-transform: uppercase; letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.card-value {
  font-size: 28px; font-weight: 700; letter-spacing: -0.8px;
  font-variant-numeric: tabular-nums;
}
.card-value.green { color: var(--green); }
.card-value.red   { color: var(--red); }
.card-value.blue  { color: var(--blue); }
.card-sub {
  font-size: 13px; color: var(--text3); margin-top: 4px;
}

/* ─── PROGRESS ─── */
.progress {
  height: 8px; background: var(--separator);
  border-radius: 4px; overflow: hidden; margin-top: 8px;
}
.progress-bar {
  height: 100%; background: var(--blue);
  border-radius: 4px;
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

/* ─── LIST (iOS grouped list) ─── */
.list {
  background: var(--bg2);
  border-radius: var(--card-r);
  margin: 10px 16px;
  overflow: hidden;
}
.list-row {
  display: flex; align-items: center;
  padding: 12px 16px;
  border-bottom: 0.5px solid var(--separator);
  cursor: pointer;
  transition: background 0.12s;
}
.list-row:last-child { border-bottom: none; }
.list-row:active { background: var(--separator); }
.list-row .icon {
  width: 30px; height: 30px;
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  color: #fff; margin-right: 12px;
  flex-shrink: 0;
}
.list-row .label { flex: 1; font-size: 17px; }
.list-row .value {
  font-size: 15px; color: var(--text3);
  font-variant-numeric: tabular-nums;
  margin-right: 6px;
}
.list-row .chev { color: var(--text3); font-size: 14px; }

/* ─── BOTTOM TAB BAR ─── */
.tabbar {
  position: fixed; bottom: 0; left: 0; right: 0;
  height: 84px;
  background: var(--nav-blur);
  -webkit-backdrop-filter: var(--blur);
  backdrop-filter: var(--blur);
  border-top: 0.5px solid var(--separator);
  display: flex;
  padding-bottom: 20px;
  z-index: 200;
}
.tab {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 2px; cursor: pointer;
  color: var(--text3);
  transition: color 0.15s;
  padding-top: 8px;
}
.tab .tab-icon { font-size: 22px; line-height: 1; }
.tab .tab-label { font-size: 10px; font-weight: 500; }
.tab.active { color: var(--blue); }
.tab:active { transform: scale(0.92); transition: transform 0.1s; }
"""

CSS += r"""
/* ─── CHAT ─── */
.chat-wrap {
  display: flex; flex-direction: column;
  padding: 12px 12px 12px;
  gap: 8px;
}
.bubble {
  max-width: 76%;
  padding: 10px 14px;
  border-radius: 20px;
  font-size: 16px;
  line-height: 1.35;
  word-wrap: break-word;
  white-space: pre-wrap;
  animation: bubbleIn 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(6px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.bubble.me {
  background: var(--blue); color: #fff;
  align-self: flex-end; border-bottom-right-radius: 6px;
}
.bubble.mimi {
  background: var(--bg2); color: var(--text);
  align-self: flex-start; border-bottom-left-radius: 6px;
}
.bubble.typing {
  background: var(--bg2); color: var(--text3);
  align-self: flex-start;
}

/* ─── COMPOSER (iOS message input) ─── */
.composer {
  position: fixed; bottom: 84px; left: 0; right: 0;
  background: var(--nav-blur);
  -webkit-backdrop-filter: var(--blur);
  backdrop-filter: var(--blur);
  border-top: 0.5px solid var(--separator);
  padding: 8px 10px;
  display: flex; align-items: flex-end; gap: 8px;
  z-index: 150;
}
.composer-input {
  flex: 1; min-height: 36px; max-height: 100px;
  background: var(--bg2);
  border: 0.5px solid var(--separator);
  border-radius: 18px;
  padding: 8px 14px;
  font-size: 16px; font-family: inherit;
  color: var(--text);
  outline: none; resize: none;
  -webkit-user-select: text; user-select: text;
  line-height: 1.3;
}
.composer-send {
  width: 36px; height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--blue); color: #fff;
  font-size: 18px; font-weight: 700;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.1s, opacity 0.15s;
  flex-shrink: 0;
}
.composer-send:active { transform: scale(0.88); }
.composer-send:disabled { opacity: 0.4; }

/* ─── FAB ─── */
.fab {
  position: fixed;
  bottom: 100px; right: 20px;
  width: 56px; height: 56px;
  border-radius: 50%;
  background: var(--blue); color: #fff;
  border: none; font-size: 28px; font-weight: 300;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(0,122,255,0.45);
  z-index: 180;
  transition: transform 0.15s cubic-bezier(0.22, 1, 0.36, 1);
}
.fab:active { transform: scale(0.9); }

/* ─── TOAST ─── */
.toast {
  position: fixed; bottom: 100px; left: 50%;
  transform: translateX(-50%) translateY(20px);
  background: rgba(0,0,0,0.85); color: #fff;
  padding: 12px 20px; border-radius: 20px;
  font-size: 14px; font-weight: 500;
  opacity: 0; pointer-events: none;
  transition: opacity 0.25s, transform 0.25s;
  z-index: 300;
  max-width: 88vw;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
.toast.err  { background: rgba(255,59,48,0.95); }

/* ─── SHEET (bottom modal) ─── */
.sheet-bg {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  opacity: 0; pointer-events: none;
  transition: opacity 0.28s;
  z-index: 400;
}
.sheet-bg.show { opacity: 1; pointer-events: auto; }
.sheet {
  position: fixed; left: 0; right: 0; bottom: 0;
  background: var(--bg2);
  border-radius: 20px 20px 0 0;
  padding: 12px 16px 30px;
  transform: translateY(100%);
  transition: transform 0.36s cubic-bezier(0.22, 1, 0.36, 1);
  z-index: 500;
  max-height: 86vh; overflow-y: auto;
}
.sheet.show { transform: translateY(0); }
.sheet-handle {
  width: 40px; height: 5px;
  background: var(--separator);
  border-radius: 3px;
  margin: 0 auto 14px;
}
.sheet-title {
  font-size: 20px; font-weight: 700;
  margin-bottom: 14px; letter-spacing: -0.4px;
}
.field {
  margin-bottom: 14px;
}
.field label {
  display: block; font-size: 13px; color: var(--text3);
  font-weight: 500; margin-bottom: 6px;
  text-transform: uppercase; letter-spacing: 0.4px;
}
.field input, .field select, .field textarea {
  width: 100%; padding: 12px 14px;
  background: var(--bg); border: 0.5px solid var(--separator);
  border-radius: 10px; font-size: 16px;
  font-family: inherit; color: var(--text);
  outline: none;
  -webkit-user-select: text; user-select: text;
}
.field textarea { resize: vertical; min-height: 80px; }
.btn-primary {
  width: 100%; padding: 14px;
  background: var(--blue); color: #fff;
  border: none; border-radius: 12px;
  font-size: 17px; font-weight: 600;
  cursor: pointer;
  transition: transform 0.1s;
}
.btn-primary:active { transform: scale(0.97); }
.btn-secondary {
  width: 100%; padding: 14px; margin-top: 8px;
  background: transparent; color: var(--blue);
  border: none; font-size: 17px; font-weight: 500;
  cursor: pointer;
}

/* ─── HAPTIC (visual) ─── */
@keyframes tapPulse {
  0%   { transform: scale(1); }
  50%  { transform: scale(0.94); }
  100% { transform: scale(1); }
}
.tap-pulse { animation: tapPulse 0.18s ease; }

/* ─── SWIPE INDICATOR ─── */
.swipe-cue {
  position: fixed; left: 8px; top: 50%;
  transform: translateY(-50%);
  width: 4px; height: 40px;
  background: var(--blue);
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}
.swipe-cue.show { opacity: 0.6; }
"""

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Mimi">
<meta name="theme-color" content="#007aff">
<link rel="manifest" href="/app-manifest.json">
<link rel="apple-touch-icon" href="/app-icon.svg">
<title>Mimi</title>
<style>__CSS__</style>
</head>
<body>
<div id="app">

  <!-- ═══ NAV BAR ═══ -->
  <div class="navbar" id="navbar">
    <div class="navbar-top">
      <button class="navbar-btn" id="navBack" style="visibility:hidden" onclick="goBack()">‹ Back</button>
      <div class="navbar-title-small" id="navTitleSmall"></div>
      <button class="navbar-btn" onclick="openMoreMenu()">⋯</button>
    </div>
    <div class="navbar-title-large" id="navTitleLarge">Mimi</div>
  </div>

  <!-- ═══ CONTENT ═══ -->
  <div class="content" id="content">

    <!-- HOME -->
    <div class="screen active" id="screen-home">
      <div id="homeCards"></div>
    </div>

    <!-- COUNCIL -->
    <div class="screen" id="screen-council">
      <div class="list" id="councilList"></div>
    </div>

    <!-- NUSRAT -->
    <div class="screen" id="screen-nusrat">
      <div class="chat-wrap" id="chatWrap"></div>
    </div>

    <!-- STATS -->
    <div class="screen" id="screen-stats">
      <div class="list" id="statsList"></div>
    </div>

    <!-- MORE -->
    <div class="screen" id="screen-more">
      <div class="list" id="moreList"></div>
    </div>

  </div>

  <!-- ═══ COMPOSER (Nusrat only) ═══ -->
  <div class="composer" id="composer" style="display:none">
    <textarea class="composer-input" id="composerInput" placeholder="Message Nusrat…" rows="1"></textarea>
    <button class="composer-send" id="composerSend" onclick="sendMessage()">↑</button>
  </div>

  <!-- ═══ FAB ═══ -->
  <button class="fab" id="fab" onclick="openAddSheet()" style="display:none">+</button>

  <!-- ═══ BOTTOM TABS ═══ -->
  <div class="tabbar" id="tabbar">
    <div class="tab active" data-tab="home"    onclick="switchTab('home')">
      <div class="tab-icon">⌂</div><div class="tab-label">Home</div>
    </div>
    <div class="tab" data-tab="council" onclick="switchTab('council')">
      <div class="tab-icon">♛</div><div class="tab-label">Council</div>
    </div>
    <div class="tab" data-tab="nusrat"  onclick="switchTab('nusrat')">
      <div class="tab-icon">✦</div><div class="tab-label">Nusrat</div>
    </div>
    <div class="tab" data-tab="stats"   onclick="switchTab('stats')">
      <div class="tab-icon">◉</div><div class="tab-label">Stats</div>
    </div>
    <div class="tab" data-tab="more"    onclick="switchTab('more')">
      <div class="tab-icon">⋯</div><div class="tab-label">More</div>
    </div>
  </div>

</div>

<!-- ═══ SHEET (bottom modal) ═══ -->
<div class="sheet-bg" id="sheetBg" onclick="closeSheet()"></div>
<div class="sheet" id="sheet">
  <div class="sheet-handle"></div>
  <div class="sheet-title" id="sheetTitle">Add</div>
  <div id="sheetBody"></div>
</div>

<!-- ═══ TOAST ═══ -->
<div class="toast" id="toast"></div>

<script>__JS__</script>
</body>
</html>
"""

JS = r"""
// ─── state ───
const STATE = {
  tab: 'home',
  history: [],
  data: null,
  chat: [{who:'mimi', text:'Ready, boss.'}],
  council: [],
};

// ─── haptics ───
function haptic(ms=10) {
  if (navigator.vibrate) {
    try { navigator.vibrate(ms); } catch(e) {}
  }
}

// ─── toast ───
let toastTimer = null;
function toast(msg, isErr=false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isErr ? ' err' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.className = 'toast'; }, 2200);
}

// ─── tab switching ───
function switchTab(tab, pushHistory=true) {
  if (STATE.tab === tab) return;
  if (pushHistory) STATE.history.push(STATE.tab);
  STATE.tab = tab;
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-' + tab).classList.add('active');
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tab);
  });
  // Title
  const titles = {home:'Mimi', council:'Council', nusrat:'Nusrat',
                  stats:'Stats', more:'More'};
  document.getElementById('navTitleLarge').textContent = titles[tab] || 'Mimi';
  document.getElementById('navTitleSmall').textContent = titles[tab] || '';
  // Composer / FAB
  document.getElementById('composer').style.display = (tab === 'nusrat' ? 'flex' : 'none');
  document.getElementById('fab').style.display = (tab === 'home' ? 'flex' : 'none');
  // Back button
  document.getElementById('navBack').style.visibility =
    STATE.history.length ? 'visible' : 'hidden';
  // Reset scroll
  document.getElementById('content').scrollTop = 0;
  haptic(8);
}

function goBack() {
  const prev = STATE.history.pop();
  if (prev) switchTab(prev, false);
}
"""

JS += r"""
// ─── data fetch ───
async function loadData() {
  try {
    const r = await fetch('/data.json', {cache:'no-store'});
    STATE.data = await r.json();
    renderHome();
    renderStats();
    renderCouncil();
  } catch(e) {
    toast('Offline', true);
  }
}

// ─── HOME ───
function renderHome() {
  const d = STATE.data.metrics;
  const life = d.life;
  const lvl = d.level;
  const tasksP = d.tasks_p;
  const tasksOd = d.tasks_od;
  const studyW = d.study_w;
  const studyT = d.study_t;
  const bal = d.balance;
  const inc = d.income;
  const exp = d.expense;
  const jr = d.journal;

  const html = `
    <div class="card card-press" onclick="haptic(15);toast('Lv${lvl} · ${d.title}')">
      <div class="card-title">Life Score</div>
      <div class="card-value ${life>=70?'green':life>=40?'':'red'}">${life.toFixed(1)} / 100</div>
      <div class="progress"><div class="progress-bar" style="width:${Math.min(100,life)}%"></div></div>
      <div class="card-sub">Lv${lvl} · ${d.xp || 0} XP</div>
    </div>

    <div class="card card-press" onclick="haptic();switchTab('stats')">
      <div class="card-title">Tasks</div>
      <div class="card-value ${tasksOd>0?'red':'green'}">${tasksP}</div>
      <div class="card-sub">${tasksOd} overdue</div>
    </div>

    <div class="card card-press" onclick="haptic();switchTab('stats')">
      <div class="card-title">Study · 7 days</div>
      <div class="card-value blue">${studyW.toFixed(1)} h</div>
      <div class="progress"><div class="progress-bar" style="width:${Math.min(100,studyW/7*100)}%;background:var(--green)"></div></div>
      <div class="card-sub">today ${studyT} min</div>
    </div>

    <div class="card card-press" onclick="haptic()">
      <div class="card-title">Balance</div>
      <div class="card-value ${bal>=0?'green':'red'}">৳ ${bal.toLocaleString(undefined,{maximumFractionDigits:0})}</div>
      <div class="card-sub">in ${inc.toLocaleString(undefined,{maximumFractionDigits:0})} · out ${exp.toLocaleString(undefined,{maximumFractionDigits:0})}</div>
    </div>

    <div class="card card-press" onclick="haptic()">
      <div class="card-title">Journal</div>
      <div class="card-value">${jr}</div>
      <div class="card-sub">entries</div>
    </div>
  `;
  document.getElementById('homeCards').innerHTML = html;
}

// ─── STATS ───
function renderStats() {
  const d = STATE.data.metrics;
  const rows = [
    ['Active goals',   d.goals_a, 'var(--blue)'],
    ['Goal progress',  d.goals_p.toFixed(0)+'%', 'var(--purple)'],
    ['Pending tasks',  d.tasks_p, d.tasks_p ? 'var(--orange)' : 'var(--green)'],
    ['Overdue',        d.tasks_od, d.tasks_od ? 'var(--red)' : 'var(--green)'],
    ['Study (7d)',     d.study_w.toFixed(1)+'h', d.study_w>=7 ? 'var(--green)' : 'var(--orange)'],
    ['Balance',        '৳'+d.balance.toFixed(0), d.balance>=0 ? 'var(--green)' : 'var(--red)'],
    ['Active debts',   d.debts, d.debts ? 'var(--orange)' : 'var(--green)'],
    ['Journal',        d.journal, 'var(--text2)'],
  ];
  const html = rows.map(([k,v,c]) => `
    <div class="list-row">
      <div class="label">${k}</div>
      <div class="value" style="color:${c};font-weight:600">${v}</div>
    </div>`).join('');
  document.getElementById('statsList').innerHTML = html;
}
"""

JS += r"""
// ─── COUNCIL ───
function renderCouncil() {
  const colors = {
    devops:'#8e8e93', strategy:'#5856d6', finance:'#34c759',
    admin:'#ff9500', study:'#007aff', health:'#ff2d55',
    civil:'#a2845e', research:'#5ac8fa', relations:'#af52de',
    legal:'#ff3b30'
  };
  const icons = {
    devops:'⚙', strategy:'♟', finance:'৳', admin:'▤',
    study:'✎', health:'♥', civil:'⌂', research:'⌕',
    relations:'☺', legal:'⚖'
  };
  if (!STATE.council.length) {
    document.getElementById('councilList').innerHTML =
      '<div class="list-row"><div class="label" style="color:var(--text3)">Loading…</div></div>';
    return;
  }
  const html = STATE.council.map(d => `
    <div class="list-row" onclick="haptic(15);toast('${d.name} · ${d.role}')">
      <div class="icon" style="background:${colors[d.name]||'#8e8e93'}">${icons[d.name]||'◇'}</div>
      <div class="label">${d.name}</div>
      <div class="value">${d.role}</div>
      <div class="chev">›</div>
    </div>`).join('');
  document.getElementById('councilList').innerHTML = html;
}

// ─── MORE ───
const MORE_ITEMS = [
  ['Goals',     'mimi.goals',      '#5856d6', '◈'],
  ['Missions',  'mimi.missions',   '#af52de', '◉'],
  ['Finance',   'mimi.finance',    '#34c759', '৳'],
  ['Debts',     'mimi.debts',      '#ff9500', '⚖'],
  ['Journal',   'mimi.journal',    '#ff2d55', '✐'],
  ['Predict',   'mimi.predict',    '#5ac8fa', '◐'],
  ['Review',    'mimi.ai_review',  '#007aff', '☰'],
  ['Lab',       'mimi.upgrade.lab','#ffcc00', '✚'],
  ['Sonar',     'mimi.health.diagnostic', '#34c759', '◉'],
  ['Sync',      'mimi.sync',       '#8e8e93', '↻'],
  ['Web',       'mimi.web.server', '#007aff', '◐'],
  ['Settings',  'mimi.api_manager','#8e8e93', '⚒'],
];

function renderMore() {
  const html = MORE_ITEMS.map(([label, path, color, icon]) => `
    <div class="list-row" onclick="haptic(15);runEditor('${path}','${label}')">
      <div class="icon" style="background:${color}">${icon}</div>
      <div class="label">${label}</div>
      <div class="chev">›</div>
    </div>`).join('');
  document.getElementById('moreList').innerHTML = html;
}

// ─── NUSRAT CHAT ───
function renderChat() {
  const html = STATE.chat.map(m => `
    <div class="bubble ${m.who === 'me' ? 'me' : 'mimi'}">${escapeHtml(m.text)}</div>
  `).join('');
  const w = document.getElementById('chatWrap');
  w.innerHTML = html;
  setTimeout(() => {
    document.getElementById('content').scrollTop = 999999;
  }, 30);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
"""

JS += r"""
// ─── SEND MESSAGE ───
async function sendMessage() {
  const inp = document.getElementById('composerInput');
  const text = inp.value.trim();
  if (!text) return;
  STATE.chat.push({who:'me', text});
  inp.value = '';
  inp.style.height = 'auto';
  renderChat();
  haptic(12);

  // typing indicator
  const typing = document.createElement('div');
  typing.className = 'bubble typing';
  typing.textContent = '···';
  document.getElementById('chatWrap').appendChild(typing);
  document.getElementById('content').scrollTop = 999999;

  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text})
    });
    const j = await r.json();
    typing.remove();
    const reply = j.reply || j.error || '(no reply)';
    STATE.chat.push({who:'mimi', text: reply});
    renderChat();
    haptic(10);
  } catch(e) {
    typing.remove();
    STATE.chat.push({who:'mimi', text: '[error: ' + e + ']'});
    renderChat();
  }
}

// auto-grow textarea
document.addEventListener('input', e => {
  if (e.target.id === 'composerInput') {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(100, e.target.scrollHeight) + 'px';
  }
});

// ─── SHEET ───
function openSheet(title, bodyHtml, onSave) {
  document.getElementById('sheetTitle').textContent = title;
  document.getElementById('sheetBody').innerHTML = bodyHtml;
  document.getElementById('sheetBg').classList.add('show');
  document.getElementById('sheet').classList.add('show');
  window.__sheetSave = onSave;
  haptic(10);
}

function closeSheet() {
  document.getElementById('sheetBg').classList.remove('show');
  document.getElementById('sheet').classList.remove('show');
  window.__sheetSave = null;
}

function sheetSave() {
  if (window.__sheetSave) window.__sheetSave();
}

// ─── ADD SHEET (Fab) ───
function openAddSheet() {
  haptic(15);
  const html = `
    <div class="list" style="margin:0 0 12px">
      <div class="list-row" onclick="haptic();closeSheet();openAddTask()">
        <div class="icon" style="background:var(--orange)">☑</div>
        <div class="label">New Task</div><div class="chev">›</div>
      </div>
      <div class="list-row" onclick="haptic();closeSheet();openAddGoal()">
        <div class="icon" style="background:var(--purple)">◈</div>
        <div class="label">New Goal</div><div class="chev">›</div>
      </div>
      <div class="list-row" onclick="haptic();closeSheet();openAddExpense()">
        <div class="icon" style="background:var(--red)">৳</div>
        <div class="label">New Expense</div><div class="chev">›</div>
      </div>
      <div class="list-row" onclick="haptic();closeSheet();openAddJournal()">
        <div class="icon" style="background:var(--pink)">✐</div>
        <div class="label">New Journal</div><div class="chev">›</div>
      </div>
    </div>
    <button class="btn-secondary" onclick="closeSheet()">Cancel</button>
  `;
  openSheet('Add', html, null);
}
"""

JS += r"""
// ─── ADD TASK ───
function openAddTask() {
  const html = `
    <div class="field"><label>Title</label>
      <input id="f-title" placeholder="What to do?" autofocus></div>
    <div class="field"><label>Due date</label>
      <input id="f-due" type="date"></div>
    <div class="field"><label>Priority</label>
      <select id="f-prio">
        <option>low</option><option selected>medium</option>
        <option>high</option><option>critical</option>
      </select></div>
    <button class="btn-primary" onclick="saveTask()">Add Task</button>
    <button class="btn-secondary" onclick="closeSheet()">Cancel</button>
  `;
  openSheet('New Task', html, saveTask);
  setTimeout(() => {
    const d = document.getElementById('f-due');
    if (d) d.value = new Date().toISOString().slice(0,10);
  }, 100);
}

async function saveTask() {
  const title = document.getElementById('f-title').value.trim();
  if (!title) { toast('Title required', true); return; }
  const payload = {
    action: 'task_add',
    title,
    due_date: document.getElementById('f-due').value || null,
    priority: document.getElementById('f-prio').value,
  };
  await postAction(payload, 'Task added');
}

// ─── ADD GOAL ───
function openAddGoal() {
  const html = `
    <div class="field"><label>Title</label>
      <input id="f-title" placeholder="What to achieve?" autofocus></div>
    <div class="field"><label>Deadline</label>
      <input id="f-due" type="date"></div>
    <div class="field"><label>Priority</label>
      <select id="f-prio">
        <option>low</option><option selected>medium</option>
        <option>high</option><option>critical</option>
      </select></div>
    <button class="btn-primary" onclick="saveGoal()">Add Goal</button>
    <button class="btn-secondary" onclick="closeSheet()">Cancel</button>
  `;
  openSheet('New Goal', html, saveGoal);
}

async function saveGoal() {
  const title = document.getElementById('f-title').value.trim();
  if (!title) { toast('Title required', true); return; }
  await postAction({
    action: 'goal_add',
    title,
    deadline: document.getElementById('f-due').value || null,
    priority: document.getElementById('f-prio').value,
  }, 'Goal added');
}

// ─── ADD EXPENSE ───
function openAddExpense() {
  const html = `
    <div class="field"><label>Amount</label>
      <input id="f-amt" type="number" inputmode="decimal" placeholder="0" autofocus></div>
    <div class="field"><label>Category</label>
      <input id="f-cat" placeholder="food / transport / ..."></div>
    <div class="field"><label>Description</label>
      <input id="f-desc" placeholder="optional"></div>
    <button class="btn-primary" onclick="saveExpense()">Add Expense</button>
    <button class="btn-secondary" onclick="closeSheet()">Cancel</button>
  `;
  openSheet('New Expense', html, saveExpense);
}

async function saveExpense() {
  const amt = parseFloat(document.getElementById('f-amt').value);
  if (!amt || amt <= 0) { toast('Amount required', true); return; }
  await postAction({
    action: 'expense_add',
    amount: amt,
    category: document.getElementById('f-cat').value || 'general',
    description: document.getElementById('f-desc').value || '',
  }, 'Expense added');
}

// ─── ADD JOURNAL ───
function openAddJournal() {
  const html = `
    <div class="field"><label>Title</label>
      <input id="f-title" placeholder="optional" autofocus></div>
    <div class="field"><label>Content</label>
      <textarea id="f-content" placeholder="What happened?"></textarea></div>
    <button class="btn-primary" onclick="saveJournal()">Save</button>
    <button class="btn-secondary" onclick="closeSheet()">Cancel</button>
  `;
  openSheet('New Journal', html, saveJournal);
}

async function saveJournal() {
  const content = document.getElementById('f-content').value.trim();
  if (!content) { toast('Content required', true); return; }
  await postAction({
    action: 'journal_add',
    title: document.getElementById('f-title').value || '',
    content,
  }, 'Journal saved');
}

// ─── POST ACTION ───
async function postAction(payload, successMsg) {
  try {
    const r = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const j = await r.json();
    if (j.ok) {
      toast(successMsg || 'Saved');
      haptic(20);
      closeSheet();
      loadData();
    } else {
      toast(j.error || 'Error', true);
    }
  } catch(e) {
    toast('Network error', true);
  }
}
"""

JS += r"""
// ─── MORE MENU (nav bar ⋯) ───
function openMoreMenu() {
  haptic(12);
  const html = `
    <div class="list" style="margin:0 0 12px">
      <div class="list-row" onclick="haptic();closeSheet();loadData();toast('Refreshed')">
        <div class="icon" style="background:var(--blue)">↻</div>
        <div class="label">Refresh</div>
      </div>
      <div class="list-row" onclick="haptic();closeSheet();switchTab('stats')">
        <div class="icon" style="background:var(--purple)">◉</div>
        <div class="label">View Stats</div>
      </div>
      <div class="list-row" onclick="haptic();closeSheet();switchTab('council')">
        <div class="icon" style="background:var(--orange)">♛</div>
        <div class="label">Council</div>
      </div>
      <div class="list-row" onclick="haptic();closeSheet();switchTab('nusrat')">
        <div class="icon" style="background:var(--pink)">✦</div>
        <div class="label">Talk to Nusrat</div>
      </div>
    </div>
    <button class="btn-secondary" onclick="closeSheet()">Cancel</button>
  `;
  openSheet('Menu', html, null);
}

// ─── EDITOR LAUNCH (opens classic module via server route) ───
function runEditor(path, label) {
  toast('Opening ' + label + '…');
  // Editors are TUI-only; on iOS the server shows them in browser if needed
  fetch('/api/launch?path=' + encodeURIComponent(path))
    .then(r => r.json())
    .then(j => {
      if (j.ok) toast(label + ' ready in terminal');
      else toast(j.error || 'Cannot open', true);
    }).catch(() => toast('Offline', true));
}

// ─── GESTURES ───
let touchStartX = 0, touchStartY = 0, touchStart = 0;
document.addEventListener('touchstart', e => {
  if (!e.touches.length) return;
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
  touchStart = Date.now();
}, {passive: true});

document.addEventListener('touchend', e => {
  if (!e.changedTouches.length) return;
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  const dt = Date.now() - touchStart;

  // Swipe from left edge → back
  if (touchStartX < 30 && dx > 80 && Math.abs(dy) < 60) {
    if (STATE.history.length) goBack();
  }
  // Swipe right → prev tab, left → next tab (only if large and horizontal)
  else if (Math.abs(dx) > 120 && Math.abs(dy) < 60 && dt < 500) {
    const tabs = ['home','council','nusrat','stats','more'];
    const i = tabs.indexOf(STATE.tab);
    if (dx > 0 && i > 0) switchTab(tabs[i-1]);
    else if (dx < 0 && i < tabs.length-1) switchTab(tabs[i+1]);
  }
}, {passive: true});

// ─── NAV BAR CONDENSE ON SCROLL ───
document.getElementById('content').addEventListener('scroll', e => {
  const y = e.target.scrollTop;
  const nb = document.getElementById('navbar');
  nb.classList.toggle('condensed', y > 40);
}, {passive: true});

// ─── LOAD COUNCIL FROM SERVER ───
async function loadCouncil() {
  try {
    const r = await fetch('/api/council');
    const j = await r.json();
    if (j.ok) { STATE.council = j.departments; renderCouncil(); }
  } catch(e) {}
}

// ─── PWA SERVICE WORKER ───
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/app-sw.js').catch(() => {});
}

// ─── INIT ───
async function init() {
  renderMore();
  await loadCouncil();
  await loadData();
  renderChat();
  // Event: composer send on Enter (keyboard)
  document.getElementById('composerInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}
init();
setInterval(loadData, 15000);
"""


def render_page():
    """Return the full HTML page with CSS + JS inlined."""
    html = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
    return html
