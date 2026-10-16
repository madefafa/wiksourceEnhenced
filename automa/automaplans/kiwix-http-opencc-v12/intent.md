# Intent

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v12.automa.json"
workflow_version: "v12"
automa_version: "1.30.02"
```

目标是修复直接 Kiwix `/content/...` 页面没有浮动 dropdown 的问题。执行链保持 `trigger -> active-tab -> delay -> webhook -> javascript-code -> stop-current`。核心变更是内容文档与 UI 文档解耦：iframe 页面内容在 iframe 文档处理，UI 在外壳文档；直接内容页内容和 UI 都在当前文档。
