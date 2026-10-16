const state = {
  records: [],
  catalog: { dynasties: [], domains: [] },
  version: '',
  filtered: [],
  page: 1,
  pageSize: 50,
  sorting: (() => {
    try {
      const saved = JSON.parse(localStorage.getItem('author-browser.sorting') || '[]');
      return Array.isArray(saved) ? saved.filter((item) => item && typeof item.key === 'string' && ['author', '朝代id', '领域标签', '影响力评分', '身份与贡献', '领域', '简介'].includes(item.key) && ['asc', 'desc'].includes(item.direction)) : [];
    } catch {
      return [];
    }
  })(),
  webMode: localStorage.getItem('author-browser.webMode') === 'true',
  webHost: localStorage.getItem('author-browser.webHost') || 'browse.library.kiwix.org',
  webVersion: localStorage.getItem('author-browser.webVersion') || 'wikisource_zh_all_nopic_2026-06',
  editingId: null,
};

const $ = (selector) => document.querySelector(selector);
const byId = new Map();
const domainByValue = new Map();
let toastTimer;

function text(value) {
  return value === null || value === undefined || value === '' ? '—' : String(value);
}

function escapeHtml(value) {
  const entities = { 38: '&', 60: '<', 62: '>', 34: '"', 39: '&#' + String.fromCharCode(39) + ';' };
  return String(value ?? '').replace(/[&<>"']/g, (char) => entities[char.charCodeAt(0)]);
}

function showToast(message, isError = false) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.toggle('error', isError);
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3200);
}

async function request(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.error || `请求失败 (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return payload;
}

function initializeFilters() {
  const from = $('#dynastyFrom');
  const to = $('#dynastyTo');
  const ids = [...new Set(state.catalog.dynasties.map((item) => item['朝代id']).filter((id) => Number.isFinite(id)))].sort((a, b) => a - b);
  for (const id of ids) {
    const names = [...new Set(state.catalog.dynasties.filter((item) => item['朝代id'] === id).map((item) => item['朝代']))].join('、');
    const label = `${id} · ${names}`;
    from.add(new Option(label, String(id)));
    to.add(new Option(label, String(id)));
  }

  const categories = [...new Set(state.catalog.domains.map((item) => item.category))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
  for (const category of categories) $('#domainCategory').add(new Option(category, category));
  for (const item of state.catalog.domains) domainByValue.set(`${item.category}/${item.label}`, item);
  updateDomainOptions();
}

function updateDomainOptions() {
  const select = $('#domainLabel');
  const selected = select.value;
  select.replaceChildren(new Option('全部二级', ''));
  const category = $('#domainCategory').value;
  const options = state.catalog.domains.filter((item) => !category || item.category === category).sort((a, b) => a.label.localeCompare(b.label, 'zh-CN'));
  for (const item of options) select.add(new Option(`${item.label} · ${item.code}`, `${item.category}/${item.label}`));
  if ([...select.options].some((option) => option.value === selected)) select.value = selected;
}

function passesFilters(record) {
  const fromValue = $('#dynastyFrom').value;
  const toValue = $('#dynastyTo').value;
  const id = Number(record['朝代id']);
  if (fromValue !== '' && id < Number(fromValue)) return false;
  if (toValue !== '' && id > Number(toValue)) return false;
  const query = $('#authorSearch').value.trim().toLocaleLowerCase();
  if (query && !String(record.author || '').toLocaleLowerCase().includes(query)) return false;
  const selectedCategory = $('#domainCategory').value;
  if (selectedCategory && !(record['领域标签'] || []).some((label) => label.startsWith(`${selectedCategory}/`))) return false;
  const selectedDomain = $('#domainLabel').value;
  if (selectedDomain && !(record['领域标签'] || []).includes(selectedDomain)) return false;
  if ($('#reviewOnly').checked && record['领域分类状态'] !== '待审核') return false;
  return true;
}

function sortValue(record, key) {
  if (key === '领域标签') return (record[key] || []).join(' ');
  if (key === '影响力评分') return Number(record[key] ?? 0);
  return record[key] ?? '';
}

function applyFilters() {
  state.filtered = state.records.filter(passesFilters);
  for (const sort of [...state.sorting].reverse()) {
    state.filtered.sort((a, b) => {
      const av = sortValue(a, sort.key);
      const bv = sortValue(b, sort.key);
      const result = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv), 'zh-CN', { numeric: true });
      return result * (sort.direction === 'asc' ? 1 : -1);
    });
  }
  const pageCount = Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
  state.page = Math.min(state.page, pageCount);
  render();
}

function toggleSort(key, additive) {
  const current = state.sorting.find((item) => item.key === key);
  if (!additive) {
    if (!current) state.sorting = [{ key, direction: 'asc' }];
    else if (current.direction === 'asc') state.sorting = [{ key, direction: 'desc' }];
    else state.sorting = [];
  } else if (!current) {
    state.sorting.push({ key, direction: 'asc' });
  } else if (current.direction === 'asc') {
    current.direction = 'desc';
  } else {
    state.sorting = state.sorting.filter((item) => item.key !== key);
  }
  localStorage.setItem('author-browser.sorting', JSON.stringify(state.sorting));
  applyFilters();
}

function sortLabel(key) {
  const index = state.sorting.findIndex((item) => item.key === key);
  if (index < 0) return '';
  return `${state.sorting[index].direction === 'asc' ? '▲' : '▼'}${state.sorting.length > 1 ? index + 1 : ''}`;
}

function renderTags(record) {
  const labels = record['领域标签'] || [];
  if (!labels.length) return record['领域待审核片段']?.length
    ? `<span class="domain-tag review-tag">待分类：${escapeHtml(record['领域待审核片段'].join('、'))}</span>`
    : '—';
  return `<div class="tag-list">${labels.map((label) => `<span class="domain-tag">${escapeHtml(label)}</span>`).join('')}</div>`;
}

function authorUrl(record) {
  return window.buildAuthorUrl(record.url, state.webMode, state.webHost, state.webVersion);
}

function renderRow(record) {
  const editing = state.editingId === String(record.id);
  const dynastySelect = editing
    ? `<select class="form-select form-select-sm edit-select" data-edit-dynasty>${state.catalog.dynasties.map((item) => `<option value="${escapeHtml(item['朝代'])}" ${item['朝代'] === record['朝代'] ? 'selected' : ''}>${escapeHtml(item['朝代'])} · ID ${escapeHtml(item['朝代id'])}</option>`).join('')}</select>`
    : `<div>${escapeHtml(text(record['朝代']))}</div><small class="text-secondary">ID ${escapeHtml(text(record['朝代id']))}</small>`;
  const domainEditor = editing
    ? `<div class="domain-editor">${state.catalog.domains.map((item) => {
      const value = `${item.category}/${item.label}`;
      return `<label><input class="form-check-input mt-0" type="checkbox" data-domain-option value="${escapeHtml(value)}" ${(record['领域标签'] || []).includes(value) ? 'checked' : ''}><span>${escapeHtml(item.category)} / ${escapeHtml(item.label)} <small class="text-secondary">${item.code}</small></span></label>`;
    }).join('')}</div>`
    : renderTags(record);
  const actions = editing
    ? `<div class="d-flex flex-column gap-1"><button class="btn btn-primary btn-sm" data-action="save">保存</button><button class="btn btn-outline-secondary btn-sm" data-action="cancel">取消</button></div>`
    : `<button class="btn btn-outline-primary btn-sm" data-action="edit">编辑</button>`;
  const authorLink = authorUrl(record);
  const authorCell = editing
    ? `<input class="form-control form-control-sm text-edit" data-edit-field="author" value="${escapeHtml(record.author || '')}" maxlength="300">`
    : authorLink
      ? `<a href="${escapeHtml(authorLink)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(record['备注'] || '新页面打开作者资料')}">${escapeHtml(text(record.author))}</a>`
      : `<span title="${escapeHtml(record['备注'] || '')}">${escapeHtml(text(record.author))}</span>`;
  const textField = (key, value, multiline = false) => {
    if (!editing) return `<div class="text-content" title="${escapeHtml(value || '')}">${escapeHtml(text(value))}</div>`;
    if (key === '影响力评分') return `<select class="form-select form-select-sm score-editor" data-edit-field="${key}">${[0, 1, 2, 3, 4, 5].map((score) => `<option value="${score}" ${Number(value) === score ? 'selected' : ''}>${score}</option>`).join('')}</select>`;
    return `<textarea class="form-control form-control-sm text-edit" data-edit-field="${key}" rows="${multiline ? 3 : 2}" maxlength="${key === '简介' || key === '身份与贡献' ? 4000 : 2000}">${escapeHtml(value || '')}</textarea>`;
  };

  return `<tr data-record-id="${escapeHtml(record.id)}">
    <td class="author-cell" data-label="作者">${authorCell}</td>
    <td class="dynasty-cell" data-label="朝代">${dynastySelect}</td>
    <td class="domain-cell" data-label="领域标签">${domainEditor}</td>
    <td class="score-cell" data-label="评分">${textField('影响力评分', record['影响力评分'])}</td>
    <td class="text-cell contribution-cell" data-label="身份与贡献">${textField('身份与贡献', record['身份与贡献'], true)}</td>
    <td class="text-cell" data-label="领域原文">${textField('领域', record['领域'])}</td>
    <td class="text-cell intro-cell" data-label="简介">${textField('简介', record['简介'], true)}</td>
    <td data-label="操作">${actions}</td>
  </tr>`;
}

function renderPagination(pageCount) {
  const list = $('#pagination');
  list.replaceChildren();
  const add = (label, page, disabled = false, active = false, aria = '') => {
    const item = document.createElement('li');
    item.className = `page-item${disabled ? ' disabled' : ''}${active ? ' active' : ''}`;
    item.innerHTML = `<button class="page-link" type="button" ${disabled ? 'disabled' : ''} ${aria}>${label}</button>`;
    item.querySelector('button').addEventListener('click', () => { state.page = page; render(); });
    list.append(item);
  };
  add('上一页', Math.max(1, state.page - 1), state.page <= 1, false, 'aria-label="上一页"');
  const start = Math.max(1, Math.min(state.page - 2, pageCount - 4));
  const end = Math.min(pageCount, start + 4);
  for (let page = start; page <= end; page += 1) add(String(page), page, false, page === state.page, `aria-label="第${page}页"`);
  add('下一页', Math.min(pageCount, state.page + 1), state.page >= pageCount, false, 'aria-label="下一页"');
}

function render() {
  const pageCount = Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
  const start = (state.page - 1) * state.pageSize;
  const rows = state.filtered.slice(start, start + state.pageSize);
  const table = $('.data-table');
  const tableFrame = $('.table-frame');
  const narrow = window.matchMedia('(max-width: 700px)').matches;
  document.body.classList.toggle('narrow-layout', narrow);
  table.classList.toggle('mobile-card-table', narrow);
  tableFrame.classList.toggle('mobile-cards', narrow);
  $('#recordsBody').innerHTML = rows.length ? rows.map(renderRow).join('') : '<tr><td colspan="8" class="state-cell">没有符合条件的记录</td></tr>';
  $('#emptyState').classList.toggle('d-none', rows.length > 0);
  $('#resultSummary').textContent = `共 ${state.filtered.length.toLocaleString()} 条 · 第 ${state.page} / ${pageCount} 页`;
  $('#pageJump').max = String(pageCount);
  $('#pageJump').value = String(state.page);
  $('#pagination').replaceChildren();
  renderPagination(pageCount);
  document.querySelectorAll('[data-sort]').forEach((header) => {
    const key = header.dataset.sort;
    header.querySelector('.sort-indicator').textContent = sortLabel(key);
    const current = state.sorting.find((item) => item.key === key);
    header.setAttribute('aria-sort', current ? (current.direction === 'asc' ? 'ascending' : 'descending') : 'none');
    header.title = '点击排序当前全部筛选结果（跨页生效）；按住 Shift 点击可添加次级排序';
  });
  const primarySort = state.sorting[0];
  $('#globalSort').value = primarySort?.key || '';
  $('#globalSortDirection').value = primarySort?.direction || 'asc';
  $('#globalSortDirection').disabled = !primarySort;
  $('#sortSummary').textContent = state.sorting.map((item, index) => `${index + 1}. ${item.key} ${item.direction === 'asc' ? '升序' : '降序'}`).join(' · ');
}

async function saveRow(row) {
  const id = row.dataset.recordId;
  const original = byId.get(id);
  const dynasty = row.querySelector('[data-edit-dynasty]').value;
  const labels = [...row.querySelectorAll('[data-domain-option]:checked')].map((input) => input.value);
  const patch = {};
  if (dynasty !== original['朝代']) patch['朝代'] = dynasty;
  if (JSON.stringify(labels.slice().sort()) !== JSON.stringify((original['领域标签'] || []).slice().sort())) patch['领域标签'] = labels;
  for (const input of row.querySelectorAll('[data-edit-field]')) {
    const key = input.dataset.editField;
    const nextValue = key === '影响力评分' ? Number(input.value) : input.value.trim();
    if (nextValue !== original[key]) patch[key] = nextValue;
  }
  if (Object.hasOwn(patch, '影响力评分') && (!Number.isInteger(patch['影响力评分']) || patch['影响力评分'] < 0 || patch['影响力评分'] > 5)) {
    showToast('评分必须是 0 到 5 的整数', true);
    return;
  }
  if (!Object.keys(patch).length) {
    state.editingId = null;
    render();
    return;
  }
  const saveButton = row.querySelector('[data-action="save"]');
  saveButton.disabled = true;
  saveButton.textContent = '保存中';
  try {
    const result = await request(`/api/records/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patch, version: state.version }),
    });
    Object.assign(original, result.record);
    state.version = result.version;
    state.editingId = null;
    applyFilters();
    showToast(`记录已保存；备份：${result.backup}`);
  } catch (error) {
    if (error.status === 409) {
      showToast(`${error.message}，正在重新加载`, true);
      await loadData();
    } else {
      showToast(error.message, true);
      saveButton.disabled = false;
      saveButton.textContent = '保存';
    }
  }
}

async function loadData() {
  $('#connectionStatus').textContent = '正在加载数据...';
  try {
    const payload = await request('/api/records');
    state.records = payload.records;
    state.version = payload.version;
    state.catalog = payload.catalog;
    byId.clear();
    for (const record of state.records) byId.set(String(record.id), record);
    initializeFilters();
    $('#connectionStatus').textContent = `${state.records.length.toLocaleString()} 条记录已载入`;
    $('.status-dot').classList.add('online');
    applyFilters();
  } catch (error) {
    $('#connectionStatus').textContent = '数据载入失败';
    $('#recordsBody').innerHTML = `<tr><td colspan="8" class="state-cell">${escapeHtml(error.message)}</td></tr>`;
    showToast(error.message, true);
  }
}

$('#webMode').checked = state.webMode;
$('#webHost').value = state.webHost;
$('#webVersion').value = state.webVersion;
$('#webModeSettings').hidden = !state.webMode;
document.querySelectorAll('[data-sort]').forEach((header) => {
  header.addEventListener('click', (event) => toggleSort(header.dataset.sort, event.shiftKey));
});
function saveWebSettings() {
  state.webMode = $('#webMode').checked;
  state.webHost = $('#webHost').value.trim();
  state.webVersion = $('#webVersion').value.trim();
  localStorage.setItem('author-browser.webMode', String(state.webMode));
  localStorage.setItem('author-browser.webHost', state.webHost);
  localStorage.setItem('author-browser.webVersion', state.webVersion);
  $('#webModeSettings').hidden = !state.webMode;
  render();
}
$('#webMode').addEventListener('change', saveWebSettings);
$('#webHost').addEventListener('input', saveWebSettings);
$('#webVersion').addEventListener('input', saveWebSettings);
$('#globalSort').addEventListener('change', () => {
  const key = $('#globalSort').value;
  state.sorting = key ? [{ key, direction: $('#globalSortDirection').value }] : [];
  localStorage.setItem('author-browser.sorting', JSON.stringify(state.sorting));
  state.page = 1;
  applyFilters();
});
$('#globalSortDirection').addEventListener('change', () => {
  if (!state.sorting.length) return;
  state.sorting[0].direction = $('#globalSortDirection').value;
  localStorage.setItem('author-browser.sorting', JSON.stringify(state.sorting));
  applyFilters();
});
['dynastyFrom', 'dynastyTo', 'domainLabel', 'authorSearch', 'reviewOnly'].forEach((id) => {
  const element = document.getElementById(id);
  element.addEventListener(id === 'authorSearch' ? 'input' : 'change', () => { state.page = 1; applyFilters(); });
});
$('#domainCategory').addEventListener('change', () => { updateDomainOptions(); state.page = 1; applyFilters(); });
$('#resetFilters').addEventListener('click', () => {
  $('#dynastyFrom').value = '';
  $('#dynastyTo').value = '';
  $('#domainCategory').value = '';
  $('#domainLabel').value = '';
  updateDomainOptions();
  $('#authorSearch').value = '';
  $('#reviewOnly').checked = false;
  state.sorting = [];
  localStorage.removeItem('author-browser.sorting');
  state.page = 1;
  applyFilters();
});
$('#pageSize').addEventListener('change', () => { state.pageSize = Number($('#pageSize').value); state.page = 1; applyFilters(); });
$('#pageJump').addEventListener('change', () => {
  const max = Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
  state.page = Math.max(1, Math.min(max, Number($('#pageJump').value) || 1));
  render();
});
$('#recordsBody').addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const row = button.closest('tr');
  const id = row.dataset.recordId;
  if (button.dataset.action === 'edit') { state.editingId = id; render(); }
  if (button.dataset.action === 'cancel') { state.editingId = null; render(); }
  if (button.dataset.action === 'save') saveRow(row);
});

window.addEventListener('resize', () => {
  document.body.classList.toggle('narrow-layout', window.matchMedia('(max-width: 700px)').matches);
  render();
});

loadData();
