# 代码同步方案 v2（修正版）

> **生成日期**: 2026-03-11
> **背景**: Codex 提出了 6 里程碑的同步计划（v1），经审阅发现核心方案（Phase C 新建目录）不可行。本文档为修正后的完整方案。

---

## 一、现状分析（基于 v1 报告 + 本地实际验证）

### 1.1 本地仓库状态

| 项目 | 值 |
|------|-----|
| 分支 | `main`，clean |
| HEAD | `edb6316`（docs: sync planning files） |
| 相对 origin/main | 超前 4 commits（edb6316, ac9d865, e27e200, e5afa27） |
| results/ 总大小 | 226 MB（仅含聚合产物，缺 runs/logs） |
| emnlp_final_raw/ | 5.8 MB — 仅有 `tables/`, `plots/`, `latex_tables/`, `report/`；**缺 `runs/` 和 `logs/`** |
| final_journal_v2/ | 5.8 MB — 同上，仅有聚合产物 |
| phase5v2/, phase6/ | **不存在**（原始 run 数据从未拉回） |
| artifacts/ | 13 个校准 JSON 文件（完整） |

### 1.2 远端仓库状态（Codex v1 报告）

| 项目 | 值 |
|------|-----|
| 路径 | `/root/LLM_KVCache_Quantization` |
| git HEAD | `fa6ab12`（远古提交） |
| git status | 脏（大量已修改 + 未跟踪） |
| results/ | emnlp_final_raw ~2.4G, final_journal_v2 ~2.4G, phase5v2, phase6 等 |
| 异常目录 | backup/, debug_history/, temp/, meta-llama/, Users/chenzilang/... 嵌套 |
| 代码版本 | **严重落后本地**：缺 37 scripts, 22 src, 25 tests, 7 configs, 6 docs |

### 1.3 关键认知：远端不是 git 镜像

**远端从未被当作 git 仓库管理。** 它最初 clone 了一次（fa6ab12），之后所有代码更新都通过 rsync 覆盖。远端 git 状态是历史遗留。

这意味着：
- 远端 git diff/status 作为**诊断参考**有用，但不作为同步策略的基础
- "远端脏"是正常状态——实验输出、临时文件、模型缓存都在那里
- 同步策略应基于 **rsync 增量覆盖**，而非 git-based 方案

### 1.4 本地真正缺什么

| 数据集 | 远端路径 | 估计大小 | 本地状态 | 优先级 |
|--------|----------|---------|---------|--------|
| emnlp_final_raw/runs/ | results/emnlp_final_raw/runs/ | ~2G | **完全缺失** | P0 |
| emnlp_final_raw/logs/ | results/emnlp_final_raw/logs/ | ~200M | **完全缺失** | P1 |
| phase5v2/runs/ | results/phase5v2/runs/ | ~1.5G | **完全缺失** | P2（已合并到 emnlp_final_raw） |
| phase5v2/logs/ | results/phase5v2/logs/ | ~100M | **完全缺失** | P2 |
| phase6/runs/ | results/phase6/runs/ | ~500M | **完全缺失** | P2（已合并到 emnlp_final_raw） |
| 聚合产物 | results/emnlp_final_raw/{tables,plots,...} | ~6M | ✅ 已有 | — |

> **P0 理由**：论文写作和数据审计需要 seed 级原始 CSV。目前本地只有聚合后的汇总表，无法做 per-run 检查。
> **P2 理由**：phase5v2 和 phase6 的 runs 已合并到 emnlp_final_raw，拉 emnlp_final_raw 即覆盖大部分需求。如需溯源才需要拉原始分目录。

---

## 二、Codex v1 方案的问题

### 2.1 Phase C（新建目录）为什么不可行

Codex v1 建议新建 `/root/LLM_KVCache_Quantization_sync_20260311`，不动旧目录。

**致命问题：**

1. **路径硬编码**：至少 4 个脚本硬编码了 `/root/LLM_KVCache_Quantization`：
   - `scripts/phase6_post_profiling.sh` L22: `SRC="/root/LLM_KVCache_Quantization"`
   - `scripts/dispatch_phase5v2.sh`
   - `scripts/dispatch_phase5v2_throughput.sh`
   - `scripts/dispatch_phase6_core.sh`
   - SKILL.md L22: `REMOTE_DIR="/root/LLM_KVCache_Quantization"`

2. **校准产物断链**：远端 `artifacts/` 有校准 JSON，实验配置通过相对路径 `artifacts/kv_calib_*.json` 引用。新目录没有这些文件。

3. **结果断链**：`results/emnlp_final_raw`（2136 dirs, ~2.4G）在旧目录。新目录要么 symlink（增加复杂度），要么复制（浪费 ~5G + 时间）。

4. **成本不对称**：远端"脏"文件（backup/, temp/, debug_history/）全在旧目录根层。不用 `--delete` 的 rsync 根本不会碰它们，无需为它们"搬家"。

### 2.2 其他问题

| 问题 | 说明 |
|------|------|
| 未参考 SKILL.md | 项目有成熟的 rsync 规范（`.agents/skills/remote-server/SKILL.md` L101-127），Codex 计划完全没有引用 |
| git-centric 思维 | 用 `git diff remote_head..HEAD` 分析差异，但远端是 rsync-managed，git 状态无意义 |
| 6 里程碑过度工程化 | 其中 3 个（创建新目录 + 验证 + 切换）可以省掉 |
| 门禁修复方向错误 | 本地 pytest 不能跑是 macOS 环境限制（MEMORY.md 已知陷阱 #6），不是 gate 的 bug |

---

## 三、修正版 ExecPlan

### 3.0 问题陈述

- **现状**: 本地代码领先远端 37+ scripts / 22+ src 文件；远端有 ~2.4G 实验原始数据未拉回本地
- **期望**: 双向同步——先拉回远端结果（论文/审计需要），再推送最新代码（后续实验需要）
- **为什么现在做**: Phase 7 论文写作中，需要 seed 级原始 CSV 支撑数据审计；远端代码落后可能导致下次实验跑不通

### 3.1 objective.md 对齐

- 服务目标：保证实验主线代码和结果链条在本地和远端均完整可用
- 触碰边界：远端代码目录（覆盖式更新）、远端结果目录（只读拉取）
- 不触碰：研究方向、算法口径、实验定义、远端 results/ 内容

### 3.2 目标与非目标

**目标：**
- 拉回远端 `results/emnlp_final_raw/{runs,logs}` 到本地
- 推送本地最新代码/配置/文档到远端 `/root/LLM_KVCache_Quantization`
- 远端推送后能通过 `python3 -m compileall -f -q src/ scripts/` 最小验证

**非目标：**
- 不清理远端脏目录（backup/, temp/, debug_history/, 异常嵌套 Users/）
- 不在远端做 git 操作
- 不新建远端目录
- 不拉 `results/phase5v2/` 或 `results/phase6/` 原始分目录（已合并到 emnlp_final_raw）

### 3.3 约束与假设

| 类型 | 内容 |
|------|------|
| 约束 | 远端现有 `results/` 不可被覆盖或删除 |
| 约束 | rsync 不使用 `--delete`，避免误删远端文件 |
| 约束 | 不推送 `thesis/`、`logs/`、`.claude/`、`.pytest_cache/` |
| 约束 | 本地 pytest 无法运行（macOS 环境限制），gate 使用 `--skip-tests` |
| 假设 | 远端 `/root/LLM_KVCache_Quantization` 仍是后续实验的主目录 |
| 假设 | 远端 `results/emnlp_final_raw/` 自 2026-03-10 Phase 6 完成后未变化 |
| 假设 | 远端无正在运行的实验进程 |

### 3.4 具体工作清单

#### Phase A: 前置检查（~3 min，本地）

```bash
# A1: 本地状态确认
git status --short --branch
# 预期: ## main...origin/main [ahead 4], clean

# A2: gate 通过
bash scripts/rsync_gate.sh --skip-tests
# 预期: "Gate PASSED. Safe to rsync."

# A3: SSH 连通性
ssh -p 31867 root@region-42.seetacloud.com "echo OK && nvidia-smi --query-gpu=name --format=csv,noheader"
# 预期: OK + GPU 型号

# A4: 远端无运行进程
ssh -p 31867 root@region-42.seetacloud.com "bash -lc 'ps aux | grep python | grep -v grep | wc -l'"
# 预期: 0（无实验进程）

# A5: 远端磁盘空间
ssh -p 31867 root@region-42.seetacloud.com "df -h /root"
# 预期: 有足够空间
```

#### Phase B: 拉回远端结果（~15-30 min，取决于网速）

```bash
# B1: dry-run 确认拉取范围
rsync -avzn --progress \
  -e "ssh -p 31867" \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/results/emnlp_final_raw/ \
  results/emnlp_final_raw/
# 审查输出：应该只有 runs/ 和 logs/ 下的文件需要传输
# tables/、plots/、latex_tables/、report/ 应该大部分 up-to-date

# B2: 执行拉取（去掉 -n）
rsync -avz --progress \
  -e "ssh -p 31867" \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/results/emnlp_final_raw/ \
  results/emnlp_final_raw/

# B3: 验证
ls results/emnlp_final_raw/runs/ | wc -l
# 预期: ~2136（与 Phase 6 记录一致）

ls results/emnlp_final_raw/logs/ | wc -l
# 预期: > 0

du -sh results/emnlp_final_raw/
# 预期: ~2-3G
```

**可选**：如果论文需要溯源到 phase5v2/phase6 分目录，追加：
```bash
rsync -avz --progress \
  -e "ssh -p 31867" \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/results/phase5v2/ \
  results/phase5v2/

rsync -avz --progress \
  -e "ssh -p 31867" \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/results/phase6/ \
  results/phase6/
```

#### Phase C: 推送代码到远端（~5-10 min）

```bash
# C1: dry-run 确认推送范围
rsync -avzn --progress --itemize-changes \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  --exclude='results/' \
  --exclude='artifacts/' \
  --exclude='thesis/' \
  --exclude='logs/' \
  --exclude='.pytest_cache/' \
  --exclude='.claude/' \
  --exclude='*.jsonl' \
  --exclude='docs/autodl_server.md' \
  --exclude='progress.md' \
  --exclude='task_plan.md' \
  --exclude='findings.md' \
  -e "ssh -p 31867" \
  ./ root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/

# 审查 dry-run 输出：
# - 应该看到 src/**/*.py, scripts/**/*.py, configs/**/*.yaml 等被更新
# - 应该看到 CLAUDE.md, objective.md, iteration.md 等被更新
# - 不应该看到 results/, artifacts/, thesis/, .claude/ 下的文件
# - 不应该看到 docs/autodl_server.md
#
# 关键检查点:
#   变更文件数应与 git diff fa6ab12..edb6316 --name-only 大致对应
#   不应出现 "deleting" 行（因为没用 --delete）

# C2: 执行推送（去掉 -n）
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  --exclude='results/' \
  --exclude='artifacts/' \
  --exclude='thesis/' \
  --exclude='logs/' \
  --exclude='.pytest_cache/' \
  --exclude='.claude/' \
  --exclude='*.jsonl' \
  --exclude='docs/autodl_server.md' \
  --exclude='progress.md' \
  --exclude='task_plan.md' \
  --exclude='findings.md' \
  -e "ssh -p 31867" \
  ./ root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/
```

**排除列表说明：**

| 排除项 | 理由 |
|--------|------|
| `.git` | 远端 git 是遗留状态，不覆盖 |
| `__pycache__/`, `*.pyc` | 编译缓存，远端会自动生成 |
| `.venv` | 本地虚拟环境，远端有自己的 conda |
| `results/` | 远端结果更完整，不能被本地覆盖 |
| `artifacts/` | 远端已有校准产物（Phase 6 验证过），且本地的可能不如远端新 |
| `thesis/` | 论文 LaTeX 构建产物，远端不需要 |
| `logs/` | 本地日志，与远端无关 |
| `.pytest_cache/` | 测试缓存 |
| `.claude/` | Claude Code 本地配置 |
| `*.jsonl` | 会话日志，敏感 |
| `docs/autodl_server.md` | 含密码，不推 |
| `progress.md`, `task_plan.md`, `findings.md` | 临时 planning 文件（.gitignore 已排除） |

#### Phase D: 远端验证（~3 min）

```bash
# D1: 关键文件存在性
ssh -p 31867 root@region-42.seetacloud.com "bash -lc '
cd /root/LLM_KVCache_Quantization

echo \"=== 关键文件检查 ===\"
for f in \
  src/engine/engine.py \
  src/engine/generate_loop.py \
  src/engine/patch_model.py \
  src/cache/kv_cache.py \
  src/quant/quantize.py \
  scripts/run_experiments.py \
  scripts/aggregate_results.py \
  scripts/eval_ppl.py \
  scripts/eval_ruler.py \
  configs/exp_matrix.yaml \
  CLAUDE.md \
  objective.md \
  iteration.md \
  review_tracker.md; do
  if [ -f \"\$f\" ]; then echo \"  OK: \$f\"; else echo \"  MISSING: \$f\"; fi
done

echo \"\"
echo \"=== Python 编译检查 ===\"
python3 -m compileall -f -q src/ scripts/ 2>&1 | tail -5
echo \"compileall exit: \$?\"

echo \"\"
echo \"=== 校准产物完整性 ===\"
ls artifacts/kv_calib_*.json 2>/dev/null | wc -l
echo \"calib JSON files\"

echo \"\"
echo \"=== 结果目录完整性 ===\"
ls results/emnlp_final_raw/runs/ 2>/dev/null | wc -l
echo \"emnlp_final_raw/runs/ dirs\"
'"

# D2: second dry-run 确认无残留差异（仅代码文件）
rsync -avzn \
  --exclude='.git' \
  --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.venv' --exclude='results/' --exclude='artifacts/' \
  --exclude='thesis/' --exclude='logs/' --exclude='.pytest_cache/' \
  --exclude='.claude/' --exclude='*.jsonl' \
  --exclude='docs/autodl_server.md' \
  --exclude='progress.md' --exclude='task_plan.md' --exclude='findings.md' \
  -e "ssh -p 31867" \
  ./ root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/ 2>&1 | grep -c '^>'
# 预期: 0（无待传文件）
```

### 3.5 验收标准

| # | 标准 | 验证方式 |
|---|------|---------|
| 1 | 本地 emnlp_final_raw/runs/ 有 ~2136 dirs | `ls results/emnlp_final_raw/runs/ \| wc -l` |
| 2 | 远端 Python 编译通过 | `compileall exit: 0` |
| 3 | 远端关键文件全部 OK | D1 检查无 MISSING |
| 4 | 代码 second dry-run 差异为 0 | D2 grep count = 0 |
| 5 | 远端 results/ 未被修改 | 不在 rsync 推送范围内 |
| 6 | 远端 artifacts/ 未被覆盖 | 不在 rsync 推送范围内 |

### 3.6 风险与缓解

| # | 风险 | 概率 | 缓解 | 回滚 |
|---|------|------|------|------|
| 1 | rsync 推送覆盖远端手工修改的脚本 | 中 | 推前 dry-run 逐条审查 `>f` 行；远端历来不手工改代码 | 远端 git 有 fa6ab12 可 checkout 恢复；但实际上远端脏改没有提交过，无法恢复——所以 dry-run 审查是唯一防线 |
| 2 | 拉取结果时网络中断导致不完整 | 低 | rsync 支持断点续传（重跑即可） | 再跑一次 rsync |
| 3 | 远端有实验进程正在运行，rsync 覆盖导致运行中脚本不一致 | 中 | Phase A 的 A4 检查确认无 python 进程 | 等进程结束后再推 |
| 4 | artifacts/ 被意外推送覆盖远端更新的校准文件 | 低 | 排除列表已包含 `artifacts/`；dry-run 二次确认 | 远端 artifacts/ 有校准产物备份 |
| 5 | `docs/autodl_server.md` 被推到远端 | 低 | 排除列表已包含；dry-run 确认 | 远端删除该文件 |
| 6 | 远端磁盘空间不足 | 极低 | A5 预检；代码推送量 <50MB | 不执行 |

### 3.7 需确认问题

**Q1: 是否需要拉 phase5v2/phase6 原始分目录？**
- 选项 A: 只拉 emnlp_final_raw（已合并全部数据，~2.4G）
- 选项 B: 同时拉 phase5v2 + phase6（可溯源但额外 ~2G）
- **默认推荐: A**。emnlp_final_raw 是 Phase 6 post-profiling 的最终合并产物，包含全部 2136 dirs。除非需要对比合并前后的差异，否则不需要原始分目录。

**Q2: 远端脏目录（backup/, temp/, debug_history/, Users/...）是否清理？**
- 选项 A: 本轮不清理，另开任务
- 选项 B: 同步完成后顺手清理
- **默认推荐: A**。清理需要先确认每个目录的内容，风险高且与同步目标无关。

**Q3: 是否更新远端 artifacts/？**
- 选项 A: 不推（当前排除列表已排除）
- 选项 B: 推送本地 artifacts/ 覆盖远端
- **默认推荐: A**。远端 artifacts/ 在 Phase 6 中经过完整验证（"6/6 calib OK"），且远端可能有本地没有的 7B/8B 校准文件。不推更安全。

### 3.8 里程碑与执行顺序

```
Phase A: 前置检查（3 min）
  ↓
Phase B: 拉回远端结果（15-30 min）
  ↓
Phase C: 推送代码到远端（5-10 min）
  ↓
Phase D: 远端验证（3 min）
  ↓
记录到 iteration.md + commit
```

总耗时：~30-50 min（含网络传输）。

---

## 四、与 Codex v1 的差异对照

| 维度 | Codex v1 | 修正版 v2 | 理由 |
|------|----------|-----------|------|
| 远端目标 | 新建 `_sync_20260311` 目录 | 原地覆盖 `/root/LLM_KVCache_Quantization` | 4+ 脚本硬编码路径；新目录断链 artifacts/results |
| 同步工具 | 未明确 | rsync（沿用 SKILL.md 规范） | 项目既有实践 |
| `--delete` | 讨论后禁用 | **禁用**（写入排除列表而非新建目录来避免误删） | 远端脏文件不碍事，不删 |
| 远端 git 操作 | 做 git status/diff 分析 | **不做**任何远端 git 操作 | 远端是 rsync-managed，git 无意义 |
| Phase 数 | 6 个里程碑 | **4 个 Phase** | 去掉"新建目录/验证新目录/切换目录" |
| 门禁策略 | 3 选项（修 gate / skip / 后续修） | 直接 `--skip-tests` | 本地 pytest 不能跑是环境限制，不是 gate bug |
| 排除列表 | 概念性描述 | **精确到每个路径 + 理由表** | 可直接复制执行 |
| artifacts/ | "条件推" | **不推**（远端已有且经过验证） | 避免覆盖远端更完整的校准产物 |
| 拉取范围 | 笼统说"拉 logs/runs" | **精确到 emnlp_final_raw，可选 phase5v2/phase6** | 减少不必要传输 |
| 验证方式 | git diff --no-index | `compileall` + `rsync second dry-run` + 文件存在性 | 匹配 rsync-managed 环境 |

---

## 五、执行后的仓库状态预期

| 位置 | 状态 |
|------|------|
| 本地 results/emnlp_final_raw/ | ~2.4G，含 runs/(2136 dirs) + logs/ + tables/ + plots/ + ... |
| 本地 git | clean, main, ahead 4+ |
| 远端代码 | 与本地 edb6316 一致（src/, scripts/, configs/, docs/, tests/） |
| 远端 results/ | 不变 |
| 远端 artifacts/ | 不变 |
| 远端脏目录 | 不变（backup/, temp/, debug_history/ 等原样保留） |

---

## 六、后续建议（不在本轮执行）

1. **远端脏目录清理**：另开任务，逐个确认 backup/, temp/, debug_history/, Users/... 的内容后清理
2. **rsync_gate.sh 改进**：将 pytest 替换为 `python3 -m py_compile scripts/run_experiments.py` 或 `compileall`，使本地门禁能正常通过
3. **git push**：4 个 ahead commits 推到 origin/main（需用户确认）
4. **远端 .gitignore 更新**：远端 .gitignore 可能是旧版，rsync 已推送最新版本后无需额外操作
