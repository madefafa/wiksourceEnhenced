# Acceptance

```yaml
case_id: static-v12-json
scenario: v12 静态结构与兼容逻辑
input: 根目录 v12 JSON
version_browser: Automa 1.30.02; browser unknown
expected: JSON、节点、边、UI 宿主和 iframe 回退检查通过
actual: 通过
runtime_status: pass
evidence: ["validation.md", "../../Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v12.automa.json"]
executed_at: "2026-10-16T03:22:00+08:00"
blocking_reason: none
next_step: 在 Automa 中导入并测试直接 /content 与 viewer iframe 页面
```

```yaml
case_id: direct-content-v12
scenario: 直接 /content 页面浮动 dropdown
input: http://localhost:8889/content/aaa65f7e-af66-95a6-6f37-7ca124589b9f/Author%3A%E4%B9%A0%E8%BF%91%E5%B9%B3
version_browser: Automa 1.30.02; browser unknown
expected: 页面显示“渲染选项”浮动按钮，点击出现 dropdown
actual: not-run
runtime_status: not-run
evidence: ["validation.md"]
executed_at: not-run
blocking_reason: 尚未获得浏览器运行反馈
next_step: 导入 v12 后打开指定 URL 测试
```

```yaml
case_id: viewer-iframe-v12
scenario: viewer iframe 内容与浮动 dropdown
input: 两个已批准 Kiwix 域名下的 viewer 页面
version_browser: Automa 1.30.02; browser unknown
expected: iframe 内容处理正常，浮动 dropdown 可见
actual: not-run
runtime_status: not-run
evidence: ["validation.md"]
executed_at: not-run
blocking_reason: 尚未获得浏览器运行反馈
next_step: 导入 v12 后测试 viewer 页面
```

```yaml
case_id: localhost-auto-trigger-v12-r2
scenario: localhost 直接 content 页面自动触发 dropdown
input: http://localhost:8889/content/aaa65f7e-af66-95a6-6f37-7ca124589b9f/Author%3A%E4%B9%A0%E8%BF%91%E5%B9%B3
version_browser: Automa 1.30.02; browser unknown
expected: 访问页面后自动执行工作流并显示“渲染选项”浮动按钮，点击后出现 dropdown
actual: not-run
runtime_status: not-run
evidence: ["validation.md", "../../Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v12.automa.json"]
executed_at: not-run
blocking_reason: 修改后尚未重新加载工作流并获得浏览器反馈
next_step: 在 Automa 中重新导入/刷新现有 v12，再访问指定 localhost 页面
```
