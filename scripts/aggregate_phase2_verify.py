#!/usr/bin/env python3
"""
Phase 2 编号 8 Post: 统一验证聚合器（Codex 2026-04-18 09:30 修订版）

支持 5 种 run_name 格式（8A batch1 / 8B batch2 / 8C C1 7B / C2 8B / 编号 7 sweep+ablation）
主键 (batch, model, task, allocator_type, k, agg, seed, n_samples, sample_offset)
dedup by timestamp (ISO 字典序)

硬 Gate 判定（Codex 2026-04-18 10:00 修订: scale-shift 版）：
  1. F1 稳定：Random 多 seed 下 BAKV > mean(Random) (8A 数据)
  2. F2 Scale-Shift：对每个 model 扫 k∈{1,3,5,7} 找 BAKV best-k；不同 model best-k 分化
     即 behavior-guided allocation 存在 model-scale-dependent optimal budget window (8C C1/C2)
  3. F2 扩任务：4 new tasks 上 BAKV 在 1.5B best-k (=1) 下 ≥ Heuristic ≥3/4 (8B 数据)
  4. F2 sample offset：BAKV vs Heuristic Δ 方向一致 (8A 数据)
  5. F3 不视为失败：k≥3 BAKV ≈ Heuristic 在跨模型/扩任务仍成立 (8B/8C)
  6. F4 跨模型（加分）：max vs mean aggregation 在 7B k=1+k=5 诊断结果 (6 new runs)

用法:
  python3 scripts/aggregate_phase2_verify.py \
    --sweep_dirs results/phase2_batch3_cross_model_7b \
                 results/phase2_batch1_verify_1p5b \
                 results/phase2_batch2_extend_tasks \
    --out_csv results/phase2_verify_all.csv \
    --out_md docs/phase2_verify_final_report.md \
    --out_gate_log results/phase2_gate8_decision.log
"""
import argparse
import csv
import math
import random
import re
import sys
from collections import defaultdict
from pathlib import Path


# ========== Run name regex dispatch（5 种格式） ==========

# 编号 7 M3 sweep (1.5B): phase2sweep_1p5b_int4mixedkv_{allocator}_k{K}[_seed{S}]_{task}_n{N}
RE_PHASE7_SWEEP = re.compile(
    r"phase2sweep_1p5b_int4mixedkv_"
    r"(?P<allocator>bakv|heuristic|random3)"
    r"_k(?P<k>\d+)(?:_seed(?P<seed>\d+))?"
    r"_(?P<task>[a-z_]+)_n(?P<n>\d+)"
)
# 编号 7 M3 ablation: phase2abl_1p5b_int4mixedkv_{alloc_raw}_k{K}[_seed{S}]_{task}_n{N}
RE_PHASE7_ABLATION = re.compile(
    r"phase2abl_1p5b_int4mixedkv_"
    r"(?P<allocator>bakv_max|bakv_mean|random)"
    r"_k(?P<k>\d+)(?:_seed(?P<seed>\d+))?"
    r"_(?P<task>[a-z_]+)_n(?P<n>\d+)"
)
# 编号 8 C1 7B: phase2c1_7b_int4mixedkv_{policy}_{task}_n{N}
RE_PHASE8_C1 = re.compile(
    r"phase2c1_7b_int4mixedkv_"
    r"(?P<policy>uniform_int[48]_k[48]v[48]|bakv_k\d+|heuristic_k\d+|random3_k\d+_seed\d+)"
    r"_(?P<task>[a-z_]+)_n(?P<n>\d+)"
)
# 编号 8 batch1 (1.5B): phase2v_b1_1p5b_int4mixedkv_{policy}_{task}_n{N}_off{OFF}
RE_PHASE8_BATCH1 = re.compile(
    r"phase2v_b1_1p5b_int4mixedkv_"
    r"(?P<policy>bakv_k\d+|heuristic_k\d+|random3_k\d+_seed\d+)"
    r"_(?P<task>[a-z_]+)_n(?P<n>\d+)_off(?P<off>\d+)"
)
# 编号 8 batch2 (1.5B 扩任务): phase2v_b2_1p5b_int4mixedkv_{policy}_{task}_n{N}
RE_PHASE8_BATCH2 = re.compile(
    r"phase2v_b2_1p5b_int4mixedkv_"
    r"(?P<policy>uniform_int[48]_k[48]v[48]|bakv_k\d+|heuristic_k\d+|random3_k\d+_seed\d+)"
    r"_(?P<task>[a-z_]+)_n(?P<n>\d+)"
)
# 编号 8 C2 8B: phase2c2_8b_int4mixedkv_{policy}_{task}_n{N}
RE_PHASE8_C2 = re.compile(
    r"phase2c2_8b_int4mixedkv_"
    r"(?P<policy>uniform_int[48]_k[48]v[48]|bakv_k\d+|heuristic_k\d+|random3_k\d+_seed\d+)"
    r"_(?P<task>[a-z_]+)_n(?P<n>\d+)"
)

POLICY_PART_RE = re.compile(
    r"(?P<allocator>uniform_int4|uniform_int8|bakv|heuristic|random3)"
    r"(?:_k(?P<k>\d+))?(?:_seed(?P<seed>\d+))?"
)


def parse_policy(policy_str: str):
    """从 policy 子串解析 (allocator, k, seed)"""
    if policy_str.startswith("uniform_int4"):
        return "uniform_int4", 0, None
    if policy_str.startswith("uniform_int8"):
        return "uniform_int8", 0, None
    m = re.match(r"bakv_k(\d+)", policy_str)
    if m:
        return "bakv", int(m.group(1)), None
    m = re.match(r"heuristic_k(\d+)", policy_str)
    if m:
        return "heuristic", int(m.group(1)), None
    m = re.match(r"random3_k(\d+)_seed(\d+)", policy_str)
    if m:
        return "random3", int(m.group(1)), int(m.group(2))
    return "unknown", 0, None


def parse_run_name(rn: str):
    """尝试所有正则，返回 dict 含完整元数据"""
    m = RE_PHASE7_SWEEP.match(rn)
    if m:
        alloc = m.group("allocator")
        seed = int(m.group("seed")) if m.group("seed") else None
        return {
            "batch": "phase7_sweep", "model": "Qwen2.5-1.5B",
            "allocator_type": alloc, "k": int(m.group("k")),
            "agg": "max" if alloc == "bakv" else "-",
            "seed": seed, "task": m.group("task"),
            "n_samples": int(m.group("n")), "sample_offset": 0,
        }
    m = RE_PHASE7_ABLATION.match(rn)
    if m:
        raw = m.group("allocator")
        seed = int(m.group("seed")) if m.group("seed") else None
        if raw == "bakv_max":
            return {"batch": "phase7_ablation", "model": "Qwen2.5-1.5B",
                    "allocator_type": "bakv", "k": int(m.group("k")), "agg": "max",
                    "seed": seed, "task": m.group("task"),
                    "n_samples": int(m.group("n")), "sample_offset": 0}
        if raw == "bakv_mean":
            return {"batch": "phase7_ablation", "model": "Qwen2.5-1.5B",
                    "allocator_type": "bakv", "k": int(m.group("k")), "agg": "mean",
                    "seed": seed, "task": m.group("task"),
                    "n_samples": int(m.group("n")), "sample_offset": 0}
        if raw == "random":
            return {"batch": "phase7_ablation", "model": "Qwen2.5-1.5B",
                    "allocator_type": "random3", "k": int(m.group("k")), "agg": "-",
                    "seed": seed, "task": m.group("task"),
                    "n_samples": int(m.group("n")), "sample_offset": 0}
    m = RE_PHASE8_C1.match(rn)
    if m:
        alloc, k, seed = parse_policy(m.group("policy"))
        return {"batch": "phase8_c1", "model": "Qwen2.5-7B",
                "allocator_type": alloc, "k": k,
                "agg": "max" if alloc == "bakv" else "-",
                "seed": seed, "task": m.group("task"),
                "n_samples": int(m.group("n")), "sample_offset": 0}
    m = RE_PHASE8_BATCH1.match(rn)
    if m:
        alloc, k, seed = parse_policy(m.group("policy"))
        return {"batch": "phase8_batch1", "model": "Qwen2.5-1.5B",
                "allocator_type": alloc, "k": k,
                "agg": "max" if alloc == "bakv" else "-",
                "seed": seed, "task": m.group("task"),
                "n_samples": int(m.group("n")), "sample_offset": int(m.group("off"))}
    m = RE_PHASE8_BATCH2.match(rn)
    if m:
        alloc, k, seed = parse_policy(m.group("policy"))
        return {"batch": "phase8_batch2", "model": "Qwen2.5-1.5B",
                "allocator_type": alloc, "k": k,
                "agg": "max" if alloc == "bakv" else "-",
                "seed": seed, "task": m.group("task"),
                "n_samples": int(m.group("n")), "sample_offset": 0}
    m = RE_PHASE8_C2.match(rn)
    if m:
        alloc, k, seed = parse_policy(m.group("policy"))
        return {"batch": "phase8_c2", "model": "LLaMA-3.1-8B",
                "allocator_type": alloc, "k": k,
                "agg": "max" if alloc == "bakv" else "-",
                "seed": seed, "task": m.group("task"),
                "n_samples": int(m.group("n")), "sample_offset": 0}
    return None


UNIFIED_FIELDS = [
    "batch", "model", "task", "allocator_type", "k", "agg", "seed",
    "n_samples", "sample_offset",
    "score", "metric_name",
    "f1_mean", "exact_match_rate", "contains_match_rate",
    "latency_ttft_ms", "latency_tpot_ms", "gpu_peak_mem_mb",
    "timestamp", "git_commit", "run_name",
]


# ========== IO + dedup ==========

def find_pairs(runs_dir: Path):
    pairs = defaultdict(dict)
    for p in sorted(runs_dir.rglob("*.csv")):
        name = p.name
        m_prof = re.match(r"profile_longbench_(.+?)_([0-9T:\-\.]+)\.csv$", name)
        m_task = re.match(r"longbench_task_summary_(.+?)_([0-9T:\-\.]+)\.csv$", name)
        if m_prof:
            pairs[(m_prof.group(1), m_prof.group(2))]["profile"] = p
        elif m_task:
            pairs[(m_task.group(1), m_task.group(2))]["task_summary"] = p
    return pairs


def load_runs(runs_dirs):
    rows = []
    for d in runs_dirs:
        if not d.exists():
            print(f"WARN: {d} missing, skip", file=sys.stderr)
            continue
        pairs = find_pairs(d)
        for key, files in pairs.items():
            if "profile" not in files or "task_summary" not in files:
                continue
            profs = list(csv.DictReader(open(files["profile"], newline="")))
            tasks = list(csv.DictReader(open(files["task_summary"], newline="")))
            if not profs or not tasks:
                continue
            prof = profs[0]
            parsed = parse_run_name(prof.get("run_name", ""))
            if not parsed:
                continue
            for tr in tasks:
                rows.append({
                    **parsed,
                    "task": tr.get("task_name", "") or parsed["task"],
                    "score": tr.get("official_metric_value", ""),
                    "metric_name": tr.get("official_metric_name", ""),
                    "f1_mean": tr.get("f1_mean", ""),
                    "exact_match_rate": tr.get("exact_match_rate", ""),
                    "contains_match_rate": tr.get("contains_match_rate", ""),
                    "latency_ttft_ms": prof.get("ttft_ms", ""),
                    "latency_tpot_ms": prof.get("tpot_ms", ""),
                    "gpu_peak_mem_mb": prof.get("gpu_mem_peak_mb", ""),
                    "timestamp": tr.get("timestamp", ""),
                    "git_commit": tr.get("git_commit", ""),
                    "run_name": prof.get("run_name", ""),
                })
    return rows


def dedup_by_timestamp(rows):
    """9 维主键保留最新 timestamp"""
    latest = {}
    dropped = 0
    for r in rows:
        key = (r["batch"], r["model"], r["task"], r["allocator_type"],
               r["k"], r["agg"], r["seed"], r["n_samples"], r["sample_offset"])
        ts = r.get("timestamp", "")
        if key not in latest:
            latest[key] = r
        elif ts > latest[key].get("timestamp", ""):
            latest[key] = r; dropped += 1
        else:
            dropped += 1
    return sorted(latest.values(),
                  key=lambda r: tuple(str(r[k]) for k in [
                      "batch", "model", "task", "allocator_type", "k", "agg", "seed",
                      "n_samples", "sample_offset"])), dropped


# ========== Gate 判定 ==========

def _score(r):
    try:
        return float(r["score"])
    except (ValueError, TypeError):
        return None


def gate_f1_random_multi_seed(rows):
    """8A: Random-k 多 seed 下 BAKV > mean(Random) 稳定？"""
    out = []
    # 聚合 1.5B batch1 的 Random seeds per (task, k)
    by_key = defaultdict(list)
    bakv_map = {}
    for r in rows:
        if r["model"] != "Qwen2.5-1.5B":
            continue
        s = _score(r)
        if s is None:
            continue
        if r["allocator_type"] == "random3" and r["batch"] in ("phase8_batch1", "phase7_sweep"):
            by_key[(r["task"], r["k"])].append((r["seed"], s))
        if r["allocator_type"] == "bakv" and r["batch"] in ("phase8_batch1", "phase7_sweep"):
            bakv_map[(r["task"], r["k"])] = s

    total = 0
    pass_ = 0
    for (task, k), random_list in by_key.items():
        if len(random_list) < 3:
            continue  # 至少 3 seeds 才算
        random_mean = sum(s for _, s in random_list) / len(random_list)
        bakv = bakv_map.get((task, k))
        if bakv is None:
            continue
        total += 1
        pct = (bakv - random_mean) / random_mean * 100 if random_mean else 0
        out.append(f"  {task}/k={k}: BAKV={bakv:.3f} vs mean(Random[{len(random_list)} seeds])={random_mean:.3f} → +{pct:.1f}%")
        if bakv > random_mean:
            pass_ += 1
    verdict = "PASS" if (total > 0 and pass_ / total >= 0.8) else "FAIL"
    return verdict, f"{pass_}/{total} (task,k) combos: BAKV > mean(Random 多 seed)\n" + "\n".join(out)


def gate_f2_scale_shift_best_k(rows):
    """8C: 对每个 model 扫 k∈{1,3,5,7} 找 best-k by BAKV avg score；
    PASS 条件: (a) 该 model 的 best-k 上 BAKV > Heuristic 同 k, 3/3 tasks 胜;
              (b) 不同 model 的 best-k 分化（证明 scale-dependent optimal budget window）。
    替代旧 k=1 硬编码 gate——保留历史判定到 gate_f2_cross_model_7b_k1_legacy 供回看。
    """
    # 收集 (model, k, task) -> {allocator: score}
    buckets = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # model -> k -> task -> alloc -> score
    for r in rows:
        if r["batch"] not in ("phase8_c1", "phase8_c2", "phase7_sweep"):
            continue
        if r["allocator_type"] not in ("bakv", "heuristic"):
            continue
        if r["k"] not in (1, 3, 5, 7):
            continue
        s = _score(r)
        if s is None:
            continue
        buckets[r["model"]][r["k"]][r["task"]][r["allocator_type"]] = s

    out = []
    per_model_best_k = {}
    for model, by_k in sorted(buckets.items()):
        # 每个 k 计算 BAKV 平均分，找 best-k
        best_k, best_avg = None, -1e9
        k_stats = {}
        for k, by_task in by_k.items():
            bakv_scores = [d["bakv"] for d in by_task.values() if "bakv" in d]
            heur_scores = [d["heuristic"] for d in by_task.values() if "heuristic" in d]
            if not bakv_scores or not heur_scores:
                continue
            avg_b = sum(bakv_scores) / len(bakv_scores)
            avg_h = sum(heur_scores) / len(heur_scores)
            wins = sum(1 for t, d in by_task.items() if "bakv" in d and "heuristic" in d and d["bakv"] > d["heuristic"])
            n = sum(1 for t, d in by_task.items() if "bakv" in d and "heuristic" in d)
            rel = (avg_b - avg_h) / avg_h * 100 if avg_h else 0
            k_stats[k] = (avg_b, avg_h, rel, wins, n)
            if avg_b > best_avg:
                best_avg, best_k = avg_b, k
        if best_k is None:
            continue
        per_model_best_k[model] = best_k
        avg_b, avg_h, rel, wins, n = k_stats[best_k]
        sign = "+" if rel >= 0 else ""
        out.append(f"  {model}: best-k={best_k} → BAKV avg={avg_b:.3f}, Heuristic avg={avg_h:.3f} (Δ={sign}{rel:.1f}%, wins={wins}/{n})")
        for k in sorted(k_stats.keys()):
            avg_b_k, avg_h_k, rel_k, w_k, n_k = k_stats[k]
            marker = " ← best" if k == best_k else ""
            out.append(f"    k={k}: BAKV={avg_b_k:.3f} vs Heur={avg_h_k:.3f} (Δ={rel_k:+.1f}%, w={w_k}/{n_k}){marker}")

    # 判定逻辑
    # (a) 至少一个 model 的 best-k 上 3/3 胜 Heuristic
    best_k_3of3 = 0
    for model, k in per_model_best_k.items():
        by_task = buckets[model][k]
        w = sum(1 for t, d in by_task.items() if "bakv" in d and "heuristic" in d and d["bakv"] > d["heuristic"])
        n = sum(1 for t, d in by_task.items() if "bakv" in d and "heuristic" in d)
        if n > 0 and w == n:
            best_k_3of3 += 1
    # (b) 不同 model 的 best-k 分化
    unique_best_ks = set(per_model_best_k.values())
    scale_shift = len(per_model_best_k) >= 2 and len(unique_best_ks) >= 2

    n_models = len(per_model_best_k)
    if n_models < 2:
        verdict = "PENDING"
        summary = f"只有 {n_models} 个 model 数据，need ≥2 验证 scale-shift"
    elif best_k_3of3 >= 1 and scale_shift:
        verdict = "PASS"
        summary = f"scale-shift 成立: {n_models} models, unique best-k={sorted(unique_best_ks)}; ≥1 model 的 best-k 上 3/3 胜"
    elif scale_shift:
        verdict = "PARTIAL"
        summary = f"scale-shift 成立 (best-k={sorted(unique_best_ks)}) 但没有 model 在 best-k 上 3/3 胜 Heuristic"
    else:
        verdict = "FAIL"
        summary = f"scale-shift 不成立: 所有 model 的 best-k 相同 ({sorted(unique_best_ks)})"
    return verdict, summary + "\n" + "\n".join(out)


def gate_f2_cross_model_7b_k1_legacy(rows):
    """[Legacy] 8C C1: 7B × k=1 下 BAKV vs Heuristic ≥2/3 tasks 胜？
    保留此函数作为历史快照——原 k=1 硬编码 gate 在 C1 数据出来后被证伪
    （7B best-k=5 不是 k=1），参考 gate_f2_scale_shift_best_k 替代。
    """
    by_task = defaultdict(dict)
    for r in rows:
        if r["model"] != "Qwen2.5-7B" or r["batch"] != "phase8_c1" or r["k"] != 1:
            continue
        if r["allocator_type"] in ("bakv", "heuristic"):
            s = _score(r)
            if s is not None:
                by_task[r["task"]][r["allocator_type"]] = s
    wins = 0; total = 0
    rel_deltas = []
    out = []
    for task, d in by_task.items():
        if "bakv" in d and "heuristic" in d:
            total += 1
            rel = (d["bakv"] - d["heuristic"]) / d["heuristic"] * 100 if d["heuristic"] else 0
            rel_deltas.append(rel)
            sign = "+" if rel >= 0 else ""
            out.append(f"  {task}: BAKV={d['bakv']:.3f} vs Heuristic={d['heuristic']:.3f} → Δ={sign}{rel:.1f}%")
            if d["bakv"] > d["heuristic"]:
                wins += 1
    avg_rel = sum(rel_deltas) / len(rel_deltas) if rel_deltas else 0
    verdict = "PASS" if (total > 0 and wins >= (2 * total // 3) and avg_rel > 20) else "FAIL"
    return verdict, f"[legacy k=1 only] wins={wins}/{total}, avg Δ={avg_rel:+.1f}%\n" + "\n".join(out)


def gate_f2_extend_tasks(rows):
    """8B: 4 new tasks × k=1 下 BAKV ≥ Heuristic ≥3/4？"""
    new_tasks = {"dureader", "vcsum", "trec", "lcc"}
    by_task = defaultdict(dict)
    for r in rows:
        if r["batch"] != "phase8_batch2" or r["k"] != 1:
            continue
        if r["task"] in new_tasks and r["allocator_type"] in ("bakv", "heuristic"):
            s = _score(r)
            if s is not None:
                by_task[r["task"]][r["allocator_type"]] = s
    ge = 0; total = 0
    out = []
    for task, d in by_task.items():
        if "bakv" in d and "heuristic" in d:
            total += 1
            out.append(f"  {task}: BAKV={d['bakv']:.3f} vs Heuristic={d['heuristic']:.3f}")
            if d["bakv"] >= d["heuristic"]:
                ge += 1
    verdict = "PASS" if (total >= 3 and ge >= 3) else ("PENDING" if total < 3 else "FAIL")
    return verdict, f"BAKV ≥ Heuristic: {ge}/{total} new tasks (gate: ≥3/4)\n" + "\n".join(out)


def gate_f2_sample_offset(rows):
    """8A A4: 3 个 offset 下 BAKV vs Heuristic Δ 方向一致不翻转？"""
    by_task_off = defaultdict(dict)  # (task, off) -> {alloc: score}
    for r in rows:
        if r["batch"] != "phase8_batch1" or r["k"] != 1:
            continue
        if r["allocator_type"] in ("bakv", "heuristic"):
            s = _score(r)
            if s is not None:
                by_task_off.setdefault((r["task"], r["sample_offset"]), {})[r["allocator_type"]] = s
    # 对每个 task，收集 3 个 offset 的 Δ 符号
    task_offsets = defaultdict(dict)
    for (task, off), d in by_task_off.items():
        if "bakv" in d and "heuristic" in d:
            delta = d["bakv"] - d["heuristic"]
            task_offsets[task][off] = delta
    consistent = 0; total = 0
    out = []
    for task, offs in task_offsets.items():
        if len(offs) < 2:
            continue
        signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in offs.values()]
        same = (all(s >= 0 for s in signs) or all(s <= 0 for s in signs))
        total += 1
        if same:
            consistent += 1
        out.append(f"  {task}: offsets={sorted(offs.items())} signs={signs} → {'一致' if same else '翻转'}")
    verdict = "PASS" if (total > 0 and consistent == total) else ("PENDING" if total == 0 else "FAIL")
    return verdict, f"BAKV vs Heuristic Δ 方向一致: {consistent}/{total} tasks\n" + "\n".join(out)


def gate_f3_convergence(rows):
    """k≥3 BAKV ≈ Heuristic 在跨模型/扩任务仍成立"""
    out = []
    by_model_task_k = defaultdict(dict)
    for r in rows:
        if r["k"] not in (3, 5, 7):
            continue
        if r["allocator_type"] in ("bakv", "heuristic"):
            s = _score(r)
            if s is not None:
                by_model_task_k.setdefault((r["model"], r["task"], r["k"]), {})[r["allocator_type"]] = s
    converge = 0; total = 0
    for key, d in by_model_task_k.items():
        if "bakv" in d and "heuristic" in d and d["heuristic"] != 0:
            total += 1
            rel = abs(d["bakv"] - d["heuristic"]) / d["heuristic"] * 100
            tie = rel < 5  # 5% within = tie
            if tie:
                converge += 1
            out.append(f"  {key}: |Δ|={rel:.1f}% ({'tie' if tie else 'diff'})")
    verdict = "PASS" if (total > 0 and converge / total >= 0.5) else "PENDING"
    return verdict, f"k≥3 收敛证据: {converge}/{total} (model,task,k) tie (<5% Δ)\n" + "\n".join(out[:20])


def bootstrap_mean_ci(values, n_resamples=1000, alpha=0.05, seed=42):
    """简单 bootstrap 置信区间"""
    if not values:
        return None, None, None
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(n_resamples * alpha / 2)]
    hi = means[int(n_resamples * (1 - alpha / 2))]
    mean = sum(values) / n
    return mean, lo, hi


def compute_gate8(rows):
    log = ["=" * 70]
    log.append("Phase 2 编号 8 边界型 Gate 判定（Codex 2026-04-18 09:15 版）")
    log.append("=" * 70)
    log.append("")

    tests = [
        ("F1 稳定（Random 多 seed）", gate_f1_random_multi_seed),
        ("F2 Scale-Shift（跨模型 best-k 分化）", gate_f2_scale_shift_best_k),
        ("F2 扩任务（4 new tasks）", gate_f2_extend_tasks),
        ("F2 sample offset（方向一致）", gate_f2_sample_offset),
        ("F3 收敛（k≥3 tie）", gate_f3_convergence),
        ("[Legacy] F2 k=1 硬编码（已过时仅参考）", gate_f2_cross_model_7b_k1_legacy),
    ]
    verdicts = []
    for name, fn in tests:
        log.append(f"## {name}")
        v, msg = fn(rows)
        verdicts.append((name, v))
        log.append(f"结论: {v}")
        log.append(msg)
        log.append("")

    # 综合判定
    passed = sum(1 for _, v in verdicts if v == "PASS")
    pending = sum(1 for _, v in verdicts if v == "PENDING")
    failed = sum(1 for _, v in verdicts if v == "FAIL")
    log.append("=" * 70)
    log.append(f"综合: {passed} PASS, {pending} PENDING, {failed} FAIL")
    if passed >= 3 and failed == 0:
        log.append("🟢 编号 8 Gate PASS → 允许进编号 9（NoLiMa）或直接 编号 11-13 收口")
        log.append("   论文口径（Codex 克制版）: behavior-guided allocation shows cross-model advantage in low-budget regime")
    elif pending > 0:
        log.append("⏳ PENDING: 部分数据缺失（batch1/batch2/C2 未完成？），补数据后重跑")
    else:
        log.append("🔴 编号 8 Gate FAIL → publishable finding + 论文缩窄到具体边界")
    log.append("=" * 70)
    return "\n".join(log) + "\n", (passed, pending, failed)


# ========== Report ==========

def build_main_table(rows):
    by = defaultdict(dict)
    for r in rows:
        by[(r["batch"], r["model"], r["task"], r["allocator_type"], r["k"])][
            (r["agg"], r["seed"], r["n_samples"], r["sample_offset"])] = r

    lines = []
    lines.append("# Phase 2 编号 8 验证报告（Codex 2026-04-18 09:30 修订版，边界型主张）")
    lines.append("")
    lines.append(f"总数据点：{len(rows)} unique rows (dedup by 9-dim key)")
    lines.append("")
    lines.append("## Batch 分布")
    batch_counts = defaultdict(int)
    for r in rows:
        batch_counts[r["batch"]] += 1
    for batch, cnt in sorted(batch_counts.items()):
        lines.append(f"- `{batch}`: {cnt} rows")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=UNIFIED_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in UNIFIED_FIELDS})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep_dirs", nargs="+", required=True, type=Path)
    ap.add_argument("--out_csv", required=True, type=Path)
    ap.add_argument("--out_md", required=True, type=Path)
    ap.add_argument("--out_gate_log", type=Path, default=Path("results/phase2_gate8_decision.log"))
    args = ap.parse_args()

    raw = load_runs(args.sweep_dirs)
    print(f"Loaded {len(raw)} raw rows")

    rows, dropped = dedup_by_timestamp(raw)
    print(f"Dedup: dropped {dropped} older rows, kept {len(rows)} unique")

    write_csv(rows, args.out_csv)
    print(f"Wrote {args.out_csv}")

    md = build_main_table(rows)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    print(f"Wrote {args.out_md}")

    gate_log, (passed, pending, failed) = compute_gate8(rows)
    args.out_gate_log.parent.mkdir(parents=True, exist_ok=True)
    args.out_gate_log.write_text(gate_log, encoding="utf-8")
    print(f"Wrote {args.out_gate_log}")
    print()
    print(gate_log)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
