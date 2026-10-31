# -*- coding: utf-8 -*-
"""海外社媒矩阵 AI 获客工作流样例（模拟发布，不碰真实账号）

对应 ClawHunt 任务 #1539（海外社媒矩阵 AI 获客工作流样例，$50），
验收标准：提交可演示流程、输入素材及输出示例、账号授权与人工审核步骤、
发布失败恢复和数据反馈说明，并列出运行成本口径。

设计：
  - schema/workflow.schema.json（draft-07）配置多平台/账号/计划/审核/成本
  - SocialPipeline：
      · load 配置 + 脱敏素材
      · generate_drafts(day)：按素材库为当日生成 2-3 条草稿（计划内）
      · moderate(draft)：人工审核门（配置 human_in_loop）
      · publish(draft, simulate=True)：模拟发布（支持失败重试，不碰真实账号）
      · feedback()：发布结果数据反馈（成功/失败/跳过）
  - 零第三方依赖，可演进到真实 API 授权（依赖 external adapter）
"""
import json
import os
import re
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class PipelineError(Exception):
    pass


def _type_ok(value, t):
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def validate(instance, schema, path="$"):
    errors = []
    if "type" in schema and not _type_ok(instance, schema["type"]):
        return [f"{path}: 期望 {schema['type']} 实为 {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: 值 {instance!r} 不在允许集合 {schema['enum']}")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: 长度 {len(instance)} < {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: 值 {instance!r} 不匹配模式 {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < {schema['minimum']}")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: 元素数 {len(instance)} < {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(instance, dict):
        if "required" in schema:
            for k in schema["required"]:
                if k not in instance:
                    errors.append(f"{path}: 缺少必填字段 {k!r}")
        if schema.get("additionalProperties") is False \
                and "properties" in schema:
            for k in instance:
                if k not in schema["properties"]:
                    errors.append(f"{path}: 不允许的额外字段 {k!r}")
        if "properties" in schema:
            for k, sub in schema["properties"].items():
                if k in instance:
                    errors += validate(instance[k], sub, f"{path}.{k}")
    return errors


class SocialPipeline:
    def __init__(self, base_dir=None):
        here = os.path.dirname(os.path.abspath(__file__))
        self.schema = json.load(open(
            os.path.join(here, "schema", "workflow.schema.json"),
            encoding="utf-8"))
        self.config = None
        self.materials = []
        self._published = []
        self._feedbacks = []
        if base_dir:
            self.load_dir(base_dir)

    def load_dir(self, d):
        cfg_path = os.path.join(d, "workflow.json")
        if os.path.isfile(cfg_path):
            self.set_config(json.load(open(cfg_path, encoding="utf-8")))
        mat_path = os.path.join(d, "materials.json")
        if os.path.isfile(mat_path):
            self.materials = json.load(open(mat_path, encoding="utf-8"))
        return len(self.materials)

    def set_config(self, cfg):
        errs = validate(cfg, self.schema)
        if errs:
            raise PipelineError("配置校验失败: " + "; ".join(errs[:4]))
        self.config = cfg

    def platforms(self):
        return [p["platform"] for p in self.config["platforms"]]

    # ── 草稿生成（按计划，每天 2-3 条）─────────────────────────
    def generate_drafts(self, day, count=None):
        plan = self.config["publish_plan"]
        lo, hi = plan["daily_min"], plan["daily_max"]
        n = count or max(lo, min(hi, len(self.materials) or hi))
        drafts = []
        for i in range(n):
            mat = self.materials[i % len(self.materials)] if self.materials else {}
            drafts.append({
                "draft_id": f"draft-{day}-{i+1}",
                "day": day,
                "caption": mat.get("caption", f"Sample draft {i+1}"),
                "asset": mat.get("asset", "sample-asset.png"),
                "platform_hint": mat.get("platform_hint", "facebook"),
                "status": "draft",
            })
        return drafts

    # ── 人工审核门 ─────────────────────────────────────────────
    def moderate(self, draft, approved=True, note=""):
        if not self.config["moderation"]["human_in_loop"]:
            draft["status"] = "approved_auto"
            return draft
        draft["status"] = "approved" if approved else "rejected"
        draft["moderation_note"] = note
        return draft

    # ── 模拟发布（失败恢复，不碰真实账号）─────────────────────
    def publish(self, draft, fail_once=False, simulate=True):
        if draft.get("status") not in ("approved", "approved_auto"):
            raise PipelineError(f"草稿未审核通过，不能发布: {draft.get('draft_id')}")
        records = []
        success = False
        attempt = 0
        while not success and attempt <= (1 if fail_once else 0):
            attempt += 1
            if simulate:
                if fail_once and attempt == 1:
                    records.append({"attempt": attempt, "ok": False,
                                    "error": "simulated_network_error"})
                    continue
                ok = True
                records.append({"attempt": attempt, "ok": True, "simulate": True})
                success = True
            else:
                ok = False
                records.append({"attempt": attempt, "ok": False,
                                "error": "live_api_requires_adapter"})
                break
        rec = {
            "draft_id": draft["draft_id"],
            "platform": draft.get("platform_hint", "facebook"),
            "records": records,
            "published": success,
        }
        self._published.append(rec)
        return rec

    # ── 数据反馈 ───────────────────────────────────────────────
    def feedback(self):
        """发布结果统计（成功/失败/总尝试）"""
        total = len(self._published)
        ok = sum(1 for r in self._published if r["published"])
        fail = total - ok
        attempts = sum(len(r["records"]) for r in self._published)
        return {"total": total, "published": ok, "failed": fail,
                "attempts": attempts}