# Intent

```yaml
workflow_file: "Kiwix：HTTP Request 下载 OpenCC + CSS 繁简样式优化-v11.automa.json"
workflow_version: "v11"
automa_version: "1.30.02"
state: awaiting-user-input
```

## 目标

基于 v10 创建 v11，使 OpenCC 繁简转换和 CSS 阅读样式优化在确认的 Kiwix 域名下所有路径生效，而不是只匹配 `/viewer` 精确路径。

## 输入与输出

- 输入：浏览器访问确认域名下任意路径；Automa HTTP Request 返回 OpenCC UMD 源码。
- 中间状态：变量 `openccSource` 传入 website-context JavaScript。
- 输出：目标内容文档被幂等地转换/注入样式；无目标文档时安全结束。
- 终点：`stop-current` 节点。

## 计划结构

`trigger -> active-tab -> delay -> webhook(HTTP GET OpenCC) -> javascript-code -> stop-current`

## 范围与约束

- 必须新建 v11 文件，不覆盖 v10。
- 外部依赖继续使用 Automa HTTP Request/Webhook，而不是页面脚本直接 fetch CDN。
- 仅修改触发器范围、脚本版本标识/选择器安全性及必要的 v11 标识；不改变既有 OpenCC/CSS 功能意图。
- 需要用户确认域名清单后才能锁定 URL 正则。

## 证据矩阵

| 断言 | 文档 | source | JSON | runtime | feedback | freshness |
|---|---|---|---|---|---|---|
| v10 是 Automa 1.30.02 导出结构 | unavailable | unavailable | confirmed | unavailable | unavailable | current |
| HTTP Request 下载 OpenCC 并保存变量 | unavailable | unavailable | confirmed | unavailable | unavailable | current |
| v10 只匹配两个 `/viewer` URL | unavailable | unavailable | confirmed | unavailable | unavailable | current |
| v11 可覆盖域名下所有内容 | unavailable | unavailable | partial | unavailable | unavailable | unknown |

## 非目标

- 不增加新的第三方依赖。
- 不保证跨域 iframe 内部内容可被父页面访问。
- 不在没有用户确认和浏览器反馈时宣称导入成功或运行成功。
