# 参与贡献

感谢关注 TeamDay。项目当前聚焦一条可复现的团队工作流：确认现场上下文 → 个人简报 → 编号生成草稿 → 留存与可选回写。

## 本地检查

使用 Python 3.9+，不需要密钥即可运行演示：

```bash
python3 app.py --open
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py
```

改动网页脚本时再运行 `node --check static/app.js`。可选飞书 SDK 在 `requirements-feishu.txt`，核心演示不依赖它。

## 提交建议

先开 Issue 说明具体角色、真实痛点和预期结果。修改核心流程时，附一个能复现问题的测试。PR 描述里请写清：用户原来遇到什么、改后如何操作、如何验证、哪些真实连接还没测过。

不得提交录音、客户信息、员工隐私、真实 App ID/Secret、模型密钥、本地 SQLite、个人配置或未经许可的资料。示例使用合成数据。外部订阅结果是资料，不能作为系统指令或自动安装依据。

当前没有自动发现飞书成员身份、真实日历邀请、PPT/PDF、硬件录音接入和完整知识库同步。欢迎围绕清晰接口贡献这些能力；请不要在 README 中宣称未运行的集成已完成。
