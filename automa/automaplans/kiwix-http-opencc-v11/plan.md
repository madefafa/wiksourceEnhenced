# Plan v1

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
workflow_version: "v11"
automa_version: "1.30.02"
source_asset: "../../Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v10.automa.json"
status: awaiting-user-decision
```

## 方案

1. 深拷贝 v10 JSON，保留 top-level `extVersion`、`version`、`settings`、`globalData`、`drawflow` 等原生字段。
2. 生成新文件 `Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json`，不覆盖 v10。
3. 将工作流名称、节点 ID、边 ID/class、脚本内部版本标识改为 v11，保持节点布局与标准 Block 类型。
4. 将 URL trigger 从精确 `/viewer` 改为用户确认域名下全路径匹配；保留 `supportSPA: true`。
5. 对 JavaScript 做最小安全增强：无内容 iframe/main 时安全结束；保留幂等样式 ID、状态存储和 `automaNextBlock()`。
6. 保留 HTTP Request 的 CDN + Automa 变量策略：GET `opencc-js@1.0.5`，变量名 `openccSource`。
7. 对 JSON 执行静态检查：解析、顶层版本、节点唯一性、边引用、句柄引用、可达性、无重叠位置、v10 未改写。
8. 输出导入测试说明，但仅在用户实际导入后记录 `imported/recognition-tested`，仅在浏览器运行反馈后记录 `verified`。

## 默认候选域名范围

仅在用户确认后采用：

- `http://192.168.*.*:8889` 域名/主机下所有路径。
- `https://browse.library.kiwix.org` 域名下所有路径。

若用户确认其他域名，替换为明确、逐域名的正则，不使用宽泛的 `.*kiwix.*`。

## 失败与回滚

- 域名范围未确认：保持 `awaiting-user-input`，不生成 JSON。
- 静态校验失败：保留失败资产，创建 v11 修订版本，不覆盖历史文件。
- 导入或运行失败：记录反馈后按 JSON -> category -> documentation -> source -> runtime 顺序排查；修复后回到 testing。
- 三次同一错误修复失败：停止修改，记录 blocked。

## 预期文件

- `request.md`
- `ask.md`
- `context-brief.md`
- `block-contracts.md`
- `intent.md`
- `plan.md`
- `decision.md`
- `validation.md`
- `feedback.md`
- `troubleshooting.md`
- `lessons.md`
- `pending-knowledge-sync.md`
- `acceptance.md`
- 获批后：`workflow.json`（请求目录内副本）与项目根目录 v11 工作流资产
