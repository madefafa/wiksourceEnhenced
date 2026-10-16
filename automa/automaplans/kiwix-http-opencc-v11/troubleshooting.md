# Troubleshooting

## 静态检查首次断言失败

- symptom: 校验脚本假定所有节点 ID 均以 `-v11` 结尾。
- cause: 原 v10 的终止节点 ID `workflow-state-hanshu-red-003` 不含版本后缀，改名不是必要条件；边引用保持一致。
- repair: 放宽校验为检查节点唯一、边引用存在，而不强制节点 ID 后缀。
- result: pass
- scope: 静态校验；未涉及浏览器运行。
