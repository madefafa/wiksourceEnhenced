# Ask 预检：Kiwix HTTP OpenCC v12 iframe 浮动菜单修复

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v12.automa.json"
workflow_version: "v12"
automa_version: "1.30.02"
state: awaiting-user-decision
source_asset: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
```

## 用户反馈

在 iframe 穿透页面 `http://localhost:8889/content/aaa65f7e-af66-95a6-6f37-7ca124589b9f/Author%3A%E4%B9%A0%E8%BF%91%E5%B9%B3` 中，繁简/CSS 处理可能执行，但没有显示浮动 dropdown。

## 根因判断

v11 JavaScript 使用 `context: website`，但 `getFrame()` 只查找父页面中的 `iframe#articleIFrame, iframe#content_iframe`；对直接打开的 `/content/...` 页面，`document` 本身就是内容文档，因此 `getDoc()` 返回 null，`render()` 提前返回。浮动按钮创建逻辑虽然位于后面，但 v11 的页面形态兼容不足，且面板固定在当前执行文档。

## v12 修复建议

- 保留 v11，不覆盖历史资产。
- 创建 v12，兼容两种页面形态：
  1. viewer 外壳 + 内容 iframe：处理 iframe 文档，浮动按钮挂载到外壳文档。
  2. 直接 `/content/...` 内容页：将当前 `document` 作为内容文档，同时将浮动按钮挂载到当前文档。
- 将 `getDoc()` 改为：优先匹配可访问的目标 iframe；没有 iframe 或 iframe 文档不可用时回退到当前 `document`。
- 将浮动按钮和 dropdown 的挂载逻辑抽象为 `getUiDoc()`，确保 UI 始终添加到当前可见页面文档，而不是只添加到内容 iframe。
- 在直接内容页使用当前文档的 `body`/`documentElement`，并保留 `position: fixed` 与高 z-index。
- 对 iframe `load` 和 SPA 内容变化继续重新渲染；避免重复创建按钮和面板。

## 风险

- 跨域 iframe 仍受浏览器同源策略限制；若无法读取 `contentDocument`，只能处理外壳或当前页面可访问文档。
- 当前没有浏览器导入/运行反馈，因此 v12 生成后只能静态验证，不能宣称已修复运行问题。

## 推荐

建议批准后生成 v12；这是基于 v11 的兼容性修复，不改变 OpenCC 下载策略和现有 CSS/转换开关。
