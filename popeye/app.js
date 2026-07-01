/**
 * app.js - UI 逻辑（依赖 stats.js, his_data.js）
 * 只做：事件绑定、表格渲染、跨视图状态。
 * 不包含任何纯数学计算。
 */

(function () {
  'use strict';

  // ===== 立即显示 loading =====
  function injectEarlyLoading() {
    if (document.getElementById('appLoading')) return;
    const div = document.createElement('div');
    div.id = 'appLoading';
    div.style.cssText = 'position:fixed;inset:0;background:rgba(240,242,245,0.95);' +
      'display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999;' +
      'font-family:"Microsoft YaHei",sans-serif;color:#1a3c6e;';
    div.innerHTML = '<style>@keyframes _wbSpin{to{transform:rotate(360deg)}}</style>' +
      '<div style="width:50px;height:50px;border:5px solid #c0c8d0;border-top-color:#2563a8;' +
      'border-radius:50%;animation:_wbSpin 0.9s linear infinite;margin-bottom:16px"></div>' +
      '<div style="font-size:15px;font-weight:600">正在加载历史数据...</div>' +
      '<div style="font-size:12px;color:#888;margin-top:4px">数据量较大，请稍候</div>';
    (document.body || document.documentElement).appendChild(div);
  }
  if (document.body) {
    injectEarlyLoading();
  } else {
    document.addEventListener('DOMContentLoaded', injectEarlyLoading);
  }

  // ===== 全局状态 =====
  const state = {
    DATA: (typeof RAW_DATA !== 'undefined') ? RAW_DATA : {},
    FOLDERS: (typeof FOLDERS !== 'undefined') ? FOLDERS : [],
    allLeagues: {},
    leagueNames: [],
    currentIdIndex: {},
    currentRows: [],
    currentMatchId: '',
    currentView: 'analysis', // 'analysis' | 'ou' | 'win'
    precomputed: [],   // [{folder, rec, analysis}]
    // 新增
    selectedMatchId: null,
    analysisRecords: [],
    analysisViewReady: false,
  };

  // ===== DOM 引用 =====
  const $ = (id) => document.getElementById(id);
  const els = {
    leagueSelect: $('leagueSelect'),
    searchInput: $('searchInput'),
    autocomplete: $('autocomplete'),
    tableOu: $('tableOu'),
    tableWin: $('tableWin'),
    tableAnalysis: $('tableAnalysis'),
    noResultOu: $('noResultOu'),
    noResultWin: $('noResultWin'),
    noResultAnalysis: $('noResultAnalysis'),
    hintOu: $('hintOu'),
    hintWin: $('hintWin'),
    hintAnalysis: $('hintAnalysis'),
    matchInfo: $('matchInfo'),
    infoId: $('infoId'),
    infoTime: $('infoTime'),
    infoLeague: $('infoLeague'),
    infoHome: $('infoHome'),
    infoAway: $('infoAway'),
    infoCount: $('infoCount'),
    legend: $('legend'),
    statusTip: $('statusTip'),
    btnSearch: $('btnSearch'),
    btnClear: $('btnClear'),
    btnAnalysis: $('btnAnalysis'),
    btnOu: $('btnOu'),
    btnWin: $('btnWin'),
    btnOuReport: $('btnOuReport'),
    btnClearAnalysis: $('btnClearAnalysis'),
    btnCalcBingo: $('btnCalcBingo'),
    bingoPasteInput: $('bingoPasteInput'),
    loading: null,
  };

  // ===== 工具：转义 HTML 防 XSS =====
  function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // ===== 1. 启动：建联赛索引 =====
  function buildLeagueIndex() {
    const leagueSet = {};
    for (const folder of state.FOLDERS) {
      const fd = state.DATA[folder] || {};
      for (const id in fd) {
        const oc = (fd[id] && fd[id].oc) || {};
        if (!oc.st) continue;
        const ln = oc.st;
        if (!leagueSet[ln]) {
          leagueSet[ln] = {};
          state.leagueNames.push(ln);
        }
        if (!leagueSet[ln][id]) {
          leagueSet[ln][id] = {
            gt: oc.gt || '', st: oc.st || '',
            sh: oc.sh || '', sa: oc.sa || '',
          };
        }
      }
    }
    state.leagueNames.sort();
    state.allLeagues = leagueSet;
  }

  function populateLeagues() {
    const sel = els.leagueSelect;
    for (const ln of state.leagueNames) {
      const opt = document.createElement('option');
      opt.value = ln;
      opt.textContent = ln + ' (' + Object.keys(state.allLeagues[ln]).length + '场)';
      sel.appendChild(opt);
    }
  }

  function show(el) { if (el) el.hidden = false; }
  function hide(el) { if (el) el.hidden = true; }

  // ===== 2. 联赛切换 =====
  function onLeagueChange() {
    const selVal = els.leagueSelect.value;
    els.searchInput.value = '';
    els.autocomplete.hidden = true;
    els.tableOu.innerHTML = '';
    els.tableWin.innerHTML = '';
    hide(els.matchInfo);
    hide(els.noResultOu);
    hide(els.noResultWin);
    // 分析视图不清空，但搜索只影响 OU/Win
    els.statusTip.textContent = '';
    hide(els.btnOuReport);

    if (!selVal) {
      state.currentIdIndex = {};
      els.searchInput.disabled = true;
      els.searchInput.placeholder = '先选择联赛，再输入/选择赛事ID或球队名';
      return;
    }
    els.searchInput.disabled = false;
    els.searchInput.placeholder = '输入ID或球队名搜索...';
    state.currentIdIndex = state.allLeagues[selVal] || {};
    els.statusTip.textContent = '当前联赛共 ' + Object.keys(state.currentIdIndex).length + ' 场比赛';
  }

  // ===== 3. Autocomplete =====
  function updateAutocomplete() {
    const q = els.searchInput.value.trim().toLowerCase();
    const leagueSel = els.leagueSelect.value;
    if (!leagueSel || !q) { els.autocomplete.hidden = true; return; }
    const matches = [];
    for (const id in state.currentIdIndex) {
      const info = state.currentIdIndex[id];
      const text = (id + ' ' + (info.sh || '') + ' ' + (info.sa || '') + ' ' + (info.gt || '')).toLowerCase();
      if (text.indexOf(q) !== -1) matches.push(id);
      if (matches.length >= 20) break;
    }
    if (!matches.length) { els.autocomplete.hidden = true; return; }

    const frag = document.createDocumentFragment();
    for (const id of matches) {
      const info = state.currentIdIndex[id];
      const hlInfo = info.sh ? (info.sh + ' vs ' + info.sa) : '';
      const timeStr = info.gt ? info.gt.substring(4, 6) + '/' + info.gt.substring(6, 8) : '';
      const div = document.createElement('div');
      div.dataset.id = id;
      div.innerHTML = '<b>' + esc(id) + '</b> <span style="color:#888;font-size:11px">' +
        esc(hlInfo) + (timeStr ? ' [' + esc(timeStr) + ']' : '') + '</span>';
      frag.appendChild(div);
    }
    els.autocomplete.innerHTML = '';
    els.autocomplete.appendChild(frag);
    els.autocomplete.hidden = false;
  }

  els.autocomplete.addEventListener('click', (e) => {
    const div = e.target.closest('div[data-id]');
    if (!div) return;
    selectId(div.dataset.id);
  });

  function selectId(id) {
    els.searchInput.value = id;
    els.autocomplete.hidden = true;
    doSearch(id);
  }

  els.searchInput.addEventListener('input', updateAutocomplete);
  els.searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { els.autocomplete.hidden = true; doSearch(); }
    if (e.key === 'Escape') { els.autocomplete.hidden = true; }
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.autocomplete-wrapper')) els.autocomplete.hidden = true;
  });

  // ===== 4. 查询（仅用于 OU/Win） =====
function doSearch(id, skipLeagueCheck) {
  if (!state.analysisViewReady) {
    loadAnalysisData();
  }
  const matchId = id || els.searchInput.value.trim();
  if (!matchId) return;
  const leagueSel = els.leagueSelect.value;
  // 只有非跳过模式才检查联赛匹配
  if (!skipLeagueCheck && leagueSel && !state.currentIdIndex[matchId]) {
    show(els.noResultOu);
    show(els.noResultWin);
    hide(els.hintOu);
    hide(els.hintWin);
    hide(els.matchInfo);
    hide(els.legend);
    els.statusTip.textContent = '该ID不属于所选联赛，请重新选择联赛或ID';
    return;
  }
  hide(els.hintOu);
  hide(els.hintWin);
  hide(els.noResultOu);
  hide(els.noResultWin);
  els.tableOu.innerHTML = '';
  els.tableWin.innerHTML = '';
  hide(els.matchInfo);
  show(els.legend);

  state.currentMatchId = matchId;
  state.currentRows = [];
  state.precomputed = [];
  for (const folder of state.FOLDERS) {
    const fd = state.DATA[folder] || {};
    const rec = (fd && fd[matchId]) ? fd[matchId] : null;
    state.currentRows.push({ folder, rec });
    state.precomputed.push({ folder, rec, analysis: Stats.analyzeRow(rec) });
  }

  const hasAny = state.currentRows.some((r) => r.rec !== null);
  if (!hasAny) {
    show(els.noResultOu);
    show(els.noResultWin);
    els.statusTip.textContent = '';
    return;
  }

  let firstOc = null;
  for (const r of state.precomputed) {
    if (r.rec && r.rec.oc) { firstOc = r.rec.oc; break; }
  }
  if (firstOc) {
    els.infoId.textContent = firstOc.id || state.currentMatchId;
    els.infoTime.textContent = formatMatchTime(firstOc.gt);
    els.infoLeague.textContent = firstOc.st || '-';
    els.infoHome.textContent = firstOc.sh || '-';
    els.infoAway.textContent = firstOc.sa || '-';
  } else {
    els.infoId.textContent = state.currentMatchId;
    els.infoTime.textContent = '-';
    els.infoLeague.textContent = '-';
    els.infoHome.textContent = '-';
    els.infoAway.textContent = '-';
  }
  const count = state.currentRows.filter((r) => r.rec !== null).length;
  els.infoCount.textContent = count;
  show(els.matchInfo);

  els.statusTip.textContent = '共找到 ' + count + ' 个时间段的数据';

  buildOuTable();
  buildWinTable();

  if (count > 0) {
    show(els.btnOuReport);
  } else {
    hide(els.btnOuReport);
  }
}

  // ===== 5. 表格通用：计算变化列 class =====
  function cellClass(prev, cur) {
    if (prev === undefined || prev === null) return '';
    if (cur === '' || cur === null || cur === undefined) return '';
    return prev !== cur ? ' changed' : '';
  }

  function formatMatchTime(gt) {
    if (!gt) return '-';
    const m = gt.match(/^(\d{4})(\d{2})(\d{2})\s+(\d{1,2}:\d{2})/);
    if (m) return m[2] + '/' + m[3] + ' ' + m[4];
    return gt;
  }

  function pctChangeClass(prevVal, curVal, threshold = 0.005) {
    if (prevVal === undefined || prevVal === null || prevVal === '') return '';
    if (curVal === null) return '';
    if (Math.abs(prevVal - curVal) > threshold) return ' changed';
    return '';
  }

  // ===== 6. 表格构建（使用预解析的 ouGroups / winGroups）=====
  const NG_COLS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6'];
  const TG_LABELS = ['TG0', 'TG1', 'TG2', 'TG3', 'TG4', 'TG5', 'TG6', 'TG7+'];
  const GD_LABELS = ['+4+', '+3', '+2', '+1', '0', '-1', '-2', '-3', '-4-'];

function buildOuTable() {
  const container = els.tableOu;
  container.innerHTML = '';
  const table = document.createElement('table');
  table.setAttribute('aria-label', '大小球盘口历史时序数据');

  const theadParts = [];
  theadParts.push('<caption class="sr-only">大小球盘口历史时序数据（大小球赔率、泊松 λ、EV、偏差）</caption><thead>');
  theadParts.push('<tr><th rowspan="2" scope="col">时间戳</th>' +
    '<th colspan="12" class="group-ng" scope="colgroup">进球分布赔率</th>' +
    '<th colspan="8" class="group-tg" scope="colgroup">总进球概率</th>' +
    '<th rowspan="2" class="group-lam" scope="col">λ/SSE</th>' +
    '<th colspan="9" class="group-ou-base" scope="colgroup">大小球赔率 + 公平概率 + EV</th></tr>');
  theadParts.push('<tr class="subheader-row">');
  for (const k of NG_COLS) theadParts.push('<th class="group-ng" scope="col">' + k.toUpperCase() + '</th>');
  for (const lbl of TG_LABELS) theadParts.push('<th class="group-tg" scope="col">' + lbl + '</th>');
  theadParts.push('<th class="group-ou-base" scope="col">大球OO</th>' +
    '<th class="group-ou-base" scope="col">小球UO</th>' +
    '<th class="group-ou-base ou-divider" scope="col">盘口LI</th>' +
    '<th class="group-ou-hv1" scope="col">HV1大</th>' +
    '<th class="group-ou-hv1" scope="col">HV1小</th>' +
    '<th class="group-ou-hv1 ou-divider" scope="col">HV1盘</th>' +
    '<th class="group-ou-hv2" scope="col">HV2大</th>' +
    '<th class="group-ou-hv2" scope="col">HV2小</th>' +
    '<th class="group-ou-hv2" scope="col">HV2盘</th>');
  theadParts.push('</tr></thead>');
  table.innerHTML = theadParts.join('') + '<tbody></tbody>';
  container.appendChild(table);
  const tbody = table.querySelector('tbody');

  let prevNg = null, prevTg = null, prevOuLines = null;

  for (const item of state.precomputed) {
    const { folder, rec, analysis } = item;
    const tr = document.createElement('tr');
    if (!rec) {
      tr.innerHTML = '<td class="folder-cell">' + esc(folder) + '</td>' +
        '<td colspan="30" class="missing">— 该时间段无此赛事 —</td>';
      tbody.appendChild(tr);
      continue;
    }

    const matchGt = rec.oc && rec.oc.gt ? rec.oc.gt : null;
    const timeStatus = Stats.getTimeStatus(folder, matchGt);
    const timeClass = timeStatus === 'before' ? 'time-before' :
                      timeStatus === 'after' ? 'time-after' : '';
    const ng = rec.ng || {};
    const ou = rec.ou || {};

    const curNg = NG_COLS.map((k) => ng[k] || '');
    const parts = ['<td class="folder-cell ' + timeClass + '">' + esc(folder) + '</td>'];

    // NG 列
    for (let ni = 0; ni < NG_COLS.length; ni++) {
      const nval = ng[NG_COLS[ni]] || '<span class="missing">-</span>';
      const nchg = cellClass(prevNg && prevNg[ni], ng[NG_COLS[ni]]);
      parts.push('<td class="ng-val' + nchg + '">' + nval + '</td>');
    }

    // 总进球概率：上行 = ngTgProbs（泊松模型，同 full_team_calculator），下行 = ouTg（泊松），比较大小
    const tgProbs = analysis.ngTgProbs;  // 泊松模型总进球（来自 ng λ）
    const poissonTgProbs = analysis.ouTg;
    const curTg = tgProbs ? tgProbs.slice() : new Array(8).fill('');

    for (let tgi = 0; tgi < 8; tgi++) {
      const topVal = tgProbs ? tgProbs[tgi] : -1;
      const botVal = poissonTgProbs ? poissonTgProbs[tgi] : -1;
      const topColor = (topVal >= 0 && botVal >= 0)
        ? (topVal >= botVal ? '#dc2626' : '#111') : '#000';
      const botColor = (topVal >= 0 && botVal >= 0)
        ? (botVal >= topVal ? '#dc2626' : '#111') : '#000';

      const topStr = (topVal >= 0) ? (topVal * 100).toFixed(1) + '%' : '<span class="missing">-</span>';
      const botStr = (botVal >= 0) ? (botVal * 100).toFixed(1) + '%' : '<span class="missing">-</span>';

      const tchg = pctChangeClass(prevTg && prevTg[tgi], tgProbs ? tgProbs[tgi] : null);
      parts.push('<td class="tg-val' + tchg + '" style="line-height:1.7;vertical-align:middle">' +
        '<span style="font-weight:700;color:' + topColor + '">' + topStr + '</span>' +
        '<br><span style="font-weight:700;color:' + botColor + ';font-size:11px;">' + botStr + '</span></td>');
    }

    // λ / SSE（上下两行：上面 λ总=ng总，下面 λ=ou优化）
    let lamCell = '<span class="missing">-</span><br><span class="missing">-</span>';
    const ngTotal = analysis.ngLamTotal;
    const ouLamVal = analysis.ouLam;
     let topLam = '<span class="missing">-</span>';
     let botLam = '<span class="missing">-</span>';
     if (ngTotal !== null) {
      topLam = '<span style="font-weight:700;font-size:13px;color:#b91c1c;">λ总 ' + ngTotal.toFixed(3) + '</span>';
     } else {
      topLam = '<span class="missing">-</span>';
     }
     if (ouLamVal !== null) {
      botLam = '<span style="font-weight:700;font-size:11px;color:#1a3c6e;">λ ' +       ouLamVal.toFixed(3) + '</span>';
     } else {
      botLam = '<span class="missing">-</span>';
     }
     lamCell = topLam + '<br>' + botLam;
     parts.push('<td class="ou-val" style="line-height:1.7;text-align:center;">' + lamCell + '</td>');

    // 盘口行（大小球）
    const hivGroups = analysis.ouGroups;
    const allLines = [
      { over: ou.oo || '', under: ou.uo || '', hcap: ou.li ? (parseFloat(ou.li) / 4).toFixed(2) : '' },
      hivGroups[0] || { over: '', under: '', hcap: '' },
      hivGroups[1] || { over: '', under: '', hcap: '' },
    ];
    const prevLines = prevOuLines;
    for (let lix = 0; lix < 3; lix++) {
      const line = allLines[lix];
      const pLine = prevLines ? prevLines[lix] : null;
      const ovStr = line.over, unStr = line.under, hcStr = line.hcap;
      const ovNum = parseFloat(ovStr) || 0, unNum = parseFloat(unStr) || 0, hcNum = parseFloat(hcStr) || 0;
      const chO = (pLine && ovStr && pLine.over !== ovStr) ? ' changed' : '';
      const chU = (pLine && unStr && pLine.under !== unStr) ? ' changed' : '';
      const chH = (pLine && hcStr && pLine.hcap !== hcStr) ? ' changed' : '';
      const divClass = (lix === 0) ? ' ou-divider' : '';
      if (!ovStr && !unStr && !hcStr) {
        parts.push('<td class="ou-val"><span class="missing">-</span></td>' +
          '<td class="ou-val"><span class="missing">-</span></td>' +
          '<td class="ou-val' + divClass + '"><span class="missing">-</span></td>');
      } else {
        let cellO = ovStr, cellU = unStr;
        // EV 计算使用泊松总进球（ouTg）
        const probForEV = poissonTgProbs || tgProbs;
        if (probForEV && ovNum > 0 && unNum > 0 && !isNaN(hcNum)) {
          try {
            const res = Stats.calcAsianEV(hcNum, ovNum, unNum, probForEV);
            if (res.fairOver > 0) {
              cellO += '<span class="fp-line">公平P:' + (res.fairOver * 100).toFixed(1) + '%</span>';
            }
            if (!isNaN(res.evOver)) {
              cellO += '<span class="ev-line ' + (res.evOver > 0 ? 'ev-pos' : 'ev-neg') + '">EV ' +
                (res.evOver >= 0 ? '+' : '') + res.evOver.toFixed(2) + '</span>';
            }
            if (analysis.ouDevs[hcStr] && analysis.ouDevs[hcStr].over !== undefined) {
              const dev = analysis.ouDevs[hcStr].over;
              cellO += '<span class="dev-line ' + (dev >= 0 ? 'dev-pos' : 'dev-neg') + '">' +
                (dev >= 0 ? '+' : '') + dev.toFixed(2) + '%</span>';
            }
            if (res.fairUnder > 0) {
              cellU += '<span class="fp-line">公平P:' + (res.fairUnder * 100).toFixed(1) + '%</span>';
            }
            if (!isNaN(res.evUnder)) {
              cellU += '<span class="ev-line ' + (res.evUnder > 0 ? 'ev-pos' : 'ev-neg') + '">EV ' +
                (res.evUnder >= 0 ? '+' : '') + res.evUnder.toFixed(2) + '</span>';
            }
            if (analysis.ouDevs[hcStr] && analysis.ouDevs[hcStr].under !== undefined) {
              const dev = analysis.ouDevs[hcStr].under;
              cellU += '<span class="dev-line ' + (dev >= 0 ? 'dev-pos' : 'dev-neg') + '">' +
                (dev >= 0 ? '+' : '') + dev.toFixed(2) + '%</span>';
            }
          } catch (e) { /* ignore */ }
        }
        parts.push('<td class="ou-val' + chO + '">' + cellO + '</td>' +
          '<td class="ou-val' + chU + '">' + cellU + '</td>' +
          '<td class="ou-val' + chH + divClass + '">' + esc(hcStr) + '</td>');
      }
    }
    tr.innerHTML = parts.join('');
    tbody.appendChild(tr);
    prevNg = curNg;
    prevTg = curTg;
    prevOuLines = allLines.slice();
  }
}

function buildWinTable() {
  const container = els.tableWin;
  container.innerHTML = '';
  const table = document.createElement('table');
  table.setAttribute('aria-label', '让球盘口历史时序数据');

  const theadParts = [];
  theadParts.push('<caption class="sr-only">让球盘口历史时序数据（让球赔率、双变量泊松 λ₁/λ₂、EV、偏差）</caption><thead>');
  theadParts.push('<tr><th rowspan="2" scope="col">时间戳</th>' +
    '<th colspan="12" class="group-ng" scope="colgroup">进球分布赔率</th>' +
    '<th colspan="9" class="group-tg" scope="colgroup">净胜球概率</th>' +
    '<th rowspan="2" class="group-lam" scope="col">λ₁/λ₂<br>SSE</th>' +
    '<th colspan="9" class="group-win-base" scope="colgroup">让球赔率 + 公平概率 + EV</th></tr>');
  theadParts.push('<tr class="subheader-row">');
  for (const k of NG_COLS) theadParts.push('<th class="group-ng" scope="col">' + k.toUpperCase() + '</th>');
  for (const lbl of GD_LABELS) theadParts.push('<th class="group-tg" scope="col">' + lbl + '</th>');
  theadParts.push('<th class="group-win-base" scope="col">主队</th>' +
    '<th class="group-win-base" scope="col">客队</th>' +
    '<th class="group-win-base ou-divider" scope="col">盘口</th>' +
    '<th class="group-win-hv1" scope="col">HV1主</th>' +
    '<th class="group-win-hv1" scope="col">HV1客</th>' +
    '<th class="group-win-hv1 ou-divider" scope="col">HV1盘</th>' +
    '<th class="group-win-hv2" scope="col">HV2主</th>' +
    '<th class="group-win-hv2" scope="col">HV2客</th>' +
    '<th class="group-win-hv2" scope="col">HV2盘</th>');
  theadParts.push('</tr></thead>');
  table.innerHTML = theadParts.join('') + '<tbody></tbody>';
  container.appendChild(table);
  const tbody = table.querySelector('tbody');

  let prevNg = null, prevGd = null, prevWinLines = null;

  for (const item of state.precomputed) {
    const { folder, rec, analysis } = item;
    const tr = document.createElement('tr');
    if (!rec) {
      tr.innerHTML = '<td class="folder-cell">' + esc(folder) + '</td>' +
        '<td colspan="31" class="missing">— 该时间段无此赛事 —</td>';
      tbody.appendChild(tr);
      continue;
    }

    const matchGt = rec.oc && rec.oc.gt ? rec.oc.gt : null;
    const timeStatus = Stats.getTimeStatus(folder, matchGt);
    const timeClass = timeStatus === 'before' ? 'time-before' :
                      timeStatus === 'after' ? 'time-after' : '';
    const ng = rec.ng || {};
    const win = rec.win || {};

    const curNg = NG_COLS.map((k) => ng[k] || '');
    const parts = ['<td class="folder-cell ' + timeClass + '">' + esc(folder) + '</td>'];

    // NG 列
    for (let ni = 0; ni < NG_COLS.length; ni++) {
      const nval = ng[NG_COLS[ni]] || '<span class="missing">-</span>';
      const nchg = cellClass(prevNg && prevNg[ni], ng[NG_COLS[ni]]);
      parts.push('<td class="ng-val' + nchg + '">' + nval + '</td>');
    }

    // 净胜球概率：上行 = ngGdProbs（泊松模型，同 full_team_calculator），下行 = winGd（泊松），比较大小
    const gdProbs = analysis.ngGdProbs;  // 泊松模型净胜球（来自 ng λ）
    const winGd = analysis.winGd;
    const curGd = gdProbs ? gdProbs.slice() : new Array(9).fill('');

    for (let gi = 0; gi < 9; gi++) {
      const origIdx = 8 - gi; // 显示顺序 +4+ 到 -4-
      const topVal = gdProbs ? gdProbs[origIdx] : -1;
      const botVal = winGd ? winGd[origIdx] : -1;
      const topColor = (topVal >= 0 && botVal >= 0)
        ? (topVal >= botVal ? '#dc2626' : '#111') : '#000';
      const botColor = (topVal >= 0 && botVal >= 0)
        ? (botVal >= topVal ? '#dc2626' : '#111') : '#000';

      const topStr = (topVal >= 0) ? (topVal * 100).toFixed(1) + '%' : '<span class="missing">-</span>';
      const botStr = (botVal >= 0) ? (botVal * 100).toFixed(1) + '%' : '<span class="missing">-</span>';

      const gchg = pctChangeClass(prevGd && prevGd[origIdx], gdProbs ? gdProbs[origIdx] : null);
      parts.push('<td class="tg-val' + gchg + '" style="line-height:1.7;vertical-align:middle">' +
        '<span style="font-weight:700;color:' + topColor + '">' + topStr + '</span>' +
        '<br><span style="font-weight:700;color:' + botColor + ';font-size:11px;">' + botStr + '</span></td>');
    }

    // λ总 / λ₁/λ₂（上下两行：上面 λ总=ng总，下面 λH/λA=win优化）
    let winLamCell = '<span class="missing">-</span><br><span class="missing">-</span>';
    const ngTotal = analysis.ngLamTotal;
    const winLamH = analysis.winLamH;
    const winLamA = analysis.winLamA;
    let wTop = '<span class="missing">-</span>';
    let wBot = '<span class="missing">-</span>';
    if (ngTotal !== null) {
      wTop = '<span style="font-weight:700;font-size:13px;color:#b91c1c;">λ总 ' + ngTotal.toFixed(3) + '</span>';
    } else {
      wTop = '<span class="missing">-</span>';
    }
    if (winLamH !== null && winLamA !== null) {
      wBot = '<span style="font-weight:700;font-size:11px;color:#00695c;">λ ' + winLamH.toFixed(3) + '/' + winLamA.toFixed(3) + '</span>' +
        '<br><span style="font-size:10px;color:#555;">' + Stats.formatSSE(analysis.winSse) + '</span>';
    } else {
      wBot = '<span class="missing">-</span>';
    }
    winLamCell = wTop + '<br>' + wBot;
    parts.push('<td class="win-val" style="line-height:1.7">' + winLamCell + '</td>');

    // 盘口行（让球）
    const varGroups = analysis.winGroups;
    let baseHandicap = '', baseHomeOdds = '', baseAwayOdds = '';
    if (win.g && win.gg && win.ho && win.ao) {
      const ggVal = parseFloat(win.gg);
      const hcapRaw = (ggVal - 1) / 4;
      const handicap = (win.g === 'H') ? -hcapRaw : hcapRaw;
      baseHandicap = handicap.toFixed(2);
      baseHomeOdds = win.ho;
      baseAwayOdds = win.ao;
    }
    const allLines = [
      { over: baseHomeOdds, under: baseAwayOdds, hcap: baseHandicap },
      varGroups[0] || { over: '', under: '', hcap: '' },
      varGroups[1] || { over: '', under: '', hcap: '' },
    ];
    const prevLines = prevWinLines;
    for (let lix = 0; lix < 3; lix++) {
      const line = allLines[lix];
      const pLine = prevLines ? prevLines[lix] : null;
      const ovStr = line.over, unStr = line.under, hcStr = line.hcap;
      const ovNum = parseFloat(ovStr) || 0, unNum = parseFloat(unStr) || 0, hcNum = parseFloat(hcStr) || 0;
      const chO = (pLine && ovStr && pLine.over !== ovStr) ? ' changed' : '';
      const chU = (pLine && unStr && pLine.under !== unStr) ? ' changed' : '';
      const chH = (pLine && hcStr && pLine.hcap !== hcStr) ? ' changed' : '';
      const divClass = (lix === 0) ? ' ou-divider' : '';
      if (!ovStr && !unStr && !hcStr) {
        parts.push('<td class="win-val"><span class="missing">-</span></td>' +
          '<td class="win-val"><span class="missing">-</span></td>' +
          '<td class="win-val' + divClass + '"><span class="missing">-</span></td>');
      } else {
        let cellO = ovStr, cellU = unStr;
        // EV 计算使用泊松净胜球（winGd）
        const probForEV = winGd || gdProbs;
        if (probForEV && ovNum > 0 && unNum > 0 && !isNaN(hcNum)) {
          try {
            const res = Stats.calcAsianEVForGD(hcNum, ovNum, unNum, probForEV);
            if (res.fairHome > 0) {
              cellO += '<span class="fp-line">公平P:' + (res.fairHome * 100).toFixed(1) + '%</span>';
            }
            if (!isNaN(res.evHome)) {
              cellO += '<span class="ev-line ' + (res.evHome > 0 ? 'ev-pos' : 'ev-neg') + '">EV ' +
                (res.evHome >= 0 ? '+' : '') + res.evHome.toFixed(2) + '</span>';
            }
            if (analysis.winDevs[hcStr] && analysis.winDevs[hcStr].home !== undefined) {
              const dev = analysis.winDevs[hcStr].home;
              cellO += '<span class="dev-line ' + (dev >= 0 ? 'dev-pos' : 'dev-neg') + '">' +
                (dev >= 0 ? '+' : '') + dev.toFixed(2) + '%</span>';
            }
            if (res.fairAway > 0) {
              cellU += '<span class="fp-line">公平P:' + (res.fairAway * 100).toFixed(1) + '%</span>';
            }
            if (!isNaN(res.evAway)) {
              cellU += '<span class="ev-line ' + (res.evAway > 0 ? 'ev-pos' : 'ev-neg') + '">EV ' +
                (res.evAway >= 0 ? '+' : '') + res.evAway.toFixed(2) + '</span>';
            }
            if (analysis.winDevs[hcStr] && analysis.winDevs[hcStr].away !== undefined) {
              const dev = analysis.winDevs[hcStr].away;
              cellU += '<span class="dev-line ' + (dev >= 0 ? 'dev-pos' : 'dev-neg') + '">' +
                (dev >= 0 ? '+' : '') + dev.toFixed(2) + '%</span>';
            }
          } catch (e) { /* ignore */ }
        }
        parts.push('<td class="win-val' + chO + '">' + cellO + '</td>' +
          '<td class="win-val' + chU + '">' + cellU + '</td>' +
          '<td class="win-val' + chH + divClass + '">' + esc(hcStr) + '</td>');
      }
    }
    tr.innerHTML = parts.join('');
    tbody.appendChild(tr);
    prevNg = curNg;
    prevGd = curGd;
    prevWinLines = allLines.slice();
  }
}

  // ===== 7. 清除 / 视图切换 =====
  function doClear() {
    els.searchInput.value = '';
    els.tableOu.innerHTML = '';
    els.tableWin.innerHTML = '';
    hide(els.matchInfo);
    hide(els.noResultOu);
    hide(els.noResultWin);
    // 分析视图保留
    els.statusTip.textContent = '';
    hide(els.btnOuReport);
    if (els.leagueSelect) {
      els.leagueSelect.value = '';
      onLeagueChange();
    }
  }

function switchView(view) {
  state.currentView = view;
  // 更新按钮状态
  els.btnAnalysis.classList.toggle('active', view === 'analysis');
  els.btnOu.classList.toggle('active', view === 'ou');
  els.btnWin.classList.toggle('active', view === 'win');
  els.btnAnalysis.setAttribute('aria-selected', view === 'analysis' ? 'true' : 'false');
  els.btnOu.setAttribute('aria-selected', view === 'ou' ? 'true' : 'false');
  els.btnWin.setAttribute('aria-selected', view === 'win' ? 'true' : 'false');

  // 显示对应视图容器（使用 class 控制）
  document.getElementById('viewAnalysis').classList.toggle('active', view === 'analysis');
  document.getElementById('viewOu').classList.toggle('active', view === 'ou');
  document.getElementById('viewWin').classList.toggle('active', view === 'win');

  if (view === 'analysis') {
    if (!state.analysisViewReady) loadAnalysisData();
    renderAnalysis();
  } else if (view === 'ou' || view === 'win') {
    if (state.selectedMatchId) {
      // 从分析记录选中，跳过联赛检查
      doSearch(state.selectedMatchId, true);
      const hint = view === 'ou' ? els.hintOu : els.hintWin;
      hint.hidden = true;
      const noResult = view === 'ou' ? els.noResultOu : els.noResultWin;
      noResult.hidden = true;
    } else {
      const hint = view === 'ou' ? els.hintOu : els.hintWin;
      hint.hidden = false;
      const table = view === 'ou' ? els.tableOu : els.tableWin;
      table.innerHTML = '';
      const noResult = view === 'ou' ? els.noResultOu : els.noResultWin;
      noResult.hidden = true;
      hide(els.matchInfo);
      hide(els.legend);
    }
  }
}

  // ===== 8. OU 报告 =====
  function generateOuReport() {
    if (!state.precomputed.length) {
      alert('暂无数据，请先查询一个比赛ID');
      return;
    }
    const results = [];
    for (const item of state.precomputed) {
      const { folder, rec } = item;
      if (!rec) continue;
      const matchGt = rec.oc && rec.oc.gt ? rec.oc.gt : null;
      const isAfter = Stats.getTimeStatus(folder, matchGt) === 'after';
      const ou = rec.ou || {};
      const ng = rec.ng || {};
      const ooVal = parseFloat(ou.oo), uoVal = parseFloat(ou.uo), liVal = parseFloat(ou.li);
      if (isNaN(ooVal) || isNaN(uoVal) || isNaN(liVal) || ooVal <= 0 || uoVal <= 0) continue;
      const hasNg = NG_COLS.every((k) => ng[k] && parseFloat(ng[k]) > 0);
      if (!hasNg) continue;
      const homeOdds = NG_COLS.slice(0, 6).map((k) => ng[k]);
      const awayOdds = NG_COLS.slice(6, 12).map((k) => ng[k]);
      const hp = Stats.normalizeOdds(homeOdds);
      const ap = Stats.normalizeOdds(awayOdds);
      // 使用优化泊松总进球
      const resH = Stats.optimizeLambdaSingle(homeOdds);
      const resA = Stats.optimizeLambdaSingle(awayOdds);
      const homeProbs = Stats.modelProbs(resH.lam);
      const awayProbs = Stats.modelProbs(resA.lam);
      const wdl = Stats.calcTotalGoalsAndWdl(homeProbs, awayProbs);
      const tgProbs = wdl.totalProbs.concat(wdl.prob7plus); // 8个
      const handicap = liVal / 4;
      const displayHandicap = handicap.toFixed(2);
      let res;
      try {
        res = Stats.calcAsianEV(handicap, ooVal, uoVal, tgProbs);
        if (!res || isNaN(res.fairOver) || isNaN(res.fairUnder)) continue;
      } catch (e) { continue; }
      const overFairP = res.fairOver, underFairP = res.fairUnder;
      const overEV = res.evOver, underEV = res.evUnder;
      const pickOver = overFairP >= underFairP;
      const pickEV = pickOver ? overEV : underEV;
      const warning = pickEV >= 0 ? 'reversed' : (pickEV > -0.020 ? 'deviated' : '');
      const conclusion = pickOver ? '大球' : '小球';
      const concClass = pickOver ? 'over' : 'under';
      const threshold = pickOver ? ('>=' + displayHandicap) : ('<=' + displayHandicap);
      const bestFairP = pickOver ? overFairP : underFairP;
      results.push({
        folder, handicap: displayHandicap,
        fairP: (bestFairP * 100).toFixed(1),
        ev: pickEV, conclusion, concClass, threshold, warning,
      });
      if (isAfter) break;
    }
    if (!results.length) {
      alert('没有可分析的有效盘口数据（第一个盘口）');
      return;
    }
    sendOuReportToFootball(results);
  }

  function sendOuReportToFootball(results) {
    try {
      const payload = {
        type: 'OU_REPORT',
        matchId: state.currentMatchId,
        results: results.map((r) => ({
          folder: r.folder, handicap: r.handicap, fairP: r.fairP,
          ev: r.ev, conclusion: r.conclusion, concClass: r.concClass,
          threshold: r.threshold, warning: r.warning,
        })),
      };
      if (window.opener && !window.opener.closed) {
        window.opener.postMessage(payload, '*');
      } else {
        window.postMessage(payload, '*');
      }
    } catch (e) { /* ignore */ }
  }

  // ===== 9. 跨窗口接收 =====
  window.addEventListener('message', (e) => {
    if (location.origin && e.origin && e.origin !== 'null' && e.origin !== location.origin) return;
    if (!e.data || e.data.type !== 'FAIRPLAY_FILL') return;
    const league = e.data.league || '';
    const matchId = e.data.matchId || '';
    if (league && els.leagueSelect) {
      for (const opt of els.leagueSelect.options) {
        if (opt.value === league) {
          els.leagueSelect.value = league;
          onLeagueChange();
          break;
        }
      }
    }
    setTimeout(() => {
      if (matchId) {
        els.searchInput.disabled = false;
        els.searchInput.value = matchId;
      }
      // 切换到 OU 或 Win 视图（由调用方决定，我们默认切换到 OU）
      switchView('ou');
      doSearch(matchId);
    }, 200);
  });

  // ===== 10. Loading 隐藏 =====
  function ensureLoading() {
    if (els.loading) return els.loading;
    els.loading = document.getElementById('appLoading');
    return els.loading;
  }
  function hideLoading() {
    const el = els.loading || document.getElementById('appLoading');
    if (el && el.parentNode) el.parentNode.removeChild(el);
    els.loading = null;
  }

  // ===== 11. 分析记录相关函数 =====
function getBeijingTime() {
  return new Date(); // 系统时区为北京时间则直接使用
}

  function parseGtToDate(gt) {
    if (!gt) return null;
    gt = gt.trim();
    // 格式1: "20260628 10:00"
    if (gt.includes(' ') && gt.includes(':')) {
      const parts = gt.split(' ');
      const datePart = parts[0];
      const timePart = parts[1];
      const y = parseInt(datePart.slice(0,4), 10);
      const m = parseInt(datePart.slice(4,6), 10) - 1;
      const d = parseInt(datePart.slice(6,8), 10);
      const t = timePart.split(':');
      const h = parseInt(t[0], 10);
      const mi = parseInt(t[1], 10);
      return new Date(y, m, d, h, mi);
    }
    // 格式2: 纯数字14位
    if (gt.length === 14 && /^\d+$/.test(gt)) {
      const y = parseInt(gt.slice(0,4), 10);
      const m = parseInt(gt.slice(4,6), 10) - 1;
      const d = parseInt(gt.slice(6,8), 10);
      const h = parseInt(gt.slice(8,10), 10);
      const mi = parseInt(gt.slice(10,12), 10);
      const s = parseInt(gt.slice(12,14), 10);
      return new Date(y, m, d, h, mi, s);
    }
    return null;
  }

function loadAnalysisData() {
  if (state.analysisViewReady) return;
  const latestFolder = state.FOLDERS[state.FOLDERS.length - 1];
  const folderData = state.DATA[latestFolder] || {};
  const now = getBeijingTime();
  const pastCutoff = new Date(now.getTime() - 24 * 3600 * 1000);
  const futureCutoff = new Date(now.getTime() + 24 * 3600 * 1000);

  const records = [];
  for (const id in folderData) {
    const rec = folderData[id];
    const ng = rec.ng || {};
    const ngKeys = ['h1','h2','h3','h4','h5','h6','a1','a2','a3','a4','a5','a6'];
    const hasNg = ngKeys.some(k => parseFloat(ng[k]) > 0);
    if (!hasNg) continue;
    const oc = rec.oc || {};
    const gt = oc.gt || '';
    const matchDate = parseGtToDate(gt);
    if (!matchDate) continue;
    if (matchDate < pastCutoff || matchDate > futureCutoff) continue;

    const homeOdds = [ng.h1, ng.h2, ng.h3, ng.h4, ng.h5, ng.h6].map(v => parseFloat(v) || 0);
    const awayOdds = [ng.a1, ng.a2, ng.a3, ng.a4, ng.a5, ng.a6].map(v => parseFloat(v) || 0);
    if (homeOdds.some(o => o <= 0) || awayOdds.some(o => o <= 0)) continue;

    const hp = Stats.normalizeOdds(homeOdds);
    const ap = Stats.normalizeOdds(awayOdds);
    const resH = Stats.optimizeLambdaSingle(homeOdds);
    const resA = Stats.optimizeLambdaSingle(awayOdds);
    const homeProbs = Stats.modelProbs(resH.lam);
    const awayProbs = Stats.modelProbs(resA.lam);
    const wdl = Stats.calcTotalGoalsAndWdl(homeProbs, awayProbs);

    const wdw = rec.wdw || {};
    const ho = parseFloat(wdw.ho) || 0;
    const do_ = parseFloat(wdw.do) || 0;
    const ao = parseFloat(wdw.ao) || 0;
    const expHome = wdl.homeWin * ho;
    const expDraw = wdl.draw * do_;
    const expAway = wdl.awayWin * ao;
    const avgPayout = (ho > 0 && do_ > 0 && ao > 0) ? 1 / (1/ho + 1/do_ + 1/ao) : 0;

    records.push({
      id,
      gt: gt,
      league: oc.st || '',
      home: oc.sh || '',
      away: oc.sa || '',
      homeWinProb: wdl.homeWin,
      drawProb: wdl.draw,
      awayWinProb: wdl.awayWin,
      homeGoal: resH.lam,
      awayGoal: resA.lam,
      expHomePayout: expHome,
      expDrawPayout: expDraw,
      expAwayPayout: expAway,
      avgPayout: avgPayout,
      recordTime: now.toLocaleString('zh-CN', { hour12: false }),
    });
  }
  // ... 循环记录后
  // 按开赛时间升序（最早在前）
  records.sort((a, b) => a.gt.localeCompare(b.gt));
  state.analysisRecords = records;
  state.analysisViewReady = true;
}

function renderAnalysis() {
  const container = els.tableAnalysis;
  const hint = els.hintAnalysis;
  const noResult = els.noResultAnalysis;
  if (!state.analysisRecords.length) {
    hint.hidden = true;
    noResult.hidden = false;
    container.innerHTML = '';
    return;
  }
  noResult.hidden = true;
  hint.hidden = true;

  // 只保留 6 列: 选择 + 时间/ID/赛事/主队/客队
  const cols = ['时间','ID','赛事','主队','客队'];
  const fieldMap = {
    '时间': 'gt', 'ID': 'id', '赛事': 'league', '主队': 'home', '客队': 'away',
  };
  const format = {
    '时间': v => v, 'ID': v => v, '赛事': v => v, '主队': v => v, '客队': v => v,
  };

  let html = '<table><thead><tr>';
  html += '<th class="row-select-col">选择</th>';
  cols.forEach(c => html += `<th class="analysis-th">${c}</th>`);
  html += '</tr></thead><tbody>';
  state.analysisRecords.forEach((rec, idx) => {
    const selected = (state.selectedMatchId === rec.id) ? ' checked' : '';
    html += `<tr data-id="${rec.id}" class="${selected ? 'selected-row' : ''}">`;
    html += `<td class="row-select-col"><input type="radio" name="analysisSelect" value="${idx}"${selected} /></td>`;
    cols.forEach(c => {
      const key = fieldMap[c];
      let val = rec[key];
      if (format[c]) val = format[c](val);
      html += `<td>${val}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  container.innerHTML = html;

  // 事件绑定（保持不变）
  container.querySelectorAll('tbody tr').forEach(tr => {
    tr.addEventListener('click', function(e) {
      if (e.target.tagName === 'INPUT') return;
      const radio = this.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      const id = this.dataset.id;
      if (id) selectAnalysisMatch(id);
    });
    const radio = tr.querySelector('input[type="radio"]');
    if (radio) {
      radio.addEventListener('change', function() {
        if (this.checked) {
          const id = this.closest('tr').dataset.id;
          selectAnalysisMatch(id);
        }
      });
    }
  });
}

  function selectAnalysisMatch(id) {
    state.selectedMatchId = id;
    renderAnalysis();
    // 更新右窗格头部信息
    const rec = state.analysisRecords.find(r => r.id === id);
    const hHome = document.getElementById('headerTeamHome');
    const hAway = document.getElementById('headerTeamAway');
    const hId = document.getElementById('headerMatchId');
    if (rec && hHome && hAway && hId) {
      hHome.textContent = rec.home || '-';
      hAway.textContent = rec.away || '-';
      hId.textContent = '#' + (rec.id || '');
    }
    // 如果当前在 OU/Win 视图，刷新内容
    if (state.currentView === 'ou' || state.currentView === 'win') {
      doSearch(id);
    }
  }

  // ===== 获取最后一条OU记录（供bingo集成使用）=====
  function getLastOuRecord() {
    const validItems = state.precomputed.filter(item => item.rec !== null);
    if (!validItems.length) return null;
    const last = validItems[validItems.length - 1];
    const analysis = last.analysis || {};
    const ou = last.rec.ou || {};
    // 使用 ngTgProbs（上面一行，从进球分布NG拟合）优先，ouTg（下面一行，从大小球OU优化）作为后备
    const probs = analysis.ngTgProbs || analysis.ouTg;
    if (!probs) return null;
    const overOdds = parseFloat(ou.oo);
    const underOdds = parseFloat(ou.uo);
    const li = parseFloat(ou.li);
    if (isNaN(overOdds) || isNaN(underOdds) || isNaN(li)) return null;
    const handicap = li / 4;
    return { probs, overOdds, underOdds, handicap, folder: last.folder };
  }

  // 暴露给外部 bingo 脚本
  window.getLastOuRecord = getLastOuRecord;
  window.__appState = state;

  // ===== 12. 初始化 =====
  function init() {
    buildLeagueIndex();
    populateLeagues();
    els.leagueSelect.addEventListener('change', onLeagueChange);
    els.btnSearch.addEventListener('click', () => doSearch());
    els.btnClear.addEventListener('click', doClear);
    els.btnAnalysis.addEventListener('click', () => switchView('analysis'));
    els.btnOu.addEventListener('click', () => switchView('ou'));
    els.btnWin.addEventListener('click', () => switchView('win'));
    if (els.btnOuReport) els.btnOuReport.addEventListener('click', generateOuReport);
    if (els.btnClearAnalysis) els.btnClearAnalysis.addEventListener('click', () => {
      if (window.clearBingoAnalysis) window.clearBingoAnalysis();
    });
    if (els.btnCalcBingo) els.btnCalcBingo.addEventListener('click', () => {
      if (window.runBingoAnalysis) {
        const pasteVal = els.bingoPasteInput ? els.bingoPasteInput.value : '';
        const lastRecord = getLastOuRecord();
        window.runBingoAnalysis(pasteVal, lastRecord);
      }
    });

    // 默认切换到分析视图
    switchView('analysis');

    // 暴露一些函数供调试
    window.doSearch = doSearch;
    window.doClear = doClear;
    window.switchView = switchView;
    window.onLeagueChange = onLeagueChange;
    window.generateOuReport = generateOuReport;
    window.selectId = selectId;
    window.selectAnalysisMatch = selectAnalysisMatch;
    hideLoading();
  }

  function bootstrap() {
    ensureLoading();
    init();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
