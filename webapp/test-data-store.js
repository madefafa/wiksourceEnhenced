const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

async function run() {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), 'author-browser-test-'));
  const output = path.join(temp, 'output');
  const appDir = path.join(temp, 'webapp');
  await fs.mkdir(output, { recursive: true });
  await fs.mkdir(appDir, { recursive: true });
  const source = {
    metadata: { record_count: 1 },
    '领域编码规则映射': {
      101: { '一级分类': '文学与语言', '二级标签': '文学' },
      102: { '一级分类': '文学与语言', '二级标签': '诗歌' },
    },
    records: [{
      id: 'sample', author: '测试作者', 朝代: '唐朝前期', 朝代原值: '唐朝前期', 朝代类别: '中国时期', 朝代编码: 9, 年代排序: 9, 朝代id: 9,
      领域: '文学', 领域标签: ['文学与语言/文学'], 领域编码: [101], 领域分类状态: '已分类', 领域待审核片段: [],
      影响力评分: 3, '身份与贡献': '旧身份', 简介: '旧简介',
    }],
  };
  const dataPath = path.join(output, 'merged_domain_encoded.json');
  await fs.writeFile(dataPath, `${JSON.stringify(source, null, 2)}\n`);
  const storePath = path.join(appDir, 'dataStore.js');
  let code = await fs.readFile(path.join(__dirname, 'dataStore.js'), 'utf8');
  code = code.replace("path.resolve(__dirname, '..', 'output', 'merged_domain_encoded.json')", `path.resolve(${JSON.stringify(dataPath)})`);
  code = code.replace("path.resolve(__dirname, '..', 'output', 'backups')", `path.resolve(${JSON.stringify(path.join(output, 'backups'))})`);
  await fs.writeFile(storePath, code);
  const store = require(storePath);
  try {
    const snapshot = await store.getData();
    const update = await store.updateRecord('sample', {
      '领域标签': ['文学与语言/诗歌'],
      author: '新作者',
      '影响力评分': 5,
      '身份与贡献': '新身份',
      简介: '新简介',
    }, snapshot.version);
    assert.deepEqual(update.record['领域编码'], [102]);
    assert.deepEqual(update.record['领域标签'], ['文学与语言/诗歌']);
    assert.equal(update.record['领域'], '诗歌');
    assert.equal(update.record.author, '新作者');
    assert.equal(update.record['影响力评分'], 5);
    assert.equal(update.record['身份与贡献'], '新身份');
    assert.equal(update.record['简介'], '新简介');
    assert.equal((await fs.readdir(path.join(output, 'backups'))).length, 1);
    const backupFiles = await fs.readdir(path.join(output, 'backups'));
    const backupJson = JSON.parse(await fs.readFile(path.join(output, 'backups', backupFiles[0]), 'utf8'));
    assert.deepEqual(backupJson.records[0]['领域编码'], [101]);

    await assert.rejects(() => store.updateRecord('sample', { url: 'https://evil.invalid' }, update.version), /不允许修改/);
    await assert.rejects(() => store.updateRecord('sample', { '影响力评分': 6 }, update.version), /评分必须/);
    await assert.rejects(() => store.updateRecord('sample', { '领域标签': ['不存在/标签'] }, update.version), /未知领域标签/);
    const after = await fs.readFile(dataPath);
    const staleVersion = crypto.createHash('sha256').update(after).digest('hex');
    await fs.appendFile(dataPath, ' ');
    await assert.rejects(() => store.updateRecord('sample', { '领域': 'anything' }, staleVersion), (error) => error.status === 409);
    console.log('DataStore isolated tests passed: taxonomy sync, backup-before-write, allowlist, invalid labels, stale-version conflict.');
  } finally {
    await fs.rm(temp, { recursive: true, force: true });
  }
}

run().catch((error) => { console.error(error); process.exitCode = 1; });
