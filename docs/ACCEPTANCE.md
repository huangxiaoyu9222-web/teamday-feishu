# v0.1.0 发布前复验 / Release acceptance

日期：2026-10-30。定位：**可公开发布的早期预览版本**。本记录不是对所有环境或未来模型输出的无错误保证。

## 验收范围 / Scope

- 自动化测试覆盖知识确认、成员归属、原文保留、重复执行、失败重试、快照有效性、定时窗口、RSS 解析、HTTP 来源与 CSRF、发布边界。
- 新增回归：预先打开的简报在定时首次发送前更新；旧私人记录产生的待办不会漏入共享表格；无行动时不提示执行不存在的编号。
- 本地 HTTP 协议模拟：真实 HTTP 请求序列化 → 模型校准建议 → 人工确认 → 飞书投递 → 数字指令 → 模型草稿 → SQLite 成果 → 多维表格回写；重复事件不增加请求与成果。模拟服务不是实际供应商或飞书租户。
- 浏览器合成数据实测：编号生成及草稿内容、人工确认门槛、待办保存、更新后的上下文、早间/午间切换、私人记录不显示给另一成员、设置保存、信息源表单、未提交输入在页面切换时保留。
- 视觉检查：1280×720 桌面界面；截图 `images/demo.png`。小屏有 CSS 适配，但本轮没有实机手机验收。
- 文档：README、完整使用指南、飞书接入均提供独立中英文版本和互链；当前应用界面与模型草稿为中文，英文指南提供标签映射。
- 安装：macOS 双击演示脚本；真实模式启动脚本首次生成 `.env`，下次自动准备 `.venv` 与固定版本官方 SDK。Python、组织应用审批、凭证与成员 open_id 仍为前置条件。

## 输出检查 / Output review

核对了原文与校准文本分别保留；未经确认的草稿不进入知识；采购人、采购承诺、日期与负责人不被程序自动推断；合成案例与今日新闻明确区分；生成成果标识为草稿。演示产品评估模板已移除固定客户问题断言，避免给不同项目套上“经验依赖”的结论。真实模型输出仍需人工审阅，系统提示不能构成事实准确率保证。

后续生成任务只传入已确认的校正文和摘要，不再混入原始误识别人名；原文仍保存在本地审计记录。

Raw transcripts and reviewed corrections remain separate. Subsequent generation uses confirmed corrections and summaries rather than noisy raw transcripts. Draft notes do not become confirmed knowledge. Unconfirmed decisions, owners, dates and commitments must remain uncertain. Demo references are labeled as references, not current news. Model output remains a human-reviewable draft; prompt constraints cannot guarantee factual accuracy.

## 发布与真实接入的区别 / Release vs. live readiness

可发布源码、示例、测试、双语文档与可运行演示。尚未连接安装者的真实模型和飞书租户，因此**不宣称真实企业全流程已验收**。发布说明必须保留权限配置、持续运行、信息候选未独立核验、日历/录音硬件未直连等限制。

The source release and synthetic demo are reproducible. Real model-provider connectivity, app permissions, WebSocket event delivery, member binding, actual Feishu receipt and actual Bitable writes must be validated in the installer's tenant. There are no real credentials or company records in the release package.

首次真实接入按顺序验证：模型生成一份草稿 → 单成员明确发送 → 飞书数字回复 → 可选表格回写 → 最后开启定时。使用 [中文接入指南](FEISHU.md) / [English setup](FEISHU.en.md)。

## 本轮结果 / Results

Python 3.9.6 与 Python 3.12.14 分别运行 **35 项测试，全部通过**。Python 编译、JavaScript 语法、zsh 启动脚本语法、发布文件与本地文档链接检查通过。干净 ZIP 重新解压后再次通过 35 项测试，并实测独立启动、健康检查、生成、下载、重复实例拦截与缺少凭证时的双语提示。全新虚拟环境完成固定版本飞书 SDK 安装、依赖检查和导入。系统 Python 3.9.6 的 SDK 导入有 LibreSSL 兼容性警告，未阻断导入；真实网络连接仍待租户验收。GitHub 远端 CI 尚未运行。

## 可复现命令 / Reproduce

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q app.py teamday tests
node --check static/app.js
python3 scripts/check_release.py
```

GitHub Actions 已配置 Python 3.9 / 3.12 矩阵，但远端任务需要首次推送后执行。ZIP 从 Git 跟踪文件生成；凭证、运行数据库、团队配置和虚拟环境不入包。
