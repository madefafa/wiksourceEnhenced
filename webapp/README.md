# 历史作者资料检索

本地 Node.js + Express + 原生 HTML/CSS/JavaScript 应用，使用 Bootstrap 5 渲染 `../output/merged_domain_encoded.json`。

## 启动

首次使用，在 `webapp` 目录安装依赖：

```sh
npm install
```

macOS Finder 中双击 `start.command` 即可启动服务并打开浏览器；也可在终端执行：

```sh
npm run start:mac
```

默认地址为 http://127.0.0.1:4173 。若服务已在运行，启动器只会复用服务并打开页面，不会重复启动。终端方式可用 `PORT=4174 npm run start:mac` 指定其他端口。

停止由启动器启动的服务，可双击 `stop.command` 或执行 `npm run stop:mac`。启动日志和 PID 文件放在 `.runtime/`，勿手动删除运行中的 PID 文件。

传统方式仍可执行 `npm start`；该方式在前台运行，按 `Ctrl+C` 停止。

## 功能

- 按朝代 ID 区间、领域一级/二级标签、作者姓名和待审核状态筛选。
- 表格显示作者、朝代、领域标签、评分、身份与贡献、领域原文及简介；窄屏将每条记录显示为字段卡片，页面不需要横向滚动。
- 点击表头或全局排序控件对全部筛选结果排序后再分页；按住 Shift 点击表头可添加组合排序条件，排序状态保存在浏览器本地。
- 支持分页、跳页和每页 20/50/100 条。
- 行内编辑作者、朝代、领域标签、评分、身份与贡献、领域原文及简介。朝代字段从现有数据中的完整元组选择；领域编码由标签映射生成。
- 作者名链接默认将 `192.168.10.26` 替换为 `localhost`；启用检索栏的 Web 模式后，按 `https://{host}/viewer#{version}/{文章路径}` 导航到在线 Kiwix viewer。两种模式均在新页面打开，Web host/version 保存在浏览器本地；悬停作者名显示备注。
- 每次成功编辑前自动备份至 `../output/backups/`，再通过临时文件原子替换数据文件。
- 页面及 API 仅绑定 `127.0.0.1`，适用于本机使用，不应未经鉴权直接暴露到公网。

## 校验

```sh
npm run check
npm test
```

测试使用临时目录中的样例 JSON，不会写入正式数据文件。
