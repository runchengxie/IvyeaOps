# 0033 — 任务台产物按 id 寻址，路径永不来自前端

- 状态：已采纳
- 日期：2026-09-10

## 背景

任务台右侧产物栏此前只画得出「Agent 改过哪些文件」的名字和 diff：点不动、下不了、
看不了。用户跑完一个生成报表的任务，下一步想做的事是**把那份报表拿走**，
而唯一的路是 ssh 上去 scp。

要接这条路，绕不开两个问题：

1. 文件在**磁盘上**（`file_change` 事件给的是 agent 侧的绝对路径），
   而 agent 的 `policy.file_write_roots` 默认是空的 —— 它能写的地方没有边界。
   所以"允许下载哪些路径"不能指望 agent 那边的策略。
2. 产物索引此前只活在**发起那一轮的那个标签页的内存里**。Console 恢复历史会话时
   会把它清空，所以刷新一次、或者第二天回来，列表就是空的。

## 决定

### 一、只接受 id，不接受路径

端点是 `/console/files/{id}/raw` 与 `/console/files/{id}/text`，
`id = sha1(session_id + "\0" + path)[:16]`，路径从库里查。

**用户输入永远不进文件系统** —— `../../etc/passwd` 这类穿越不是被过滤掉的，
而是根本没有入口。授权是"这条 id 对应的会话属于你"（admin 除外）。

至于"这个用户凭什么能拿这个文件"：文件正是 agent **按他自己的指令**写出来的，
他本来就能让 agent `read_file` 把内容打印出来。这个端点不扩大信任边界，
只是省掉一次往返。

越权与不存在**返回同样的 404 和同样的文案**：区分了就等于确认"这个 id 存在，
只是不归你"，那是一个可以拿来枚举别人会话的信号。

### 二、索引落库，但不复制文件

新表 `console_files(id, session_id, principal, path, name, action, changes, …)`，
在 SSE 转发时从 `file_change` 事件捞。

**只记路径，不存副本**：产物可能是几十 MB 的表格或图片，再存一份既费盘、也会立刻
和真实文件不同步。大小 / 修改时间 / 还在不在都是**取用时现场 stat** ——
文件被删了就如实说"已不在"，不拿旧值画一个点了会报错的下载按钮。

`/chat/sessions/{id}/live`（关掉页面再回来接流）也要记：发起那一轮的标签页一旦关掉，
`_tee_session_events` 的生成器就被关了，之后写的文件一条都记不上 ——
而"关了页面回头来拿文件"恰恰是最常见的用法。落库是幂等的，两条流并行记不会重复。

### 三、text/html 永远不 inline

产物里可能有 .html / .svg。在自己的域上 inline 渲染它，等于执行别人生成的脚本。

- 下载：`application/octet-stream` + `Content-Disposition: attachment`，浏览器只会存盘。
- 预览：只对**图片 / PDF** 放行 inline，并统一带
  `Content-Security-Policy: sandbox`（不给 allow-scripts）与 `X-Content-Type-Options: nosniff`。
- **HTML 走文本通道**：服务端只返回字符串，前端塞进
  `sandbox="allow-same-origin"`（不给 `allow-scripts`）的 iframe `srcdoc`，
  再往里注入一条 `<meta CSP default-src 'none'>` —— 预览**不联网**，
  一份报表不该因为被看了一眼就把"谁在什么时候看了"发给第三方。

  ⚠️ 不能写成 `sandbox=""`：Chromium 不给不透明来源的 srcdoc 建子帧，结果是
  **整片空白**（元素在、尺寸对、内容不存在）。这个坑在 IvyeaNote 上踩过一次。

- svg 在 inline 白名单里，但理由要写清楚：svg 能带脚本，可它**只在被当作文档加载时
  才跑**；预览器用的是 `<img>`，那条路按规范就不执行脚本。叠一层 `CSP: sandbox`
  是为了堵住"有人把 raw 地址粘到地址栏"那条路。

## 代价

- 不是"工作区文件浏览器"：只有走 `write_file` / `edit_file` 的产物会进列表，
  用 bash 重定向出来的文件不在其中（agent 不为它们发 `file_change`）。
- 预览文本上限 512KB，超了截断并在界面上标明。
- csv 预览不做完整 RFC 4180 解析（引号里带逗号会切错）—— 那是预览，不是导入；
  要精确读就下载下来用表格软件打开。

## 相关

- [0028](./0028-you-can-talk-to-a-running-turn.md) —— 接进正在跑的那一轮（这里复用了它的接流口）
- `src/server/tests/test_console_files.py` —— 越权、不 inline、现场 stat 都有用例钉着
