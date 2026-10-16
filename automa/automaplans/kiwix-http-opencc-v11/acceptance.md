# Acceptance

```yaml
case_id: static-v11-json
scenario: v11 静态结构检查
input: 根目录 v11 JSON
version_browser: Automa 1.30.02; browser unknown
expected: JSON、节点、边、触发范围通过静态检查
actual: 通过
runtime_status: pass
evidence: ["validation.md", "../../Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"]
executed_at: "2026-10-16T03:12:00+08:00"
blocking_reason: none
next_step: 在 Automa 中导入并执行浏览器测试
```

```yaml
case_id: import-recognition-v11
scenario: Automa 导入识别
input: v11 JSON
version_browser: Automa 1.30.02; browser unknown
expected: 每个节点标题、图标、参数、handles 正常识别
actual: not-run
runtime_status: not-run
evidence: ["validation.md"]
executed_at: not-run
blocking_reason: 尚未进行浏览器端导入
next_step: 导入 v11 并逐节点核对
```

```yaml
case_id: runtime-all-paths-v11
scenario: 两个确认域名下任意路径运行
input: Kiwix 页面 URL
version_browser: Automa 1.30.02; browser unknown
expected: OpenCC/CSS 对目标内容生效，无目标页面安全退出
actual: not-run
runtime_status: not-run
evidence: ["validation.md"]
executed_at: not-run
blocking_reason: 尚无浏览器运行反馈
next_step: 在两个范围内分别测试内容页和非 viewer 页
```
