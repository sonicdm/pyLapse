/* pyLapse web UI — shared JavaScript */

/* ===================================================================
 * Folder picker modal (reusable)
 * =================================================================== */
var _folderTarget = null;
var _folderParent = '';
var _canGoUp = false;

function folderGoUp() {
  if (_canGoUp) loadFolderList(_folderParent);
}

function openFolderModal(targetInputId, startPath) {
  _folderTarget = targetInputId;
  var el = document.getElementById(targetInputId);
  var path = startPath || (el ? el.value : '') || '';
  document.getElementById('folder-modal').style.display = 'flex';
  loadFolderList(path);
}

function closeFolderModal() {
  document.getElementById('folder-modal').style.display = 'none';
}

function selectCurrentFolder() {
  var cur = document.getElementById('folder-current').dataset.path;
  if (_folderTarget && cur) {
    document.getElementById(_folderTarget).value = cur;
  }
  closeFolderModal();
}

async function loadFolderList(path) {
  var url = '/api/browse-dir?path=' + encodeURIComponent(path) + '&target=' + encodeURIComponent(_folderTarget || '');
  var resp = await fetch(url);
  var data = await resp.json();

  var curEl = document.getElementById('folder-current');
  curEl.textContent = data.current || '(drives)';
  curEl.dataset.path = data.current || '';

  _folderParent = data.parent || '';
  _canGoUp = !!data.current;
  var upBtn = document.getElementById('folder-up-btn');
  upBtn.style.display = _canGoUp ? '' : 'none';

  var listEl = document.getElementById('folder-list');
  listEl.innerHTML = '';

  for (var i = 0; i < (data.dirs || []).length; i++) {
    var d = data.dirs[i];
    var item = document.createElement('div');
    item.className = 'folder-item';
    item.dataset.path = d.path;
    item.textContent = '\uD83D\uDCC1 ' + d.name;
    listEl.appendChild(item);
  }

  if (!data.dirs || data.dirs.length === 0) {
    listEl.innerHTML = '<p class="muted" style="padding:0.5rem;">No subdirectories</p>';
  }
}

/* Event delegation for folder items */
document.addEventListener('DOMContentLoaded', function() {
  var folderList = document.getElementById('folder-list');
  if (folderList) {
    folderList.addEventListener('click', function(e) {
      var item = e.target.closest('.folder-item');
      if (item && item.dataset.path) loadFolderList(item.dataset.path);
    });
  }
});


/* ===================================================================
 * Schedule picker (reusable component)
 * Used by camera edit, export edit, etc.
 * =================================================================== */
function formatHour(h) {
  if (h === 0) return '12 AM';
  if (h < 12) return h + ' AM';
  if (h === 12) return '12 PM';
  return (h - 12) + ' PM';
}

/* Build cron hour/minute/second from the schedule builder inputs */
function schedUpdate(el) {
  var row = el.closest('.schedule-row');
  var amount = parseFloat(row.querySelector('.sched-amount').value) || 1;
  var unit = row.querySelector('.sched-unit').value;
  var fromRaw = row.querySelector('.sched-from').value;
  var toRaw = row.querySelector('.sched-to').value;
  var now = new Date();
  var isExportCtx = !row.querySelector('.sched-type');  // export forms have no sched-type field
  var from = (fromRaw === 'now') ? (isExportCtx ? 0 : now.getHours()) : parseInt(fromRaw);
  var to = (toRaw === 'now') ? now.getHours() : parseInt(toRaw);

  var hour, minute, second = '0';

  // Build hour expression from range
  if (from === 0 && to === 0) {
    hour = '*';
  } else if (from === to) {
    hour = String(from);
  } else if (from < to) {
    hour = from + '-' + to;
  } else {
    hour = from + '-23,0-' + to;
  }

  // Build cron fields from interval
  if (unit === 'seconds') {
    amount = Math.max(1, Math.round(amount));
    minute = '*';
    second = amount >= 60 ? '0' : '*/' + amount;
  } else if (unit === 'minutes') {
    amount = Math.max(1, Math.round(amount));
    if (amount >= 60) {
      minute = '0';
    } else {
      minute = '*/' + amount;
    }
  } else {  // hours
    amount = Math.max(1, Math.round(amount));
    if (hour === '*') hour = '*/' + amount;
    minute = '0';
  }

  // Determine schedule type: interval (anchored to now) vs cron (aligned to clock)
  var isInterval = (fromRaw === 'now');

  row.querySelector('.sched-hour').value = hour;
  row.querySelector('.sched-minute').value = minute;
  var secEl = row.querySelector('.sched-second');
  if (secEl) secEl.value = second;

  // Set interval/type hidden fields if they exist (camera schedule rows)
  var typeEl = row.querySelector('.sched-type');
  var startDateEl = row.querySelector('.sched-start-date');
  var intAmountEl = row.querySelector('.sched-interval-amount');
  var intUnitEl = row.querySelector('.sched-interval-unit');
  if (typeEl) typeEl.value = isInterval ? 'interval' : 'cron';
  if (startDateEl) startDateEl.value = isInterval ? now.toISOString() : '';
  if (intAmountEl) intAmountEl.value = isInterval ? String(amount) : '';
  if (intUnitEl) intUnitEl.value = isInterval ? unit : '';

  // Update summary text
  var summaryEl = row.querySelector('.sched-summary');
  if (summaryEl) {
    var intStr;
    if (unit === 'seconds') intStr = amount + ' second' + (amount !== 1 ? 's' : '');
    else if (unit === 'minutes') intStr = amount + ' minute' + (amount !== 1 ? 's' : '');
    else intStr = amount + ' hour' + (amount !== 1 ? 's' : '');

    var rangeStr;
    var isExportContext = !typeEl;  // Export forms have no sched-type hidden field
    var nowTime = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
    var fromLabel = (fromRaw === 'now') ? (isExportContext ? 'start of collection' : 'now (' + nowTime + ')') : formatHour(from);
    var toLabel = (toRaw === 'now') ? 'now (' + nowTime + ')' : formatHour(to);
    var toIsAllDay = (toRaw === '0' || toRaw === 'All day');
    if (fromRaw !== 'now' && from === 0 && toIsAllDay) rangeStr = 'all day';
    else if (fromRaw === 'now' && isExportContext && toIsAllDay) rangeStr = 'all hours';
    else if (toIsAllDay) rangeStr = 'from ' + fromLabel;
    else if (from === to) rangeStr = 'at ' + fromLabel + ' only';
    else rangeStr = fromLabel + ' \u2014 ' + toLabel;

    summaryEl.textContent = 'Every ' + intStr + ', ' + rangeStr;

    // Show sample times
    if (isInterval && !isExportContext) {
      // Interval mode: samples anchored to current time (cameras only)
      var samples = _intervalSamples(now, amount, unit, 4);
      if (samples) summaryEl.textContent += ' \u2014 e.g. ' + samples;
    } else {
      var samples = _schedSamples(hour, minute, second);
      if (samples) summaryEl.textContent += ' \u2014 e.g. ' + samples;
    }
  }
}

/* Generate sample times for interval-based schedules (anchored to start time) */
function _intervalSamples(start, amount, unit, count) {
  var times = [];
  var ms;
  if (unit === 'seconds') ms = amount * 1000;
  else if (unit === 'minutes') ms = amount * 60000;
  else ms = amount * 3600000;
  for (var i = 0; i < count; i++) {
    var t = new Date(start.getTime() + i * ms);
    var hh = t.getHours() < 10 ? '0' + t.getHours() : '' + t.getHours();
    var mm = t.getMinutes() < 10 ? '0' + t.getMinutes() : '' + t.getMinutes();
    var str = hh + ':' + mm;
    if (unit === 'seconds') {
      var ss = t.getSeconds() < 10 ? '0' + t.getSeconds() : '' + t.getSeconds();
      str += ':' + ss;
    }
    times.push(str);
  }
  return times.join(', ');
}

/* Generate a few sample times for the cron summary */
function _schedSamples(hour, minute, second) {
  var times = [];
  var hList = _expandCron(hour, 0, 23, 5);
  var mList = _expandCron(minute, 0, 59, 60);
  var sList = _expandCron(second, 0, 59, 60);
  var showSec = (second !== '0');
  for (var hi = 0; hi < hList.length && times.length < 4; hi++) {
    for (var mi = 0; mi < mList.length && times.length < 4; mi++) {
      for (var si = 0; si < sList.length && times.length < 4; si++) {
        var h = hList[hi], m = mList[mi], s = sList[si];
        var hh = h < 10 ? '0' + h : '' + h;
        var mm = m < 10 ? '0' + m : '' + m;
        var t = hh + ':' + mm;
        if (showSec) { var ss = s < 10 ? '0' + s : '' + s; t += ':' + ss; }
        times.push(t);
      }
    }
  }
  return times.join(', ');
}

/* Expand a simple cron field into up to maxItems values */
function _expandCron(expr, lo, hi, maxItems) {
  if (expr === '*') {
    var all = [];
    for (var i = lo; i <= hi && all.length < maxItems; i++) all.push(i);
    return all;
  }
  var stepMatch = expr.match(/^\*\/(\d+)$/);
  if (stepMatch) {
    var step = parseInt(stepMatch[1]);
    var vals = [];
    for (var v = lo; v <= hi && vals.length < maxItems; v += step) vals.push(v);
    return vals;
  }
  // range-step like 6-20/2 or simple range 6-20
  var rangeStep = expr.match(/^(\d+)-(\d+)(?:\/(\d+))?$/);
  if (rangeStep) {
    var rLo = parseInt(rangeStep[1]), rHi = parseInt(rangeStep[2]), rStep = parseInt(rangeStep[3] || 1);
    var rv = [];
    for (var r = rLo; r <= rHi && rv.length < maxItems; r += rStep) rv.push(r);
    return rv;
  }
  // comma-separated
  if (expr.indexOf(',') >= 0) {
    return expr.split(',').slice(0, maxItems).map(function(x) { return parseInt(x.trim()); });
  }
  // single value
  return [parseInt(expr)];
}

/* Reverse-parse cron values into the schedule builder inputs */
function initSchedRow(row) {
  var typeEl = row.querySelector('.sched-type');
  var schedType = typeEl ? typeEl.value : 'cron';

  var hourVal = row.querySelector('.sched-hour').value;
  var minVal = row.querySelector('.sched-minute').value;
  var secEl = row.querySelector('.sched-second');
  var secVal = secEl ? secEl.value : '0';

  var from = 0, to = 0, amount = 1, unit = 'minutes', fromVal = '0';

  if (schedType === 'interval') {
    // Interval mode — read from interval fields
    var intAmountEl = row.querySelector('.sched-interval-amount');
    var intUnitEl = row.querySelector('.sched-interval-unit');
    amount = intAmountEl ? parseInt(intAmountEl.value) || 1 : 1;
    unit = intUnitEl ? intUnitEl.value : 'minutes';
    fromVal = 'now';
  } else {
    // Cron mode — reverse-parse hour/minute/second fields
    // Parse hour range
    if (hourVal === '*' || hourVal.match(/^\*\/\d+$/)) {
      from = 0; to = 0;
    } else if (hourVal.match(/^(\d+)-(\d+)$/)) {
      var m = hourVal.match(/^(\d+)-(\d+)$/);
      from = parseInt(m[1]); to = parseInt(m[2]);
    } else if (hourVal.match(/^(\d+)-23,0-(\d+)$/)) {
      var m2 = hourVal.match(/^(\d+)-23,0-(\d+)$/);
      from = parseInt(m2[1]); to = parseInt(m2[2]);
    } else if (hourVal.match(/^(\d+),/)) {
      from = parseInt(hourVal.split(',')[0]); to = 0;
    } else if (hourVal.match(/^(\d+)$/)) {
      from = parseInt(hourVal); to = parseInt(hourVal);
    }

    // Parse interval from second/minute/hour fields
    if (secVal && secVal !== '0' && secVal.match(/^\*\/(\d+)$/)) {
      amount = parseInt(secVal.match(/^\*\/(\d+)$/)[1]);
      unit = 'seconds';
    } else if (minVal === '*') {
      amount = 1; unit = 'minutes';
    } else if (minVal === '0') {
      var hStep = hourVal.match(/^\*\/(\d+)$/);
      if (hStep) { amount = parseInt(hStep[1]); unit = 'hours'; }
      else { amount = 1; unit = 'hours'; }
    } else if (minVal.match(/^\*\/(\d+)$/)) {
      amount = parseInt(minVal.match(/^\*\/(\d+)$/)[1]);
      unit = 'minutes';
    }
    // In export context, hour='*' means "Start" (all hours from collection)
    if (!typeEl && hourVal === '*' && !hourVal.match(/^\*\/\d+$/)) {
      fromVal = 'now';
    } else {
      fromVal = String(from);
    }
  }

  // Set inputs
  var amountEl = row.querySelector('.sched-amount');
  var unitEl = row.querySelector('.sched-unit');
  var fromSel = row.querySelector('.sched-from');
  var toSel = row.querySelector('.sched-to');

  if (amountEl) amountEl.value = amount;
  if (unitEl) unitEl.value = unit;
  if (fromSel) fromSel.value = fromVal;
  if (toSel) toSel.value = String(to);

  // Trigger summary update
  schedUpdate(amountEl || unitEl);
}

/* Add a new schedule row to any container by ID.
   If showRemove is false, the remove button is hidden (for single-schedule forms). */
function addScheduleRow(containerId, showRemove) {
  if (showRemove === undefined) showRemove = true;
  var container = document.getElementById(containerId);
  var row = document.createElement('div');
  row.className = 'schedule-row';
  row.style.cssText = 'padding:0.5rem 0; border-bottom:1px solid var(--border);';

  var fromOptions = '<option value="now">Now</option><option value="0">12 AM</option>';
  var toOptions = '<option value="0">All day</option>';
  for (var h = 1; h < 24; h++) {
    var label = (h <= 12 ? h : h - 12) + ' ' + (h < 12 ? 'AM' : 'PM');
    fromOptions += '<option value="' + h + '">' + label + '</option>';
    toOptions += '<option value="' + h + '">' + label + '</option>';
  }

  var removeBtn = showRemove
    ? '<button type="button" class="btn-small btn-danger" onclick="this.closest(\'.schedule-row\').remove()" style="margin-bottom:0.5rem;">&times;</button>'
    : '';

  row.innerHTML = '<input type="hidden" name="sched_enabled" class="sched-enabled" value="true">' +
    '<div style="display:flex; gap:0.4rem; align-items:flex-end; flex-wrap:wrap;">' +
    '<label class="toggle" style="flex:0 0 36px; margin-bottom:0.5rem;" title="Enable/disable this schedule">' +
      '<input type="checkbox" checked onchange="var r=this.closest(\'.schedule-row\'); var h=r.querySelector(\'.sched-enabled\'); h.value=this.checked?\'true\':\'false\'; r.classList.toggle(\'disabled\',!this.checked);">' +
      '<span class="toggle-track"></span>' +
    '</label>' +
    '<label style="flex:0 0 60px;">Every' +
      '<input type="number" class="sched-amount" value="15" min="1" max="360" style="width:100%;" onchange="schedUpdate(this)" oninput="schedUpdate(this)">' +
    '</label>' +
    '<label style="flex:0 0 90px;">Unit' +
      '<select class="sched-unit" onchange="schedUpdate(this)">' +
        '<option value="seconds">seconds</option>' +
        '<option value="minutes" selected>minutes</option>' +
        '<option value="hours">hours</option>' +
      '</select>' +
    '</label>' +
    '<label style="flex:1; min-width:80px;">From<select class="sched-from" onchange="schedUpdate(this)">' + fromOptions + '</select></label>' +
    '<label style="flex:1; min-width:80px;">To<select class="sched-to" onchange="schedUpdate(this)">' + toOptions + '</select></label>' +
    removeBtn +
    '</div>' +
    '<input type="hidden" class="sched-type" name="sched_type" value="interval">' +
    '<input type="hidden" class="sched-start-date" name="sched_start_date" value="">' +
    '<input type="hidden" class="sched-hour" name="sched_hour" value="*">' +
    '<input type="hidden" class="sched-minute" name="sched_minute" value="*/15">' +
    '<input type="hidden" class="sched-second" name="sched_second" value="0">' +
    '<input type="hidden" class="sched-interval-amount" name="sched_interval_amount" value="15">' +
    '<input type="hidden" class="sched-interval-unit" name="sched_interval_unit" value="minutes">' +
    '<p class="muted sched-summary" style="margin:0.15rem 0 0; font-size:0.8rem;"></p>';

  container.appendChild(row);
  schedUpdate(row.querySelector('.sched-amount'));
}

/* Initialize all schedule rows in a container from their hidden cron values */
function initScheduleRows(containerId) {
  document.querySelectorAll('#' + containerId + ' .schedule-row').forEach(function(row) {
    initSchedRow(row);
  });
}

/* Convenience aliases for cameras and exports */
function addCamSchedule() { addScheduleRow('cam-schedules', true); }
function addExpSchedule() { addScheduleRow('exp-schedules', true); }

/* Backward compat */
var camSchedUpdate = schedUpdate;
var initCamSchedRow = initSchedRow;


/* ===================================================================
 * Task cancellation
 * =================================================================== */
function cancelTask(taskId) {
  fetch('/api/tasks/' + taskId + '/cancel', { method: 'POST' })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.error) console.warn('Cancel failed:', data.error);
    })
    .catch(function(err) { console.error('Cancel request failed:', err); });
}


/* ===================================================================
 * Generic modal helpers
 * =================================================================== */
function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) {
  var el = document.getElementById(id);
  if (el) el.style.display = 'none';
}

/* Close any visible modal on Escape */
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal').forEach(function(m) {
      if (m.style.display !== 'none') m.style.display = 'none';
    });
  }
});

/* Dashboard camera thumbnail hide/show (persists in localStorage) */
function _hiddenThumbs() {
  try { return JSON.parse(localStorage.getItem('pylapse_hidden_thumbs') || '[]'); } catch(e) { return []; }
}
function _applyHiddenThumbs() {
  var hidden = _hiddenThumbs();
  for (var i = 0; i < hidden.length; i++) {
    var wrap = document.getElementById('thumb-wrap-' + hidden[i]);
    var showBtn = document.getElementById('thumb-show-' + hidden[i]);
    if (wrap) wrap.style.display = 'none';
    if (showBtn) showBtn.style.display = '';
  }
}
function hideThumb(camId) {
  var wrap = document.getElementById('thumb-wrap-' + camId);
  var showBtn = document.getElementById('thumb-show-' + camId);
  if (wrap) wrap.style.display = 'none';
  if (showBtn) showBtn.style.display = '';
  var hidden = _hiddenThumbs();
  if (hidden.indexOf(camId) === -1) hidden.push(camId);
  localStorage.setItem('pylapse_hidden_thumbs', JSON.stringify(hidden));
}
function showThumb(camId) {
  var wrap = document.getElementById('thumb-wrap-' + camId);
  var showBtn = document.getElementById('thumb-show-' + camId);
  if (wrap) wrap.style.display = '';
  if (showBtn) showBtn.style.display = 'none';
  var hidden = _hiddenThumbs().filter(function(id) { return id !== camId; });
  localStorage.setItem('pylapse_hidden_thumbs', JSON.stringify(hidden));
}
/* Apply hidden state on initial page load + after htmx swaps (dashboard 15s auto-refresh) */
document.addEventListener('DOMContentLoaded', _applyHiddenThumbs);
document.addEventListener('htmx:afterSettle', _applyHiddenThumbs);

/* Camera modal */
function openCameraModal() { openModal('camera-modal'); }
function closeCameraModal() { closeModal('camera-modal'); }

/* Export modal */
function openExportModal() { openModal('export-modal'); }
function closeExportModal() { closeModal('export-modal'); }

/* Export collection picker — pre-fill fields when a collection is selected */
function expCollPick(sel) {
  var opt = sel.options[sel.selectedIndex];
  var collId = document.getElementById('exp-coll-id');
  var name = document.getElementById('exp-edit-name');
  var indir = document.getElementById('exp-edit-indir');
  var dateSrc = document.getElementById('exp-date-source');
  if (opt.value) {
    collId.value = opt.value;
    if (name && !name.value) name.value = opt.dataset.name || '';
    if (indir) indir.value = opt.dataset.path || '';
    if (dateSrc) dateSrc.value = opt.dataset.dateSource || 'filename';
    // Update video pattern to match collection ext
    var pat = document.querySelector('[name="video_pattern"]');
    if (pat) pat.value = '*.' + (opt.dataset.ext || 'jpg');
  } else {
    collId.value = '';
  }
}


/* ===================================================================
 * Collections — save modal
 * =================================================================== */
function openSaveModal(path, dateSource, collId, name, exportDir, ext, timezone) {
  var collPath = document.getElementById('coll-path');
  var collDateSrc = document.getElementById('coll-date-source');
  var collName = document.getElementById('coll-name');
  document.getElementById('save-path').value = path || (collPath ? collPath.value : '');
  document.getElementById('save-date-source').value = dateSource || (collDateSrc ? collDateSrc.value : 'filename');
  document.getElementById('save-coll-id').value = collId || '';
  document.getElementById('save-name').value = name || (collName ? collName.value : '') || '';
  document.getElementById('save-ext').value = ext || 'jpg';
  document.getElementById('save-timezone').value = timezone || '';
  document.getElementById('save-modal-title').textContent = collId ? 'Edit Collection' : 'Save Collection';
  document.getElementById('save-modal').style.display = 'flex';
}

function closeSaveModal() {
  document.getElementById('save-modal').style.display = 'none';
}

function loadSavedCollection(collId, path, dateSource) {
  var collPath = document.getElementById('coll-path');
  var collDateSrc = document.getElementById('coll-date-source');
  if (collPath) collPath.value = path;
  if (collDateSrc) collDateSrc.value = dateSource;
}

/* Event delegation for save/edit collection buttons and create-video (data-attribute based) */
document.addEventListener('click', function(e) {
  var btn = e.target.closest('.save-coll-btn');
  if (btn) {
    openSaveModal(btn.dataset.path, btn.dataset.dateSource, '', btn.dataset.name, '', '');
    return;
  }
  btn = e.target.closest('.edit-coll-btn');
  if (btn) {
    openSaveModal(btn.dataset.path, btn.dataset.dateSource, btn.dataset.collId, btn.dataset.name, btn.dataset.exportDir, btn.dataset.ext, btn.dataset.timezone);
    return;
  }
  btn = e.target.closest('.create-video-btn');
  if (btn) {
    var inputDir = btn.dataset.inputDir || '';
    var name = btn.dataset.name || '';
    window.location.href = '/videos?input_dir=' + encodeURIComponent(inputDir) + '&name=' + encodeURIComponent(name);
  }
});


/* ===================================================================
 * Exports — date range presets
 * =================================================================== */
function setDateRange(preset) {
  var fromEl = document.getElementById('exp-date-from');
  var toEl = document.getElementById('exp-date-to');
  if (!fromEl || !toEl) return;

  var today = new Date();
  var fmt = function(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  };

  if (preset === 'all') {
    fromEl.value = '';
    toEl.value = '';
  } else if (preset === 'today') {
    fromEl.value = fmt(today);
    toEl.value = fmt(today);
  } else if (preset === 'yesterday') {
    var y = new Date(today); y.setDate(y.getDate() - 1);
    fromEl.value = fmt(y);
    toEl.value = fmt(y);
  } else if (preset === 'month') {
    fromEl.value = fmt(new Date(today.getFullYear(), today.getMonth(), 1));
    toEl.value = fmt(today);
  } else {
    // Numeric = last N days
    var n = parseInt(preset) || 7;
    var start = new Date(today); start.setDate(start.getDate() - (n - 1));
    fromEl.value = fmt(start);
    toEl.value = fmt(today);
  }
}


/* ===================================================================
 * Exports — time filter presets (kept for collection detail page)
 * =================================================================== */
function applyCPreset(hour, minute, el) {
  document.getElementById('coll-export-hour').value = hour;
  document.getElementById('coll-export-minute').value = minute;
  el.closest('.preset-chips').querySelectorAll('.preset-chip').forEach(function(c) { c.classList.remove('active'); });
  el.classList.add('active');
}


/* ===================================================================
 * Global task tray — polls for active tasks, shows progress on all pages
 * =================================================================== */
(function() {
  var tray = document.getElementById('task-tray');
  if (!tray) return;

  // Track tasks we've seen complete so we can show them briefly then remove
  var doneTimers = {};

  function fmtDuration(secs) {
    if (!secs || secs < 0) return '';
    secs = Math.round(secs);
    if (secs < 60) return secs + 's';
    var m = Math.floor(secs / 60);
    var s = secs % 60;
    if (m < 60) return m + 'm ' + (s < 10 ? '0' : '') + s + 's';
    var h = Math.floor(m / 60);
    m = m % 60;
    return h + 'h ' + (m < 10 ? '0' : '') + m + 'm';
  }

  function fmtRate(rate) {
    if (!rate || rate <= 0) return '';
    if (rate >= 10) return Math.round(rate) + '/s';
    if (rate >= 1) return rate.toFixed(1) + '/s';
    // Less than 1/s — show as x/min
    var perMin = rate * 60;
    if (perMin >= 1) return perMin.toFixed(1) + '/min';
    return rate.toFixed(2) + '/s';
  }

  function renderTray(tasks) {
    // Build set of active task IDs
    var activeIds = {};
    tasks.forEach(function(t) { activeIds[t.id] = true; });

    // Remove tray items for tasks no longer active (and not in done timer)
    tray.querySelectorAll('.tray-task').forEach(function(el) {
      var tid = el.dataset.taskId;
      if (!activeIds[tid] && !doneTimers[tid]) {
        el.remove();
      }
    });

    tasks.forEach(function(t) {
      var el = tray.querySelector('[data-task-id="' + t.id + '"]');
      if (!el) {
        el = document.createElement('div');
        el.className = 'tray-task';
        el.dataset.taskId = t.id;
        el.innerHTML =
          '<div class="tray-name"><span class="tray-label"></span><span class="tray-pct"></span>' +
          '<button class="btn-small btn-danger tray-cancel" onclick="cancelTask(\'' + t.id + '\')" style="padding:0 0.3rem;font-size:0.7rem;margin-left:auto;">&times;</button></div>' +
          '<div class="progress-bar"><div class="progress-fill" style="width:0%"></div></div>' +
          '<p class="tray-msg"></p>' +
          '<p class="tray-stats"></p>';
        tray.appendChild(el);
      }

      el.querySelector('.tray-label').textContent = t.name;
      var pct = t.progress.toFixed(1) + '%';
      el.querySelector('.tray-pct').textContent = pct;
      el.querySelector('.progress-fill').style.width = pct;

      var msg = '';
      if (t.current && t.total) msg = t.current + '/' + t.total;
      if (t.message) msg += (msg ? ' \u2014 ' : '') + t.message;
      el.querySelector('.tray-msg').textContent = msg || t.status;

      // Rate + ETA line
      var stats = [];
      var r = fmtRate(t.rate);
      if (r) stats.push(r);
      if (t.elapsed > 0) stats.push('elapsed ' + fmtDuration(t.elapsed));
      if (t.eta > 0) stats.push('~' + fmtDuration(t.eta) + ' left');
      el.querySelector('.tray-stats').textContent = stats.join(' \u00b7 ');
    });
  }

  function pollTasks() {
    fetch('/api/tasks/active')
      .then(function(r) { return r.json(); })
      .then(function(tasks) {
        renderTray(tasks);
        // Also check for recently completed tasks to show briefly
        checkCompleted();
        // Poll faster when there are active tasks
        var delay = tasks.length > 0 ? 800 : 5000;
        setTimeout(pollTasks, delay);
      })
      .catch(function() {
        setTimeout(pollTasks, 5000);
      });
  }

  function checkCompleted() {
    // Check all tasks and briefly show completed/failed ones
    fetch('/api/tasks')
      .then(function(r) { return r.json(); })
      .then(function(allTasks) {
        allTasks.forEach(function(t) {
          if ((t.status === 'completed' || t.status === 'failed') && !doneTimers[t.id]) {
            var el = tray.querySelector('[data-task-id="' + t.id + '"]');
            if (el) {
              // Task was active and just finished — show result briefly
              el.classList.add(t.status === 'completed' ? 'tray-done' : 'tray-failed');
              el.querySelector('.tray-pct').textContent = t.status === 'completed' ? 'Done' : 'Failed';
              el.querySelector('.tray-msg').textContent = t.status === 'failed' ? (t.error || '').split('\n').pop() : 'Completed';
              el.querySelector('.progress-fill').style.width = '100%';
              if (t.status === 'failed') el.querySelector('.progress-fill').style.background = 'var(--err)';
              doneTimers[t.id] = setTimeout(function() {
                el.remove();
                delete doneTimers[t.id];
              }, 8000);
            }
          }
        });
      })
      .catch(function() {});
  }

  // Start polling
  pollTasks();
})();
