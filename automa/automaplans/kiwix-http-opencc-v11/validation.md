# Validation

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
workflow_version: "v11"
automa_version: "1.30.02"
status: static-validated
```

| 检查 | 结果 | 说明 |
|---|---|---|
| JSON 解析 | pass | Python JSON parser 成功 |
| Automa 版本 | pass | `extVersion`/`version` 均为 `1.30.02` |
| 节点 ID 唯一 | pass | 6 个节点唯一 |
| 边引用 | pass | 5 条边的 source/target 均存在 |
| 几何位置 | pass | 节点位置唯一，无负坐标 |
| 触发范围 | pass | 两个触发器覆盖确认主机/域名所有路径 |
| OpenCC 依赖 | pass | HTTP Request GET CDN，变量 `openccSource` 保留 |
| v10 保留 | pass | v10 文件未覆盖，v11 独立创建 |
| 导入识别 | not-run | 尚未在 Automa 中导入；不能声明识别通过 |
| 浏览器运行 | not-run | 未提供浏览器/页面反馈；不能声明 runtime verified |
| 视觉效果 | not-run | 需在导入和运行后验证 |

布局、边和版本结构为静态检查结果；导入成功、执行成功、视觉效果成功三者尚未等价证明。
