# Request

```yaml
request_id: kiwix-http-opencc-v12
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v12.automa.json"
workflow_version: "v12"
automa_version: "1.30.02"
source_asset: "../Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
state: awaiting-user-decision
```

## Acceptance

1. v11 保留不变。
2. v12 对 iframe viewer 和直接 `/content/...` 页面均能确定内容文档。
3. 浮动按钮与 dropdown 挂载到当前可见 UI 文档，并保持幂等。
4. OpenCC HTTP Request、变量 `openccSource`、CSS 开关逻辑保持。
5. JSON 静态结构检查通过；浏览器运行状态在反馈前为 not-run。
