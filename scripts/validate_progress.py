#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SecMentor 学习者进度完整性校验（通用、零依赖，纯标准库）。

为什么要有这个脚本：
  skills 里的进度规则是「软约束」——弱模型/宿主可能跳过自检。
  本脚本把 state-model.md / motivation.md 里的硬规则机器化，在三个卡点
  （启动读 progress 后 / 写进度后 / review 收尾前）由 core/review 调用，
  fail 则先修后教，防止进度文件静默腐烂。

用法：
  python3 scripts/validate_progress.py [learner_dir]
  learner_dir 缺省 = 本仓库 learner/
退出码：0 合规；1 有 error（阻断继续教学）；2 仅有 warn。
"""
import json
import sys
import glob
from pathlib import Path

# 与 sec-mentor-shared/motivation.md 称号表保持一致
LEVEL_TABLE = [
    (0, 149, 1, "初入山门"),
    (150, 399, 2, "记名弟子"),
    (400, 799, 3, "入室弟子"),
    (800, 1299, 4, "门中熟手"),
    (1300, 1899, 5, "小有所成"),
    (1900, 2599, 6, "独当一面"),
    (2600, 10**9, 7, "行家里手"),
]

# recent_events 每条必须有的字段（state-model 事件写入规则）
RE_REQUIRED_KEYS = ("type", "ts", "summary")

# 合法的 topic 状态（state-model 状态机）
TOPIC_STATUS = {
    "locked", "available", "in_progress", "partial",
    "passed", "failed", "skipped", "deferred", "waived",
}
# 合法的 stage 状态
STAGE_STATUS = {"locked", "available", "in_progress", "completed", "done"}
# 合法的 mastery
MASTERY = {"none", "recall", "understand", "apply", "transfer"}


def expected_level_title(pts):
    for lo, hi, lvl, title in LEVEL_TABLE:
        if lo <= pts <= hi:
            return lvl, title
    return LEVEL_TABLE[-1][2], LEVEL_TABLE[-1][3]


def main():
    repo_root = Path(__file__).resolve().parent.parent
    learner = Path(sys.argv[1]) if len(sys.argv) > 1 else repo_root / "learner"
    prog_path = learner / "progress.json"
    errors, warns = [], []

    if not prog_path.exists():
        print(f"ERR: 找不到 {prog_path}")
        return 1
    try:
        prog = json.loads(prog_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE003
        print(f"ERR: progress.json JSON 解析失败: {e}")
        print("    → 文件已损坏（常见：recent_events 数组混入残缺对象/缺逗号/缺花括号）。")
        print("    → 先按报错行号修复语法，再重跑本校验。")
        return 1

    # ---- 1. 必填字段 ----
    for k in ("schema_version", "learner", "placement", "path",
              "current_stage", "stages", "updated_at"):
        if k not in prog:
            errors.append(f"缺必填顶层字段: {k}")

    # ---- 2. recent_events 结构与上限 ----
    re_ev = prog.get("recent_events", [])
    if len(re_ev) > 20:
        errors.append(f"recent_events {len(re_ev)} 条 > 20 上限")
    re_ts = []
    for i, e in enumerate(re_ev):
        missing = [k for k in RE_REQUIRED_KEYS if k not in e]
        if missing:
            errors.append(
                f"recent_events[{i}] 缺 {missing}（孤儿/残缺对象）: "
                f"现有字段 {list(e.keys())}"
            )
        elif "ts" in e:
            re_ts.append(e["ts"])

    # ---- 3. jsonl 成对性：recent_events 每条 ts 应能在 jsonl 找到对应事件 ----
    jsonl_files = sorted(glob.glob(str(learner / "events" / "*.jsonl")))
    jsonl_lines = []
    jsonl_ts = set()
    for f in jsonl_files:
        for ln in (Path(f).read_text(encoding="utf-8").splitlines()):
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
                jsonl_lines.append(obj)
                ts = obj.get("ts") or obj.get("at")
                if ts:
                    jsonl_ts.add(ts)
            except Exception:  # noqa: BLE003
                errors.append(f"events jsonl 解析失败 {Path(f).name}: {ln[:60]}")
    orphan_re = [e["ts"] for e in re_ev if "ts" in e and e["ts"] not in jsonl_ts]
    if orphan_re:
        errors.append(
            f"recent_events 中 {len(orphan_re)} 条 ts 在 events/*.jsonl 找不到对应行"
            f"（事件只进 recent_events 未落 jsonl）: {orphan_re[:5]}"
            + ("..." if len(orphan_re) > 5 else "")
        )
    if re_ev and len(jsonl_lines) < len(re_ev):
        errors.append(
            f"events/*.jsonl 仅 {len(jsonl_lines)} 行 < recent_events "
            f"{len(re_ev)} 条——整体事件量不足"
        )

    # ---- 4. updated_at 不应落后于 recent_events 最新 ts ----
    upd = prog.get("updated_at")
    if re_ts and upd:
        if max(re_ts) > upd:
            errors.append(
                f"updated_at={upd} 落后于 recent_events 最新 ts={max(re_ts)}，"
                f"写进度时漏更新 updated_at"
            )

    # ---- 5. evidence_id 必须落盘（文件 或 jsonl evidence_recorded 事件）----
    ev_ids_in_prog = []
    for sname, s in prog.get("stages", {}).items():
        for tid, t in (s.get("topics") or {}).items():
            # 顺便校验 topic 字段合法性
            if t.get("status") and t["status"] not in TOPIC_STATUS:
                errors.append(f"{sname}.{tid}.status 非法值: {t['status']}")
            if t.get("mastery") and t["mastery"] not in MASTERY:
                errors.append(f"{sname}.{tid}.mastery 非法值: {t['mastery']}")
            for eid in t.get("evidence_ids", []):
                ev_ids_in_prog.append((sname, tid, eid))

    ev_files = {Path(f).stem for f in glob.glob(str(learner / "evidence" / "*"))}
    ev_in_jsonl = set()
    for e in jsonl_lines:
        if e.get("type") == "evidence_recorded":
            eid = (e.get("data") or {}).get("evidence_id") or e.get("evidence_id")
            if eid:
                ev_in_jsonl.add(eid)
    dangling = [(s, t, eid) for (s, t, eid) in ev_ids_in_prog
                if eid not in ev_files and eid not in ev_in_jsonl]
    if dangling:
        ids = sorted({eid for _, _, eid in dangling})
        errors.append(
            f"evidence_id 悬空（无文件、也无 jsonl evidence_recorded 记录）"
            f"共 {len(ids)} 个: {ids}——passed 必须有真实证据落盘，不能只塞 id"
        )

    # ---- 6. motivation 自洽：level/title vs points_total ----
    mot = prog.get("motivation") or {}
    pts = mot.get("points_total", 0) or 0
    if not isinstance(pts, int):
        errors.append(f"motivation.points_total 非整数: {pts!r}")
        pts = 0
    exp_lvl, exp_title = expected_level_title(pts)
    if mot.get("level") != exp_lvl:
        errors.append(
            f"motivation.level={mot.get('level')} 与 points_total={pts} 不符"
            f"（按 motivation.md 应为 {exp_lvl}），启动时需按表重算"
        )
    if mot.get("title") != exp_title:
        errors.append(
            f"motivation.title={mot.get('title')!r} 与 points_total={pts} 不符"
            f"（应为 {exp_title!r}），启动时需按表重算"
        )

    # ---- 7. pending_celebration 陈旧 ----
    pc = mot.get("pending_celebration")
    if pc:
        if pc.get("points_total") not in (None, pts):
            errors.append(
                f"pending_celebration.points_total={pc.get('points_total')} "
                f"!= 实际 {pts}（陈旧未清理，启动时应置 null 或重发）"
            )

    # ---- 8. stage=completed 时其 topic 不应还 available/in_progress/locked ----
    for sname, s in (prog.get("stages") or {}).items():
        if s.get("status") and s["status"] not in STAGE_STATUS:
            errors.append(f"{sname}.status 非法值: {s['status']}")
        if s.get("status") == "completed":
            for tid, t in (s.get("topics") or {}).items():
                if t.get("status") in ("available", "in_progress", "locked"):
                    warns.append(
                        f"{sname}.{tid}.status={t['status']} 但 stage 已 completed"
                        f"（漏做或忘改状态，需标 skipped/deferred 或补做）"
                    )

    # ---- 9. stage 编号连续性（warn，optional 阶段可合法跳过）----
    stage_nums = []
    for sname in (prog.get("stages") or {}):
        if sname.startswith("P") and sname[1:].isdigit():
            stage_nums.append(int(sname[1:]))
    if stage_nums:
        gaps = [f"P{i}" for i in range(min(stage_nums), max(stage_nums) + 1)
                if i not in set(stage_nums)]
        if gaps:
            warns.append(
                f"stage 编号不连续，缺 {gaps}——若非有意跳过 optional 阶段，"
                f"检查是否漏学 required topic 或 stage 归属错位"
            )

    # ---- 输出 ----
    print(f"校验对象: {prog_path}")
    print(f"  jsonl 行数={len(jsonl_lines)}  recent_events={len(re_ev)}  "
          f"evidence 文件={len(ev_files)}  悬空 id={len(dangling)}")
    if errors:
        print(f"\n❌ 阻断性问题（{len(errors)} 项，须先修后教）:")
        for e in errors:
            print(f"  - {e}")
    if warns:
        print(f"\n⚠️  警告（{len(warns)} 项，不阻断但应处理）:")
        for w in warns:
            print(f"  - {w}")
    if not errors and not warns:
        print("\n✅ progress 校验通过")
        return 0
    return 1 if errors else 2


if __name__ == "__main__":
    sys.exit(main())
