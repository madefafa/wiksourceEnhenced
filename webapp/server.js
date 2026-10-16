const path = require('node:path');
const express = require('express');
const { getData, updateRecord } = require('./dataStore');

const app = express();
const port = Number(process.env.PORT) || 4173;
const publicDir = path.join(__dirname, 'public');

app.disable('x-powered-by');
app.use(express.json({ limit: '32kb' }));
app.use('/vendor/bootstrap', express.static(path.join(__dirname, 'node_modules', 'bootstrap', 'dist'), { fallthrough: false, immutable: true, maxAge: '1d' }));
app.use(express.static(publicDir, { extensions: ['html'] }));

app.get('/api/health', async (_req, res) => {
  try {
    const snapshot = await getData();
    res.json({ status: 'ok', records: snapshot.data.records.length, version: snapshot.version });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/records', async (_req, res) => {
  try {
    const snapshot = await getData();
    res.json({ metadata: snapshot.data.metadata, records: snapshot.data.records, catalog: snapshot.catalog, version: snapshot.version });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.patch('/api/records/:id', async (req, res) => {
  try {
    const { patch, version } = req.body || {};
    if (typeof version !== 'string' || !/^[a-f0-9]{64}$/.test(version)) {
      return res.status(400).json({ error: '缺少有效的数据版本标识' });
    }
    const result = await updateRecord(req.params.id, patch, version);
    res.json(result);
  } catch (error) {
    res.status(error.status || 400).json({ error: error.message });
  }
});

app.use((error, _req, res, _next) => {
  if (error instanceof SyntaxError && 'body' in error) return res.status(400).json({ error: '请求 JSON 格式无效' });
  if (error.status === 413) return res.status(413).json({ error: '请求内容过大' });
  console.error(error);
  return res.status(500).json({ error: '服务器内部错误' });
});

app.listen(port, '127.0.0.1', () => {
  console.log(`Author browser listening at http://127.0.0.1:${port}`);
});
