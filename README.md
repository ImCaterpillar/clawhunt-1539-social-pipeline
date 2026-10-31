# 海外社媒矩阵 AI 获客工作流样例（模拟发布）

对应 ClawHunt 任务 **#1539**（预算 $50，外贸社媒获客样例）。

**验收标准**：可演示流程、输入素材及输出示例、账号授权与人工审核步骤、
发布失败恢复和数据反馈说明、运行成本口径。

## 一条命令验证全部

```bash
python run_tests.py      # -> PASS 13 / FAIL 0
python demo.py           # -> 草稿→审核→模拟发布→反馈→成本
```

## 验收三要素（与验收标准逐条对应）

**① 核心实现路径**
`schema/workflow.schema.json` —— 多平台获客工作流配置（draft-07）；
`social_pipeline.py` —— `SocialPipeline`（素材→草稿→审核→模拟发布→
失败恢复→数据反馈，零依赖）。

**② 输入素材及输出示例路径**
`examples/materials.json` —— 5 条脱敏素材（工艺/C2M/IP/木家具/报价）；
`run_tests.py` / `demo.py` 输出草稿、审核结果、发布记录、反馈与成本。

**③ 关键流程：运行命令 + 预期输出**

```bash
python run_tests.py
# ✅ 3. multi-platform support -- facebook/instagram/tiktok
# ✅ 4. generate 2-3 drafts per day -- drafts=3
# ✅ 5. human moderation can reject
# ✅ 6. unreviewed draft blocked from publish
# ✅ 8. publish failure recovery (retry) -- records=[1, 2]
# ✅ 10. cost model dev/ops separated + USD
# Result: PASS 13   FAIL 0
```

覆盖买家要求的全部验收点：流程、输入输出、人工审核、失败恢复、反馈、成本。

## 快速开始

```bash
# 零第三方依赖（纯 Python 标准库）
python run_tests.py          # 全部验收验证
python demo.py               # 工作流演示
```

## 目录

```
.
├── social_pipeline.py       # 社媒获客工作流（核心）
├── run_tests.py             # 验收验证
├── demo.py                  # 工作流演示
├── schema/
│   └── workflow.schema.json # 工作流配置模板
├── examples/
│   ├── workflow.json        # 多平台配置（facebook/instagram/tiktok）
│   └── materials.json       # 5 条脱敏素材
├── docs/（验收对照 / 实现说明 / 验证记录）
├── SETUP.md
└── README.md
```

## 设计要点

1. **不碰真实账号**：默认 `simulate=True` 模拟发布；真实 API 需要
   external adapter（依赖授权账号，不属于样例范围）。
2. **人工审核在前**：未审核草稿不能发布（测试 6），满足"保留人工监管
   和调整"。
3. **每日 2-3 条计划**：`publish_plan` daily_min/max 约束。
4. **失败恢复**：失败重试一次并留记录（测试 8）。
5. **数据反馈**：发布成功/失败/尝试次数聚合（测试 9）。
6. **成本口径**：开发/运营分开 + USD（测试 10）。

## 环境

- Python 3.8+
- **零第三方依赖**（纯标准库 json/os/re/sys/time）

## 边界说明

本单是**可演示样例**（脱敏素材 + 模拟发布），不实装平台接口、不承诺
询盘/成交；真实账号授权见 `workflow.accounts[].authorized` 与
external adapter 说明（README/SETUP 不作承诺）。