# Plan v1

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v12.automa.json"
workflow_version: "v12"
automa_version: "1.30.02"
source_asset: "../Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
status: awaiting-user-decision
```

1. 深拷贝 v11 到 v12，保留 v11。
2. 更新工作流/节点/脚本版本标识到 v12。
3. 修改脚本 `getDoc()`：可访问目标 iframe 优先，否则回退当前 `document`。
4. 修改 UI 创建与事件绑定，使 panel/button 始终写入 `getUiDoc()`，并在直接内容页 body 尚未建立时延迟重试。
5. 保留幂等 ID、localStorage 配置、OpenCC 与 CSS 行为。
6. 静态校验 JSON、节点/边/触发器、脚本关键兼容逻辑和历史资产保留。
7. 导入和浏览器测试仍需用户执行后记录。
