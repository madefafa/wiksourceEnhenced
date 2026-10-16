# Validation

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v12.automa.json"
workflow_version: "v12"
automa_version: "1.30.02"
status: static-validated
source_asset: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
```

| 检查 | 结果 | 说明 |
|---|---|---|
| JSON 解析 | pass | Python JSON parser 成功 |
| Automa 版本 | pass | `extVersion`/`version` 均为 `1.30.02` |
| 节点 ID 唯一 | pass | 6 个节点唯一 |
| 边引用 | pass | 5 条边 source/target 均存在 |
| 几何位置 | pass | 节点位置唯一、无负坐标 |
| iframe 内容回退 | pass | 可访问目标 iframe 优先，否则回退当前 `document` |
| 浮动 UI 宿主 | pass | panel/button 使用当前 `uiDoc` 创建并挂载 |
| OpenCC 依赖 | pass | HTTP Request 与 `openccSource` 保持 |
| v11 保留 | pass | v11 未覆盖，v12 独立创建 |
| Automa 导入识别 | not-run | 尚未在浏览器中导入 |
| 直接 `/content/...` 运行 | not-run | 待用户实际页面测试 |
| viewer iframe 运行 | not-run | 待用户实际页面测试 |

静态通过不等于导入、执行或视觉效果已验证。

## v12 追加修复：localhost 自动触发

- 用户反馈：直接 `/content/...` 页面手动触发可显示 dropdown，但自动触发未执行。
- 根因：v12 原有 URL triggers 未包含 `http://localhost:8889`，因此自动触发器不匹配。
- 修复：在现有 v12 增加 `visit-kiwix-localhost-8889-all-paths-v1`，匹配 `^http://localhost:8889(?:/.*)?(?:[?#].*)?$`，不创建新工作流版本。
- 静态结果：pass；3 个 URL triggers，5 条边，6 个节点，Automa `1.30.02`。
- 浏览器运行：not-run，待重新加载已修改的 v12 并访问指定页面。
