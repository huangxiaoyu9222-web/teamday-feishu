# GitHub 发布准备与验收记录

本文件用于区分「仓库可公开」与「某个飞书租户已连通」。源码公开不需要真实企业凭证；应用真实运行需要安装者在自己的飞书租户完成授权与投递验证。

## 发布质量标准

TeamDay 按独立开源产品交付：清楚的定位、可运行演示、中英指南、合成示例、自动化测试、CI、许可证、贡献和安全说明。项目源于 Jade 对一线业务信息回传与团队协作的原创工作流设想，当前聚焦飞书场景。

最新复验见 [中英验收记录](ACCEPTANCE.md)。完整使用与接入指南提供中英文版本；界面和生成草稿当前为中文。

## 公开仓库检查

- [x] 一句话定位、演示入口、真实模式说明、明确限制：`README.md`
- [x] 智能体入口与使用边界：`SKILL.md`
- [x] 合成样例及跨团队配置：`examples/`
- [x] 中文上手、飞书接入、架构和界面说明：`docs/`
- [x] 自动化测试及 GitHub Actions：`tests/`、`.github/workflows/check.yml`
- [x] 许可证、贡献指南、安全说明与版本记录
- [x] 密钥与运行数据排除：`.gitignore`、`.env.example`、`scripts/check_release.py`
- [x] 本地浏览器演示：按角色切换、午间卡片、编号生成成果、现场记录校准与确认
- [ ] 用户自己的飞书租户实测：待安装者填入应用凭证、授权及 `open_id`
- [ ] 真实模型供应商实测：待安装者配置模型服务并验证实际请求
- [ ] 第一个非作者团队连续试用：发布后收集反馈与真实可靠性数据

## 发布仓库时

建议仓库名称 `teamday-feishu`，一句话描述：`Your team’s next move, delivered in Feishu. Reviewed meeting notes → daily briefs → reply-to-run drafts.`。主题可设 `feishu`, `lark`, `ai-agent`, `daily-brief`, `team-operations`, `industrial-ai`。公开前先运行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py
git status --short
```

上传的是干净源码与示例，绝不上传 `.env`、`data/`、`config.json`、`config.demo.json`、`.venv/`。设置仓库首页链接后，可增加本地工作台截图或 60 秒演示视频；只展示合成数据。GitHub 仓库创建、远端推送、截图录制和真实租户授权由仓库所有者安排。

首次公开发布时，先在 GitHub 创建**空仓库** `teamday-feishu`（不要勾选自动生成 README、许可证或 `.gitignore`），再在本项目目录执行下面的命令。将占位符替换为自己的 GitHub 用户名；Git 作者姓名和邮箱请先按自己的身份配置。推送前再检查一次 `git status --short` 和 `git ls-files`。

```bash
git config user.name "你的 Git 作者姓名"
git config user.email "你的 Git 作者邮箱"
git commit -m "Initial release v0.1.0"
git remote add origin https://github.com/<你的用户名>/teamday-feishu.git
git push -u origin main
git tag v0.1.0
git push origin v0.1.0
```

若使用网页上传，应只上传本仓库被 Git 跟踪的源码文件，不要把运行过的整个目录拖进 GitHub。附带的 ZIP 是交付与体验包；公开仓库请以上面的 Git 提交流程为准。

第一版标签建议 `v0.1.0`。发布说明应明确：编号任务目前生成 Markdown 草稿；新闻候选未独立交叉验证；日历与录音硬件尚未直连。记录真实试用者发现的问题，按实际使用数据决定下一版。
