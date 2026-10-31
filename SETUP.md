# 设置与运行

零第三方依赖，无需安装任何包。

## 环境要求

- Python 3.8+（标准库：json / os / re / sys / time）

## 快速验证

```bash
# 在项目根目录
python run_tests.py        # 验收断言，期望 PASS 13 / FAIL 0
python demo.py             # 工作流演示，期望退出码 0
```

## 在自己的代码中使用

```python
from social_pipeline import SocialPipeline

pipe = SocialPipeline("examples")

# 生成当日草稿（按计划 2-3 条）
drafts = pipe.generate_drafts("2026-10-31")

# 人工审核（拒绝 / 通过）
pipe.moderate(drafts[0], approved=False)
pipe.moderate(drafts[1], approved=True)

# 模拟发布（未审核草稿会抛 PipelineError）
rec = pipe.publish(drafts[1], simulate=True)
print(rec)

# 失败重试
rec2 = pipe.publish(drafts[1], fail_once=True)

# 数据反馈
print(pipe.feedback())
```

## 接入真实平台

本样例**不向真实账号自动发布**。如需实装：
- 在 `workflow.accounts[].authorized=true` 前完成平台授权；
- 为 facebook/instagram/tiktok 编写 external adapter（替换
  `publish(simulate=True)` 的分支）；
- 保持人工审核门不变（`human_in_loop=true`）。

## 常见问题

- **每天几条草稿？** `publish_plan.daily_min/daily_max`（默认 2-3）。
- **为什么模拟发布？** 避免未经授权自动发布；真实 API 需 adapter 与
  授权，属于落地阶段而非本样例范围。
- **Windows 中文乱码？** 脚本已内置 UTF-8 重配置。