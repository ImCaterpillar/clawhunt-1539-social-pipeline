# -*- coding: utf-8 -*-
"""海外社媒获客工作流主流程验证 —— 对应验收标准
「可演示流程、输入素材及输出示例、账号授权与人工审核、发布失败恢复、数据反馈、成本口径」

零第三方依赖。
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from social_pipeline import SocialPipeline, PipelineError, validate  # noqa

PASS, FAIL = [], []
OK = "\u2705"
NO = "\u274c"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    mark = OK if cond else NO
    line = "  " + mark + " " + name
    if detail:
        line += " -- " + detail
    print(line)


print("=" * 78)
print("Social Pipeline -- acceptance verification")
print("=" * 78)

HERE = os.path.dirname(os.path.abspath(__file__))
pipe = SocialPipeline(os.path.join(HERE, "examples"))

# 1. 可演示流程：工作流配置可加载
check("1. workflow config loadable",
      pipe.config is not None
      and pipe.config["workflow_name"] == "外贸社媒获客工作流样例（脱敏）",
      f"name={pipe.config['workflow_name'] if pipe.config else '?'}")

# 2. 输入素材已加载（脱敏样例）
check("2. input materials loaded", len(pipe.materials) == 5,
      f"materials={len(pipe.materials)}")

# 3. 多平台支持（facebook/instagram/tiktok）
plats = pipe.platforms()
check("3. multi-platform support",
      set(plats) == {"facebook", "instagram", "tiktok"},
      str(plats))

# 4. 按计划生成当日 2-3 条草稿
drafts = pipe.generate_drafts("2026-10-31")
check("4. generate 2-3 drafts per day",
      2 <= len(drafts) <= 3, f"drafts={len(drafts)}")

# 5. 人工审核门（拒绝票）
d0 = drafts[0]
pipe.moderate(d0, approved=False, note="话术需调整")
check("5. human moderation can reject", d0["status"] == "rejected",
      f"status={d0['status']}")

# 6. 未审核草稿不能发布
d1 = drafts[1]
try:
    pipe.publish(d1)
    check("6. unreviewed draft blocked from publish", False)
except PipelineError:
    check("6. unreviewed draft blocked from publish", True)

# 7. 审核通过后可模拟发布（不碰真实账号）
pipe.moderate(d1, approved=True)
rec = pipe.publish(d1, simulate=True)
check("7. approved draft publishes (simulated)",
      rec["published"] is True and rec["records"][-1]["ok"] is True,
      f"published={rec['published']}")

# 8. 发布失败恢复（fail_once → 重试成功）
d2 = drafts[2]
pipe.moderate(d2, approved=True)
rec2 = pipe.publish(d2, fail_once=True)
check("8. publish failure recovery (retry)",
      rec2["published"] is True and len(rec2["records"]) == 2
      and rec2["records"][0]["ok"] is False
      and rec2["records"][1]["ok"] is True,
      f"records={[r['attempt'] for r in rec2['records']]}")

# 9. 数据反馈（合计发布结果）
fb = pipe.feedback()
check("9. feedback aggregates results",
      fb["total"] == 2 and fb["published"] == 2 and fb["failed"] == 0,
      str(fb))

# 10. 成本口径显式（开发/运营分开 + USD）
cm = pipe.config["cost_model"]
check("10. cost model dev/ops separated + USD",
      "dev_cost_note" in cm and "ops_cost_note" in cm
      and cm.get("currency") == "USD",
      str(cm)[:80])

# 11. 非法配置被拒
bad = {"workflow_name": "x", "platforms": [], "publish_plan": {},
       "moderation": {}}
errs = validate(bad, pipe.schema)
check("11. invalid config rejected", len(errs) >= 2, f"{len(errs)} errors")

# 12. demo 可运行
r12 = subprocess.run([sys.executable, "demo.py"], cwd=HERE,
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace")
check("12. demo.py exit=0", r12.returncode == 0, f"exit={r12.returncode}")

# 13. 交付齐套
refs = ["social_pipeline.py", "run_tests.py", "demo.py",
        "schema/workflow.schema.json",
        "examples/workflow.json", "examples/materials.json",
        "README.md", "SETUP.md",
        "docs/验收对照.md", "docs/实现说明.md", "docs/验证记录.md"]
broken = [r for r in refs if not os.path.isfile(os.path.join(HERE, r))]
check("13. delivery set complete (11 files)", not broken,
      "broken=" + str(broken) if broken else str(len(refs)) + " files")

print()
print("=" * 78)
print("Result: PASS " + str(len(PASS)) + "   FAIL " + str(len(FAIL)))
print("=" * 78)
if FAIL:
    print("Failed: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)