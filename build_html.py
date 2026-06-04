"""
build_html.py - Generate index.html template (data loaded from his_data.js via <script>)
Output: docs/index.html
"""
import os

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(REPO_ROOT, "docs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

html_template = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>历史盘口数据查询工具</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Microsoft YaHei','微软雅黑',Arial,sans-serif; background: #f0f2f5; color: #333; min-height: 100vh; }

  .header { background: linear-gradient(135deg,#1a3c6e,#2563a8); color: white; padding: 16px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
  .header h1 { font-size: 20px; font-weight: 600; }
  .header p { font-size: 12px; opacity: 0.8; margin-top: 4px; }

  .search-area { background: white; padding: 16px 24px; border-bottom: 1px solid #e0e0e0; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .search-area label { font-weight: 600; white-space: nowrap; color: #555; }
  .search-area select { border: 2px solid #ccc; border-radius: 6px; padding: 8px 10px; font-size: 14px; outline: none; transition: border-color 0.2s; background: white; min-width: 200px; cursor: pointer; }
  .search-area select:focus { border-color: #2563a8; }
  .search-area input { border: 2px solid #ccc; border-radius: 6px; padding: 8px 14px; font-size: 15px; width: 260px; outline: none; transition: border-color 0.2s; }
  .search-area input:focus { border-color: #2563a8; }
  .search-area button { background: #2563a8; color: white; border: none; border-radius: 6px; padding: 9px 22px; font-size: 15px; cursor: pointer; font-family: inherit; transition: background 0.2s; white-space: nowrap; }
  .search-area button:hover { background: #1a3c6e; }
  .search-area button.clear { background: #888; }
  .search-area button.clear:hover { background: #555; }
  .view-switch { margin-left: auto; display: flex; gap: 8px; }
  .view-switch button { background: #4a6f8f; }
  .view-switch button.active { background: #1a3c6e; box-shadow: inset 0 0 0 2px white; }

  .match-info { background: #e8f4ff; border-left: 4px solid #2563a8; padding: 10px 16px; margin: 12px 24px 0; border-radius: 4px; font-size: 13px; display: none; }
  .match-info .match-title { font-size: 16px; font-weight: 700; color: #1a3c6e; margin-bottom: 4px; }
  .match-info .meta { color: #555; }

  .table-container { padding: 12px 24px 24px; overflow-x: auto; }

  .no-result { text-align: center; padding: 60px; color: #aaa; font-size: 16px; display: none; }
  .hint { text-align: center; padding: 60px; color: #aaa; font-size: 14px; }

  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); font-size: 13px; min-width: 1400px; }
  th { background: #1a3c6e; color: white; padding: 10px 7px; text-align: center; font-weight: 600; white-space: nowrap; }
  th.group-ng { background: #1e5c2e; }
  th.group-tg { background: #5b3a70; }
  th.group-ou-base { background: #b52b2b; }
  th.group-ou-hv1 { background: #8b1a1a; }
  th.group-ou-hv2 { background: #6b1414; }
  th.group-win-base { background: #2a6b5e; }
  th.group-win-hv1 { background: #1f5348; }
  th.group-win-hv2 { background: #153d34; }
  td.ou-divider, th.ou-divider { border-right: 2px solid rgba(255,255,255,0.3); }
  td { padding: 6px 5px; text-align: center; border-bottom: 1px solid #f0f0f0; white-space: nowrap; vertical-align: middle; line-height: 1.35; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #f5f9ff; }

  .folder-cell { font-weight: 700; color: #1a3c6e; font-family: monospace; font-size: 11px; }
  .missing { color: #ccc; font-style: italic; font-size: 10px; }

  .ng-val { color: #1e5c2e; font-weight: 500; }
  .tg-val { color: #5b3a70; font-weight: 500; }
  .ou-val { color: #8b0000; font-weight: 500; }
  .win-val { color: #00695c; font-weight: 500; }
  .fp-line { color: #1565c0; font-size: 10px; font-weight: 400; margin-top: 2px; display: block; }
  .ev-line { font-size: 10px; font-weight: 600; margin-top: 2px; display: block; }
  .ev-pos { color: #d32f2f; }
  .ev-neg { color: #666; }

  .changed { background: #fff3cd !important; }

  .subheader-row th { background: #2b5797; font-size: 10px; padding: 5px 3px; }
  .subheader-row th.group-ng { background: #2d7a3f; }
  .subheader-row th.group-tg { background: #754a90; }
  .subheader-row th.group-ou-base { background: #c73e3e; }
  .subheader-row th.group-ou-hv1 { background: #a02828; }
  .subheader-row th.group-ou-hv2 { background: #801818; }
  .subheader-row th.group-win-base { background: #3d8b7a; }
  .subheader-row th.group-win-hv1 { background: #2c6b5d; }
  .subheader-row th.group-win-hv2 { background: #1d5246; }

  .autocomplete-list { position: absolute; background: white; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1000; max-height: 250px; overflow-y: auto; min-width: 300px; }
  .autocomplete-list div { padding: 8px 12px; cursor: pointer; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
  .autocomplete-list div:hover { background: #e8f4ff; }
  .autocomplete-list div em { font-style: normal; color: #2563a8; font-weight: 600; }
  .autocomplete-wrapper { position: relative; }

  .legend { display: flex; gap: 16px; padding: 0 24px 8px; font-size: 12px; flex-wrap: wrap; }
  .legend-item { display: flex; align-items: center; gap: 5px; }
  .legend-color { width: 14px; height: 14px; border-radius: 2px; }

  .view-ou, .view-win { display: none; }
  .view-ou.active, .view-win.active { display: block; }
</style>
</head>
<body>

<div class="header">
  <h1>历史盘口数据查询工具</h1>
  <p>读取所有时间戳文件夹 · 按时序对比 odds_config / numberofgoals / overunder / winodds · 自动计算EV与公平概率</p>
</div>

<div class="search-area">
  <label>联赛：</label>
  <select id="leagueSelect" onchange="onLeagueChange()">
    <option value="">-- 请选择联赛 --</option>
  </select>
  <label>比赛：</label>
  <div class="autocomplete-wrapper">
    <input type="text" id="searchInput" placeholder="先选择联赛，再输入/选择赛事ID或球队名" autocomplete="off" disabled />
    <div class="autocomplete-list" id="autocomplete" style="display:none"></div>
  </div>
  <button onclick="doSearch()">查询</button>
  <button class="clear" onclick="doClear()">清除</button>
  <div class="view-switch">
    <button id="btnOu" class="active" onclick="switchView('ou')">大小球盘口</button>
    <button id="btnWin" onclick="switchView('win')">让球盘口</button>
  </div>
  <span id="statusTip" style="color:#888; font-size:13px;"></span>
</div>

<div class="match-info" id="matchInfo">
  <div class="match-title" id="matchTitle"></div>
  <div class="meta" id="matchMeta"></div>
</div>

<div class="legend" id="legend" style="display:none">
  <span style="color:#555; font-weight:600;">列色标：</span>
  <span class="legend-item"><span class="legend-color" style="background:#1e5c2e"></span>进球分布赔率</span>
  <span class="legend-item"><span class="legend-color" style="background:#5b3a70"></span>总进球/净胜球概率</span>
  <span class="legend-item"><span class="legend-color" style="background:#7a1e1e"></span>大小球/让球赔率+公平P(蓝)+EV(红正)</span>
  <span class="legend-item"><span class="legend-color" style="background:#fff3cd;border:1px solid #e0c060"></span>数值变化</span>
</div>

<div class="view-ou active" id="viewOu">
  <div class="no-result" id="noResultOu">未找到 ID 对应的记录</div>
  <div class="hint" id="hintOu">请在上方输入赛事 ID 进行查询</div>
  <div class="table-container" id="tableOu"></div>
</div>

<div class="view-win" id="viewWin">
  <div class="no-result" id="noResultWin">未找到 ID 对应的记录</div>
  <div class="hint" id="hintWin">请在上方输入赛事 ID 进行查询</div>
  <div class="table-container" id="tableWin"></div>
</div>

<script src="his_data.js"></script>
<script>
// ========== 核心计算函数 ==========
function normalizeOdds(oddsArr) {
  var probs = [], sumInv = 0, invs = [];
  for (var i = 0; i < 6; i++) {
    var v = parseFloat(oddsArr[i]);
    if (isNaN(v) || v <= 0) v = 9999;
    var inv = 1 / v;
    invs.push(inv);
    sumInv += inv;
  }
  if (sumInv === 0) return [0.167,0.167,0.167,0.167,0.167,0.165];
  for (var i = 0; i < 6; i++) probs.push(invs[i] / sumInv);
  var s = probs.reduce(function(a,b){return a+b;},0);
  for (var i=0;i<6;i++) probs[i] /= s;
  return probs;
}

// 总进球概率（0-7+）
function calcTotalGoals(hp, ap) {
  var tg = new Array(8).fill(0);
  var h = hp, a = ap;
  tg[0] = (h[0]||0) * (a[0]||0);
  tg[1] = (h[0]||0)*(a[1]||0) + (h[1]||0)*(a[0]||0);
  tg[2] = (h[0]||0)*(a[2]||0) + (h[1]||0)*(a[1]||0) + (h[2]||0)*(a[0]||0);
  tg[3] = (h[0]||0)*(a[3]||0) + (h[1]||0)*(a[2]||0) + (h[2]||0)*(a[1]||0) + (h[3]||0)*(a[0]||0);
  tg[4] = (h[0]||0)*(a[4]||0) + (h[1]||0)*(a[3]||0) + (h[2]||0)*(a[2]||0) + (h[3]||0)*(a[1]||0) + (h[4]||0)*(a[0]||0);
  tg[5] = (h[0]||0)*(a[5]||0) + (h[1]||0)*(a[4]||0) + (h[2]||0)*(a[3]||0) + (h[3]||0)*(a[2]||0) + (h[4]||0)*(a[1]||0) + (h[5]||0)*(a[0]||0);
  tg[6] = (h[1]||0)*(a[5]||0) + (h[2]||0)*(a[4]||0) + (h[3]||0)*(a[3]||0) + (h[4]||0)*(a[2]||0) + (h[5]||0)*(a[1]||0);
  var sum06 = 0;
  for (var i = 0; i <= 6; i++) sum06 += tg[i];
  tg[7] = Math.max(0, 1 - sum06);
  return tg;
}

// 净胜球概率（-4- .. +4+，基于进球分布1-6球）
function calcGoalDiff(hp, ap) {
  var hProb = new Array(7).fill(0);
  var aProb = new Array(7).fill(0);
  var sumH = 0, sumA = 0;
  for (var i=0;i<6;i++) {
    hProb[i+1] = hp[i];
    aProb[i+1] = ap[i];
    sumH += hp[i];
    sumA += ap[i];
  }
  hProb[0] = Math.max(0, 1 - sumH);
  aProb[0] = Math.max(0, 1 - sumA);
  // 卷积净胜球 -6..+6
  var gd = new Array(13).fill(0);
  for (var hg=0; hg<=6; hg++) {
    for (var ag=0; ag<=6; ag++) {
      var idx = hg - ag + 6;
      gd[idx] += hProb[hg] * aProb[ag];
    }
  }
  // 合并到 -4- .. +4+
  var result = new Array(9).fill(0);
  for (var d=-6; d<=6; d++) {
    var val = gd[d+6];
    if (d < -4) result[0] += val;
    else if (d > 4) result[8] += val;
    else result[d+4] += val;
  }
  return result;
}

// 亚洲盘EV计算（用于总进球，数组长度8，索引0~7对应0~7+球）
function calcAsianEV(handicap, overOdds, underOdds, totalProb) {
  var intPart = Math.floor(handicap);
  var frac = Math.round((handicap - intPart) * 100) / 100;
  var pOver = 0, pPush = 0, pUnder = 0;

  if (Math.abs(frac - 0.5) < 0.01) {
    for (var g = 0; g < 7; g++) { if (g > handicap) pOver += totalProb[g]; }
    pOver += totalProb[7];
    pUnder = 1 - pOver;
  } else if (Math.abs(frac) < 0.01 || Math.abs(frac - 0.0) < 0.01) {
    for (var g = 0; g < 7; g++) {
      if (g > handicap) pOver += totalProb[g];
      else if (Math.abs(g - handicap) < 0.01) pPush += totalProb[g];
    }
    pOver += totalProb[7];
    pUnder = 1 - pOver - pPush;
  } else if (Math.abs(frac - 0.25) < 0.01 || Math.abs(frac - 0.75) < 0.01) {
    var lo, hi;
    if (frac < 0.5) { lo = intPart; hi = intPart + 0.5; }
    else { lo = intPart + 0.5; hi = intPart + 1.0; }
    var rL = calcAsianEV(lo, overOdds, underOdds, totalProb);
    var rH = calcAsianEV(hi, overOdds, underOdds, totalProb);
    return {
      evOver: (rL.evOver + rH.evOver) / 2,
      evUnder: (rL.evUnder + rH.evUnder) / 2,
      fairOver: ((rL.evOver + rH.evOver)/2 + 1) / overOdds,
      fairUnder: ((rL.evUnder + rH.evUnder)/2 + 1) / underOdds
    };
  } else {
    for (var g = 0; g < 7; g++) { if (g > handicap) pOver += totalProb[g]; }
    pOver += totalProb[7];
    pUnder = 1 - pOver;
  }

  var evOver = pOver * (overOdds - 1) - pUnder * 1 + pPush * 0;
  var evUnder = pUnder * (underOdds - 1) - pOver * 1 + pPush * 0;
  return {
    evOver: evOver,
    evUnder: evUnder,
    fairOver: (evOver + 1) / overOdds,
    fairUnder: (evUnder + 1) / underOdds
  };
}

// 让球亚洲盘 EV 计算（基于净胜球概率数组，索引0~8对应 -4-,-3,...,+4+）
// 规则：设 I = 净胜球 + 盘口（盘口带符号）
// I >= 0.5  => 主队全赢
// I == 0.25 => 主队赢半
// I == 0    => 走盘
// I == -0.25=> 主队输半
// I <= -0.5 => 主队全输
function calcAsianEVForGD(handicap, homeOdds, awayOdds, gdProbs) {
  var gdValues = [-4, -3, -2, -1, 0, 1, 2, 3, 4];
  var pHomeWin = 0, pHomeHalf = 0, pPush = 0, pAwayHalf = 0, pAwayWin = 0;

  for (var i = 0; i < gdValues.length; i++) {
    var g = gdValues[i];
    var I = g + handicap;  // 净胜球 + 盘口
    var prob = gdProbs[i];
    if (I >= 0.5) {
      pHomeWin += prob;
    } else if (I >= 0.25 && I < 0.5) {
      // 通常精确等于0.25，考虑浮点误差
      if (Math.abs(I - 0.25) < 1e-6) pHomeHalf += prob;
      else pHomeWin += prob; // 实际上不会出现
    } else if (Math.abs(I) < 1e-6) {
      pPush += prob;
    } else if (I <= -0.5) {
      pAwayWin += prob;
    } else if (I <= -0.25 && I > -0.5) {
      if (Math.abs(I + 0.25) < 1e-6) pAwayHalf += prob;
      else pAwayWin += prob;
    }
  }

  // 计算期望收益（以1单位投注主队为例）
  var evHome = pHomeWin * (homeOdds - 1) + pHomeHalf * ((homeOdds - 1) / 2) + pPush * 0 + pAwayHalf * (-0.5) + pAwayWin * (-1);
  var evAway = pAwayWin * (awayOdds - 1) + pAwayHalf * ((awayOdds - 1) / 2) + pPush * 0 + pHomeHalf * (-0.5) + pHomeWin * (-1);

  var fairHome = (evHome + 1) / homeOdds;
  var fairAway = (evAway + 1) / awayOdds;

  return {
    evHome: evHome,
    evAway: evAway,
    fairHome: fairHome,
    fairAway: fairAway
  };
}

// ========== 数据初始化 ==========
var DATA = RAW_DATA;
var FOLDER_LIST = FOLDERS;

// 构建联赛索引
var allLeagues = {};
var leagueNames = [];
(function buildLeagueIndex() {
  var leagueSet = {};
  for (var fi = 0; fi < FOLDER_LIST.length; fi++) {
    var fd = DATA[FOLDER_LIST[fi]] || {};
    for (var id in fd) {
      var oc = (fd[id] && fd[id].oc) || {};
      if (!oc.st) continue;
      var ln = oc.st;
      if (!leagueSet[ln]) {
        leagueSet[ln] = true;
        leagueNames.push(ln);
        allLeagues[ln] = {};
      }
      if (!allLeagues[ln][id]) {
        allLeagues[ln][id] = { gt: oc.gt||'', st: oc.st||'', sh: oc.sh||'', sa: oc.sa||'' };
      }
    }
  }
  leagueNames.sort();
})();

(function populateLeagues() {
  var sel = document.getElementById('leagueSelect');
  for (var li = 0; li < leagueNames.length; li++) {
    var opt = document.createElement('option');
    opt.value = leagueNames[li];
    opt.textContent = leagueNames[li] + ' (' + Object.keys(allLeagues[leagueNames[li]]).length + '场)';
    sel.appendChild(opt);
  }
})();

var currentIdIndex = {};

function onLeagueChange() {
  var selVal = document.getElementById('leagueSelect').value;
  var inputEl = document.getElementById('searchInput');
  var acEl = document.getElementById('autocomplete');
  inputEl.value = '';
  acEl.style.display = 'none';
  document.getElementById('tableOu').innerHTML = '';
  document.getElementById('tableWin').innerHTML = '';
  document.getElementById('matchInfo').style.display = 'none';
  document.getElementById('noResultOu').style.display = 'none';
  document.getElementById('noResultWin').style.display = 'none';
  document.getElementById('hintOu').style.display = 'block';
  document.getElementById('hintWin').style.display = 'block';
  document.getElementById('legend').style.display = 'none';
  document.getElementById('statusTip').textContent = '';

  if (!selVal) {
    currentIdIndex = {};
    inputEl.disabled = true;
    inputEl.placeholder = '先选择联赛，再输入/选择赛事ID或球队名';
    return;
  }
  inputEl.disabled = false;
  inputEl.placeholder = '输入ID或球队名搜索...';
  currentIdIndex = allLeagues[selVal] || {};
  document.getElementById('statusTip').textContent = '当前联赛共 ' + Object.keys(currentIdIndex).length + ' 场比赛';
}

// 自动补全
var searchInput = document.getElementById('searchInput');
var autocompleteEl = document.getElementById('autocomplete');
searchInput.addEventListener('input', function() {
  var q = this.value.trim().toLowerCase();
  var leagueSel = document.getElementById('leagueSelect').value;
  if (!leagueSel || !q) { autocompleteEl.style.display='none'; return; }
  var matches = [];
  for (var id in currentIdIndex) {
    var info = currentIdIndex[id];
    var matchText = (id + ' ' + (info.sh||'') + ' ' + (info.sa||'') + ' ' + (info.gt||'')).toLowerCase();
    if (matchText.indexOf(q) !== -1) matches.push(id);
    if (matches.length >= 20) break;
  }
  if (!matches.length) { autocompleteEl.style.display='none'; return; }
  var html = '';
  for (var mi = 0; mi < matches.length; mi++) {
    var idA = matches[mi];
    var info = currentIdIndex[idA];
    var hlInfo = info.sh ? (info.sh+' vs '+info.sa) : '';
    var timeStr = info.gt ? info.gt.substring(4,6)+'/'+info.gt.substring(6,8) : '';
    html += '<div onclick="selectId(\''+idA+'\')">' +
      '<b>' + idA + '</b> <span style="color:#888;font-size:11px">' +
      hlInfo + (timeStr ? ' ['+timeStr+']' : '') + '</span></div>';
  }
  autocompleteEl.innerHTML = html;
  autocompleteEl.style.display = 'block';
});
searchInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') { autocompleteEl.style.display='none'; doSearch(); }
  if (e.key === 'Escape') { autocompleteEl.style.display='none'; }
});
document.addEventListener('click', function(e) {
  if (!e.target.closest('.autocomplete-wrapper')) autocompleteEl.style.display='none';
});
function selectId(id) {
  searchInput.value = id;
  autocompleteEl.style.display='none';
  doSearch();
}

function doClear() {
  searchInput.value = '';
  document.getElementById('tableOu').innerHTML = '';
  document.getElementById('tableWin').innerHTML = '';
  document.getElementById('matchInfo').style.display = 'none';
  document.getElementById('noResultOu').style.display = 'none';
  document.getElementById('noResultWin').style.display = 'none';
  document.getElementById('hintOu').style.display = 'block';
  document.getElementById('hintWin').style.display = 'block';
  document.getElementById('legend').style.display = 'none';
  document.getElementById('statusTip').textContent = '';
  var leagueSel = document.getElementById('leagueSelect');
  if (leagueSel) {
    leagueSel.value = '';
    onLeagueChange();
  }
}

function switchView(view) {
  document.getElementById('btnOu').classList.toggle('active', view === 'ou');
  document.getElementById('btnWin').classList.toggle('active', view === 'win');
  document.getElementById('viewOu').classList.toggle('active', view === 'ou');
  document.getElementById('viewWin').classList.toggle('active', view === 'win');
}

function doSearch() {
  var id = searchInput.value.trim();
  if (!id) return;

  var leagueSel = document.getElementById('leagueSelect').value;
  if (leagueSel && !currentIdIndex[id]) {
    document.getElementById('noResultOu').style.display = 'block';
    document.getElementById('noResultWin').style.display = 'block';
    document.getElementById('hintOu').style.display = 'none';
    document.getElementById('hintWin').style.display = 'none';
    document.getElementById('matchInfo').style.display = 'none';
    document.getElementById('legend').style.display = 'none';
    document.getElementById('statusTip').textContent = '该ID不属于所选联赛，请重新选择联赛或ID';
    return;
  }

  document.getElementById('hintOu').style.display = 'none';
  document.getElementById('hintWin').style.display = 'none';
  document.getElementById('noResultOu').style.display = 'none';
  document.getElementById('noResultWin').style.display = 'none';
  document.getElementById('tableOu').innerHTML = '';
  document.getElementById('tableWin').innerHTML = '';
  document.getElementById('matchInfo').style.display = 'none';
  document.getElementById('legend').style.display = 'flex';

  var rows = [];
  for (var ri = 0; ri < FOLDER_LIST.length; ri++) {
    var folder = FOLDER_LIST[ri];
    var fd = DATA[folder] || {};
    rows.push({ folder: folder, rec: (fd && fd[id]) ? fd[id] : null });
  }

  var hasAny = rows.some(function(r){ return r.rec !== null; });
  if (!hasAny) {
    document.getElementById('noResultOu').style.display = 'block';
    document.getElementById('noResultWin').style.display = 'block';
    document.getElementById('statusTip').textContent = '';
    return;
  }

  for (var ri3 = 0; ri3 < rows.length; ri3++) {
    var rInfo = rows[ri3];
    if (rInfo.rec && rInfo.rec.oc && rInfo.rec.oc.gt) {
      var ocv = rInfo.rec.oc;
      document.getElementById('matchTitle').textContent = (ocv.sh||'') + ' vs ' + (ocv.sa||'');
      document.getElementById('matchMeta').textContent = '联赛：' + (ocv.st||'-') + ' | 赛事时间：' + (ocv.gt||'-');
      document.getElementById('matchInfo').style.display = 'block';
      break;
    }
  }

  var count = rows.filter(function(r){ return r.rec !== null; }).length;
  document.getElementById('statusTip').textContent = '共找到 ' + count + ' 个时间段的数据';

  buildOuTable(rows);
  buildWinTable(rows);
}

// 大小球表格
function buildOuTable(rows) {
  var container = document.getElementById('tableOu');
  var table = document.createElement('table');
  var ngCols = ['h1','h2','h3','h4','h5','h6','a1','a2','a3','a4','a5','a6'];
  var tgLabels = ['TG0','TG1','TG2','TG3','TG4','TG5','TG6','TG7+'];
  var theadHTML =
    '<thead>' +
    '  <tr><th rowspan="2">时间戳</th><th colspan="12" class="group-ng">进球分布赔率</th><th colspan="8" class="group-tg">总进球概率</th><th colspan="9" class="group-ou-base">大小球赔率 + 公平概率 + EV</th></tr>' +
    '  <tr class="subheader-row">' +
    '    <th>H1</th><th>H2</th><th>H3</th><th>H4</th><th>H5</th><th>H6</th>' +
    '    <th>A1</th><th>A2</th><th>A3</th><th>A4</th><th>A5</th><th>A6</th>';
  for (var ti=0; ti<tgLabels.length; ti++) theadHTML += '<th>'+tgLabels[ti]+'</th>';
  theadHTML +=
    '    <th class="group-ou-base">大球OO</th><th class="group-ou-base">小球UO</th><th class="group-ou-base ou-divider">盘口LI</th>' +
    '    <th class="group-ou-hv1">HV1大</th><th class="group-ou-hv1">HV1小</th><th class="group-ou-hv1 ou-divider">HV1盘</th>' +
    '    <th class="group-ou-hv2">HV2大</th><th class="group-ou-hv2">HV2小</th><th class="group-ou-hv2">HV2盘</th>' +
    '  </tr></thead>';
  table.innerHTML = theadHTML + '<tbody></tbody>';
  container.appendChild(table);
  var tbody = table.querySelector('tbody');

  var prevNg = null, prevTg = null, prevOuLines = null;

  for (var ri=0; ri<rows.length; ri++) {
    var folder = rows[ri].folder, rec = rows[ri].rec;
    var tr = document.createElement('tr');
    if (!rec) {
      tr.innerHTML = '<td class="folder-cell">'+folder+'</td><td colspan="29" class="missing">— 该时间段无此赛事 —</td>';
      tbody.appendChild(tr);
      continue;
    }
    var ng = rec.ng || {}, ou = rec.ou || {};
    var curNg = ngCols.map(function(k){ return ng[k]||''; });
    var htmlOut = '<td class="folder-cell">'+folder+'</td>';

    for (var ni=0; ni<ngCols.length; ni++) {
      var nval = ng[ngCols[ni]] || '<span class="missing">-</span>';
      var nchg = (prevNg && ng[ngCols[ni]] && prevNg[ni] !== ng[ngCols[ni]]) ? ' changed' : '';
      htmlOut += '<td class="ng-val'+nchg+'">'+nval+'</td>';
    }

    var hasNgData = ngCols.every(function(k){ return ng[k] && parseFloat(ng[k])>0; });
    var tgProbs = null;
    if (hasNgData) {
      var homeOdds = [ng.h1,ng.h2,ng.h3,ng.h4,ng.h5,ng.h6];
      var awayOdds = [ng.a1,ng.a2,ng.a3,ng.a4,ng.a5,ng.a6];
      var hp = normalizeOdds(homeOdds);
      var ap = normalizeOdds(awayOdds);
      tgProbs = calcTotalGoals(hp, ap);
    }
    var curTg = tgProbs ? tgProbs.slice() : new Array(8).fill('');
    for (var tgi=0; tgi<8; tgi++) {
      var tval = tgProbs ? (tgProbs[tgi]*100).toFixed(1)+'%' : '<span class="missing">-</span>';
      var tchg = (prevTg && tgProbs && prevTg[tgi]!=='' && Math.abs(prevTg[tgi]-tgProbs[tgi])>0.005) ? ' changed' : '';
      htmlOut += '<td class="tg-val'+tchg+'">'+tval+'</td>';
    }

    var hivStr = ou.hi_var || '';
    var hivGroups = [];
    if (hivStr) {
      var lines = hivStr.split('#');
      var grpMap = {}, grpOrder = [];
      for (var hi=0; hi<lines.length; hi++) {
        var parts = lines[hi].trim().split(',');
        if (parts.length<5) continue;
        var hv = parseFloat(parts[1])/4;
        var key = hv.toFixed(2);
        if (!grpMap[key]) { grpMap[key]={over:'',under:''}; grpOrder.push(key); }
        var dir = parts[4].trim().toUpperCase();
        var odds = (parseFloat(parts[0])/1000).toFixed(2);
        if (dir==='H') grpMap[key].over = odds;
        else if (dir==='L') grpMap[key].under = odds;
      }
      for (var gidx=0; gidx<grpOrder.length; gidx++) {
        var hk = grpOrder[gidx];
        hivGroups.push({over: grpMap[hk].over, under: grpMap[hk].under, hcap: hk});
      }
    }
    var allLines = [
      { over: ou.oo||'', under: ou.uo||'', hcap: ou.li ? (parseFloat(ou.li)/4).toString() : '' },
      hivGroups[0] || {over:'',under:'',hcap:''},
      hivGroups[1] || {over:'',under:'',hcap:''}
    ];
    var prevLines = prevOuLines || null;
    for (var lix=0; lix<3; lix++) {
      var line = allLines[lix];
      var pLine = prevLines ? prevLines[lix] : null;
      var ovStr=line.over, unStr=line.under, hcStr=line.hcap;
      var ovNum=parseFloat(ovStr)||0, unNum=parseFloat(unStr)||0, hcNum=parseFloat(hcStr)||0;
      var chO = (pLine && ovStr && pLine.over!==ovStr)?' changed':'';
      var chU = (pLine && unStr && pLine.under!==unStr)?' changed':'';
      var chH = (pLine && hcStr && pLine.hcap!==hcStr)?' changed':'';
      var divClass = (lix===0)?' ou-divider':'';
      if (!ovStr && !unStr && !hcStr) {
        htmlOut += '<td class="ou-val"><span class="missing">-</span></td><td class="ou-val"><span class="missing">-</span></td><td class="ou-val'+divClass+'"><span class="missing">-</span></td>';
      } else {
        var cellO = ovStr, cellU = unStr;
        if (tgProbs && ovNum>0 && unNum>0 && !isNaN(hcNum)) {
          try {
            var res = calcAsianEV(hcNum, ovNum, unNum, tgProbs);
            if (res.fairOver>0) cellO += '<span class="fp-line">公平P:'+(res.fairOver*100).toFixed(1)+'%</span>';
            if (!isNaN(res.evOver)) cellO += '<span class="ev-line '+(res.evOver>0?'ev-pos':'ev-neg')+'">EV '+(res.evOver>=0?'+':'')+res.evOver.toFixed(2)+'</span>';
            if (res.fairUnder>0) cellU += '<span class="fp-line">公平P:'+(res.fairUnder*100).toFixed(1)+'%</span>';
            if (!isNaN(res.evUnder)) cellU += '<span class="ev-line '+(res.evUnder>0?'ev-pos':'ev-neg')+'">EV '+(res.evUnder>=0?'+':'')+res.evUnder.toFixed(2)+'</span>';
          } catch(e) {}
        }
        htmlOut += '<td class="ou-val'+chO+'">'+cellO+'</td><td class="ou-val'+chU+'">'+cellU+'</td><td class="ou-val'+chH+divClass+'">'+hcStr+'</td>';
      }
    }
    tr.innerHTML = htmlOut;
    tbody.appendChild(tr);
    prevNg = curNg;
    prevTg = curTg;
    prevOuLines = allLines.slice();
  }
}

// 让球表格
function buildWinTable(rows) {
  var container = document.getElementById('tableWin');
  var table = document.createElement('table');
  var ngCols = ['h1','h2','h3','h4','h5','h6','a1','a2','a3','a4','a5','a6'];
  var displayLabels = ['+4+', '+3', '+2', '+1', '0', '-1', '-2', '-3', '-4-'];
  var theadHTML =
    '<thead>' +
    '  <tr><th rowspan="2">时间戳</th><th colspan="12" class="group-ng">进球分布赔率</th><th colspan="9" class="group-tg">净胜球概率</th><th colspan="9" class="group-win-base">让球赔率 + 公平概率 + EV</th></tr>' +
    '  <tr class="subheader-row">' +
    '    <th>H1</th><th>H2</th><th>H3</th><th>H4</th><th>H5</th><th>H6</th>' +
    '    <th>A1</th><th>A2</th><th>A3</th><th>A4</th><th>A5</th><th>A6</th>';
  for (var ti=0; ti<displayLabels.length; ti++) theadHTML += '<th>'+displayLabels[ti]+'</th>';
  theadHTML +=
    '    <th class="group-win-base">主队</th><th class="group-win-base">客队</th><th class="group-win-base ou-divider">盘口</th>' +
    '    <th class="group-win-hv1">HV1主</th><th class="group-win-hv1">HV1客</th><th class="group-win-hv1 ou-divider">HV1盘</th>' +
    '    <th class="group-win-hv2">HV2主</th><th class="group-win-hv2">HV2客</th><th class="group-win-hv2">HV2盘</th>' +
    '  </table></thead>';
  table.innerHTML = theadHTML + '<tbody></tbody>';
  container.appendChild(table);
  var tbody = table.querySelector('tbody');

  var prevNg = null, prevGd = null, prevWinLines = null;

  for (var ri=0; ri<rows.length; ri++) {
    var folder = rows[ri].folder, rec = rows[ri].rec;
    var tr = document.createElement('tr');
    if (!rec) {
      tr.innerHTML = '<td class="folder-cell">'+folder+'</td><td colspan="30" class="missing">— 该时间段无此赛事 —</td>';
      tbody.appendChild(tr);
      continue;
    }
    var ng = rec.ng || {}, win = rec.win || {};
    var curNg = ngCols.map(function(k){ return ng[k]||''; });
    var htmlOut = '<td class="folder-cell">'+folder+'</td>';

    for (var ni=0; ni<ngCols.length; ni++) {
      var nval = ng[ngCols[ni]] || '<span class="missing">-</span>';
      var nchg = (prevNg && ng[ngCols[ni]] && prevNg[ni] !== ng[ngCols[ni]]) ? ' changed' : '';
      htmlOut += '<td class="ng-val'+nchg+'">'+nval+'</td>';
    }

    var hasNgData = ngCols.every(function(k){ return ng[k] && parseFloat(ng[k])>0; });
    var gdProbs = null;
    if (hasNgData) {
      var homeOdds = [ng.h1,ng.h2,ng.h3,ng.h4,ng.h5,ng.h6];
      var awayOdds = [ng.a1,ng.a2,ng.a3,ng.a4,ng.a5,ng.a6];
      var hp = normalizeOdds(homeOdds);
      var ap = normalizeOdds(awayOdds);
      gdProbs = calcGoalDiff(hp, ap);  // 升序: -4- .. +4+
    }
    var curGd = gdProbs ? gdProbs.slice() : new Array(9).fill('');
    // 逆序输出，使表格从左到右为 +4+ ... -4-
    for (var gi=0; gi<9; gi++) {
      var origIdx = 8 - gi;
      var gval = gdProbs ? (gdProbs[origIdx]*100).toFixed(1)+'%' : '<span class="missing">-</span>';
      var gchg = (prevGd && gdProbs && prevGd[origIdx]!=='' && Math.abs(prevGd[origIdx]-gdProbs[origIdx])>0.005) ? ' changed' : '';
      htmlOut += '<td class="tg-val'+gchg+'">'+gval+'</td>';
    }

    // 解析让球盘口
    var baseHandicap = null, baseHomeOdds = null, baseAwayOdds = null;
    if (win.g && win.gg && win.ho && win.ao) {
      var gDir = win.g;
      var ggVal = parseFloat(win.gg);
      var hcapRaw = (ggVal - 1) / 4;
      var handicap = (gDir === 'H') ? -hcapRaw : hcapRaw;
      baseHandicap = handicap.toFixed(2);
      baseHomeOdds = win.ho;
      baseAwayOdds = win.ao;
    }
    function parseVarGroup(str) {
      if (!str) return [];
      var parts = str.split(',');
      var groups = [];
      for (var i=0; i+4<parts.length; i+=5) {
        var dir = parts[i];
        var ggVal = parseFloat(parts[i+1]);
        var homeOdds = parts[i+2];
        var awayOdds = parts[i+3];
        var hcapRaw = (ggVal - 1) / 4;
        var handicap = (dir === 'H') ? -hcapRaw : hcapRaw;
        groups.push({ over: homeOdds, under: awayOdds, hcap: handicap.toFixed(2) });
      }
      return groups;
    }
    var varGroups = parseVarGroup(win.var || '');
    var allLines = [
      { over: baseHomeOdds||'', under: baseAwayOdds||'', hcap: baseHandicap||'' },
      varGroups[0] || {over:'',under:'',hcap:''},
      varGroups[1] || {over:'',under:'',hcap:''}
    ];
    var prevLines = prevWinLines || null;
    for (var lix=0; lix<3; lix++) {
      var line = allLines[lix];
      var pLine = prevLines ? prevLines[lix] : null;
      var ovStr = line.over, unStr = line.under, hcStr = line.hcap;
      var ovNum = parseFloat(ovStr)||0, unNum = parseFloat(unStr)||0, hcNum = parseFloat(hcStr)||0;
      var chO = (pLine && ovStr && pLine.over!==ovStr)?' changed':'';
      var chU = (pLine && unStr && pLine.under!==unStr)?' changed':'';
      var chH = (pLine && hcStr && pLine.hcap!==hcStr)?' changed':'';
      var divClass = (lix===0)?' ou-divider':'';
      if (!ovStr && !unStr && !hcStr) {
        htmlOut += '<td class="win-val"><span class="missing">-</span></td><td class="win-val"><span class="missing">-</span></td><td class="win-val'+divClass+'"><span class="missing">-</span></td>';
      } else {
        var cellO = ovStr, cellU = unStr;
        if (gdProbs && ovNum>0 && unNum>0 && !isNaN(hcNum)) {
          try {
            var res = calcAsianEVForGD(hcNum, ovNum, unNum, gdProbs);
            if (res.fairHome>0) cellO += '<span class="fp-line">公平P:'+(res.fairHome*100).toFixed(1)+'%</span>';
            if (!isNaN(res.evHome)) cellO += '<span class="ev-line '+(res.evHome>0?'ev-pos':'ev-neg')+'">EV '+(res.evHome>=0?'+':'')+res.evHome.toFixed(2)+'</span>';
            if (res.fairAway>0) cellU += '<span class="fp-line">公平P:'+(res.fairAway*100).toFixed(1)+'%</span>';
            if (!isNaN(res.evAway)) cellU += '<span class="ev-line '+(res.evAway>0?'ev-pos':'ev-neg')+'">EV '+(res.evAway>=0?'+':'')+res.evAway.toFixed(2)+'</span>';
          } catch(e) {}
        }
        htmlOut += '<td class="win-val'+chO+'">'+cellO+'</td><td class="win-val'+chU+'">'+cellU+'</td><td class="win-val'+chH+divClass+'">'+hcStr+'</td>';
      }
    }
    tr.innerHTML = htmlOut;
    tbody.appendChild(tr);
    prevNg = curNg;
    prevGd = curGd;
    prevWinLines = allLines.slice();
  }
}
</script>
</body>
</html>"""


def main():
    import time
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_template)
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    elapsed = time.time() - t0
    print("[OK] index.html: %.0f KB (%.1fs)" % (size_kb, elapsed))


if __name__ == '__main__':
    main()