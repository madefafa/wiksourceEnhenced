# Ask 预检：Kiwix HTTP OpenCC v11

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
workflow_version: "v11"
automa_version: "1.30.02"
state: ask-discussion
package_mode: source=unavailable
browser: unknown
page_scope: Kiwix viewer 域名下所有页面，具体域名范围待确认
permissions: Automa 页面脚本与 HTTP Request 权限，实际授权待确认
```

## 原始需求

修改现有 `Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v10.automa.json`，使其对域名下的所有内容生效，并创建新版本。

## 已确认事实

- `MEMORY.md` 不存在，项目记忆证据不可用。
- 当前目录无 `PLAN.md`、知识根索引、Block 源码或运行时记录；因此 source/runtime/feedback 证据不可用。
- v10 是 Automa `1.30.02` JSON，包含 Trigger、Active Tab、Delay、HTTP Request/Webhook、JavaScript、Stop Current 共 6 个节点。
- v10 的 URL 触发器仅覆盖：`http://192.168.*.*:8889/viewer` 的精确 viewer 路径，以及 `https://browse.library.kiwix.org/viewer` 的精确 viewer 路径。
- v10 JavaScript 使用 `context: website`，并通过 `iframe#articleIFrame, iframe#content_iframe` 查找内容 iframe；因此当前实现只在特定 viewer 页面和可识别 iframe 中处理内容。
- v10 HTTP Request 使用 Automa 扩展上下文下载 CDN 上的 OpenCC 源码，并通过变量 `openccSource` 传给 JavaScript；该外部依赖策略符合技能默认策略。

## 可行性评估

建议可行，但“域名下的所有内容”存在关键范围歧义：

1. 若含义是既有 Kiwix 域名下所有路径（不只 `/viewer`），应扩大 URL 触发器为域名级正则，并保留 `supportSPA: true`。
2. 若内容可能位于顶层文档、同源 iframe 或跨域 iframe，需要脚本增加文档/iframe 适配；跨域 iframe 不能直接读取，除非在 iframe 自身页面触发并具备匹配权限。
3. 若希望覆盖任意 Kiwix 域名，而不仅是现有两个域名，需要用户提供准确域名清单或确认使用通用域名正则。通用 `.*kiwix.*` 可能误匹配不安全站点，不建议默认采用。

## 风险与失败模式

- 扩大触发范围可能在 Kiwix 非内容页执行脚本，需脚本无目标时安全退出。
- URL 触发器扩大后，页面导航/SPA 更新可能重复执行；脚本应保持幂等并复用现有样式 ID、状态键。
- v10 节点边/句柄为导出资产事实，但没有知识根 JSON 契约可交叉验证；生成后只能做静态结构检查，不能宣称导入或运行已验证。
- 当前没有浏览器版本、实际域名、权限或反馈，因此不能完成 runtime verification。

## 推荐方案

以 v10 为唯一现有资产基线，创建 v11，不覆盖 v10：

- 工作流名称与节点 ID 改为 v11，保留 Automa `1.30.02`。
- URL 触发器扩大到用户确认的域名范围；默认候选为现有两个域名的“域名下所有路径”，即 `^http://192\\.168\\.[0-9]{1,3}\\.[0-9]{1,3}:8889(?:/|[?#].*)?$` 与 `^https://browse\\.library\\.kiwix\\.org(?:/|[?#].*)?$`。
- JavaScript 维持 HTTP Request 下载 OpenCC 的变量注入方式，增强目标文档查找的安全退出与幂等性，使无 viewer 内容时不报错。
- 新文件名：`Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json`。
- v10 保留为历史版本，v11 的静态校验报告记录旧版本与新版本差异。

## 必须由用户确认的关键决策

- “域名下所有内容”是否仅指现有两个域名的所有路径，还是还要增加其他 Kiwix 域名。
- 是否接受扩大触发范围后在该域名非 viewer 页面安全尝试并无目标时退出。

## 建议状态

`awaiting-user-input`：域名范围是生成安全正则的关键用户事实。用户确认后进入正式 plan/decision 和 JSON 生成流程。
