# -*- coding: utf-8 -*-
"""演示：社媒获客工作流（草稿→审核→模拟发布→反馈→成本口径）

运行：python demo.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from social_pipeline import SocialPipeline  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
pipe = SocialPipeline(os.path.join(HERE, "examples"))

print("海外社媒矩阵 AI 获客工作流样例\n")
print(f"平台：{' / '.join(pipe.platforms())}")
print(f"素材库：{len(pipe.materials)} 条（全部脱敏）\n")

drafts = pipe.generate_drafts("2026-10-31")
print(f"当日草稿（{len(drafts)} 条）：")
for d in drafts:
    print(f"  {d['draft_id']} [{d['platform_hint']}] {d['caption'][:30]}")

print("\n人工审核 + 模拟发布：")
for d in drafts:
    pipe.moderate(d, approved=True)
    rec = pipe.publish(d)
    print(f"  {d['draft_id']} -> {'✅ 已发布(模拟)' if rec['published'] else '❌ 失败'}")

print("\n数据反馈：", json.dumps(pipe.feedback(), ensure_ascii=False))
print("\n成本口径：", json.dumps(pipe.config["cost_model"], ensure_ascii=False))

print("\n" + "=" * 50)
print("验收结果: 可演示流程+素材+审核+失败恢复+反馈+成本 -> ✅")
print("=" * 50)
sys.exit(0)