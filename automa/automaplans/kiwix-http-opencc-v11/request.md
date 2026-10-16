# Request

```yaml
request_id: kiwix-http-opencc-v11
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
workflow_version: "v11"
automa_version: "1.30.02"
source_asset: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v10.automa.json"
collision_check: passed; target asset did not exist at request initialization
state: awaiting-user-input
```

## 用户原始请求

Command `automa` 修改 `Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v10.automa.json`，对域名下的所有内容生效，创建新版本。

## 规范化验收标准

1. v10 不被覆盖，生成独立的 v11 JSON。
2. Automa 基线保持 `1.30.02`。
3. URL 触发范围从精确 `/viewer` 页面扩大到确认域名下的所有路径。
4. Kiwix 内容不存在或页面结构不匹配时，脚本安全退出，不阻塞工作流。
5. OpenCC 继续由 Automa HTTP Request 下载并通过变量注入脚本。
6. JSON 可解析，节点 ID 唯一，边引用存在，节点可从 trigger 到 stop-current 到达。
7. 未进行浏览器导入/运行前，不宣称 runtime verified。

## 关键未知

- 需要覆盖的完整域名清单尚未由用户确认。
- 当前无浏览器、权限、页面和运行反馈。
- `MEMORY.md`、`PLAN.md`、知识根索引及源码证据不存在。
