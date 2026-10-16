const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');

const DATA_FILE = path.resolve(__dirname, '..', 'output', 'merged_domain_encoded.json');
const BACKUP_DIR = path.resolve(__dirname, '..', 'output', 'backups');
const ALLOWED_FIELDS = new Set(['朝代', '领域', '领域标签', '领域编码', 'author', '影响力评分', '身份与贡献', '简介']);
const DYNASTY_FIELDS = ['朝代', '朝代原值', '朝代类别', '朝代编码', '年代排序', '朝代id'];

let writeQueue = Promise.resolve();

function versionOf(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

async function readSnapshot() {
  const buffer = await fs.readFile(DATA_FILE);
  const data = JSON.parse(buffer.toString('utf8'));
  if (!data || !Array.isArray(data.records) || !data['领域编码规则映射']) {
    throw new Error('数据文件结构无效');
  }
  return { data, version: versionOf(buffer) };
}

function buildCatalog(data) {
  const dynastyMap = new Map();
  for (const record of data.records) {
    const tuple = Object.fromEntries(DYNASTY_FIELDS.map((key) => [key, record[key] ?? null]));
    const key = JSON.stringify(tuple);
    dynastyMap.set(key, tuple);
  }

  const taxonomy = data['领域编码规则映射'];
  const domains = Object.entries(taxonomy).map(([code, entry]) => ({
    code: Number(code),
    category: entry['一级分类'],
    label: entry['二级标签'],
  }));

  return {
    dynasties: [...dynastyMap.values()].sort((a, b) => {
      const aa = a['朝代id'] ?? -1;
      const bb = b['朝代id'] ?? -1;
      return aa - bb || String(a['朝代']).localeCompare(String(b['朝代']), 'zh-CN');
    }),
    domains,
  };
}

async function getData() {
  const snapshot = await readSnapshot();
  return { ...snapshot, catalog: buildCatalog(snapshot.data) };
}

function validatePatch(record, patch, data) {
  if (!patch || typeof patch !== 'object' || Array.isArray(patch)) throw new Error('编辑数据必须是对象');
  const keys = Object.keys(patch);
  if (!keys.length || keys.some((key) => !ALLOWED_FIELDS.has(key))) throw new Error('包含不允许修改的字段');

  const next = { ...record };
  if (Object.hasOwn(patch, '朝代')) {
    if (typeof patch['朝代'] !== 'string') throw new Error('朝代名称无效');
    const candidate = buildCatalog(data).dynasties.find((item) => item['朝代'] === patch['朝代']);
    if (!candidate) throw new Error('朝代必须从当前数据目录中选择');
    Object.assign(next, candidate);
    next['朝代原值'] = candidate['朝代'];
  }

  if (Object.hasOwn(patch, '领域标签')) {
    if (!Array.isArray(patch['领域标签']) || patch['领域标签'].some((label) => typeof label !== 'string')) {
      throw new Error('领域标签必须是字符串数组');
    }
    const taxonomy = data['领域编码规则映射'];
    const selected = [...new Set(patch['领域标签'])];
    for (const label of selected) {
      if (!Object.values(taxonomy).some((entry) => `${entry['一级分类']}/${entry['二级标签']}` === label)) {
        throw new Error(`未知领域标签: ${label}`);
      }
    }
    next['领域标签'] = selected;
    next['领域编码'] = selected.map((label) => {
      const [category, detail] = label.split('/');
      const found = Object.entries(taxonomy).find(([, entry]) => entry['一级分类'] === category && entry['二级标签'] === detail);
      return Number(found[0]);
    });
    next['领域'] = selected.map((label) => label.split('/').at(-1)).join('、');
    next['领域分类状态'] = selected.length ? '已分类' : '待审核';
    if (selected.length) next['领域待审核片段'] = [];
  }

  if (Object.hasOwn(patch, '领域')) {
    if (typeof patch['领域'] !== 'string' || patch['领域'].length > 2000) throw new Error('领域文本无效');
    next['领域'] = patch['领域'].trim();
  }
  for (const key of ['author', '身份与贡献', '简介']) {
    if (Object.hasOwn(patch, key)) {
      if (typeof patch[key] !== 'string' || patch[key].length > 4000) throw new Error(`${key}必须是有效文本`);
      next[key] = patch[key].trim();
    }
  }
  if (Object.hasOwn(patch, '影响力评分')) {
    if (!Number.isInteger(patch['影响力评分']) || patch['影响力评分'] < 0 || patch['影响力评分'] > 5) {
      throw new Error('评分必须是 0 到 5 的整数');
    }
    next['影响力评分'] = patch['影响力评分'];
  }
  if (Object.hasOwn(patch, '领域编码')) {
    throw new Error('领域编码由领域标签自动生成，不能单独编辑');
  }
  return next;
}

async function atomicWrite(buffer) {
  await fs.mkdir(path.dirname(DATA_FILE), { recursive: true });
  const tempPath = path.join(path.dirname(DATA_FILE), `.${path.basename(DATA_FILE)}.${process.pid}.${crypto.randomUUID()}.tmp`);
  try {
    const handle = await fs.open(tempPath, 'wx', 0o600);
    try {
      await handle.writeFile(buffer);
      await handle.sync();
    } finally {
      await handle.close();
    }
    await fs.rename(tempPath, DATA_FILE);
  } finally {
    await fs.rm(tempPath, { force: true });
  }
}

async function updateRecord(id, patch, expectedVersion) {
  const task = writeQueue.then(async () => {
    const source = await fs.readFile(DATA_FILE);
    const currentVersion = versionOf(source);
    if (currentVersion !== expectedVersion) {
      const error = new Error('数据已被其他操作修改，请刷新后重试');
      error.status = 409;
      throw error;
    }
    const data = JSON.parse(source.toString('utf8'));
    const index = data.records.findIndex((record) => String(record.id) === String(id));
    if (index < 0) {
      const error = new Error('记录不存在');
      error.status = 404;
      throw error;
    }
    const before = data.records[index];
    const after = validatePatch(before, patch, data);
    data.records[index] = after;
    data.metadata.record_count = data.records.length;
    const output = Buffer.from(`${JSON.stringify(data, null, 2)}\n`, 'utf8');

    await fs.mkdir(BACKUP_DIR, { recursive: true });
    const stamp = new Date().toISOString().replaceAll(':', '-');
    const backupPath = path.join(BACKUP_DIR, `merged_domain_encoded.${stamp}.${crypto.randomUUID().slice(0, 8)}.json`);
    await fs.copyFile(DATA_FILE, backupPath, fs.constants.COPYFILE_EXCL);
    await atomicWrite(output);
    return { record: after, version: versionOf(output), backup: path.relative(path.resolve(__dirname, '..'), backupPath) };
  });
  writeQueue = task.catch(() => {});
  return task;
}

module.exports = { getData, updateRecord };
