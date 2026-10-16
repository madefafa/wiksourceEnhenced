const assert = require('node:assert/strict');
const { buildAuthorUrl } = require('./public/url-utils');

const local = 'http://192.168.10.26:8889/content/aaa65f7e-af66-95a6-6f37-7ca124589b9f/Author%3A%E8%83%A1%E9%81%A9';
assert.equal(
  buildAuthorUrl(local, false, 'browse.library.kiwix.org', 'wikisource_zh_all_nopic_2026-06'),
  'http://localhost:8889/content/aaa65f7e-af66-95a6-6f37-7ca124589b9f/Author%3A%E8%83%A1%E9%81%A9',
);
assert.equal(
  buildAuthorUrl(local, true, 'browse.library.kiwix.org', 'wikisource_zh_all_nopic_2026-06'),
  'https://browse.library.kiwix.org/viewer#wikisource_zh_all_nopic_2026-06/Author%3A%E8%83%A1%E9%81%A9',
);
assert.equal(buildAuthorUrl(local, true, 'https://evil.invalid/path', 'version'), '');
assert.equal(buildAuthorUrl(local, true, 'browse.library.kiwix.org', '../version'), '');
assert.equal(buildAuthorUrl('javascript:alert(1)', true, 'browse.library.kiwix.org', 'version'), '');
console.log('Author URL tests passed: local, web viewer, and invalid input cases.');
