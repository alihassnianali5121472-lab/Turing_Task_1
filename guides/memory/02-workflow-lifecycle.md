# Workflow: from a mined package to a submitted task

*Sources: How-to.docx, task-approach-guide-updated.docx, trainGPTCOMMAND.md*

Work these phases **in order**. The order is the speed — skipping the cold-read or the
baseline battery to "save time" is the single most common way a battery gets wasted.

---

## Phase 0 — One-time environment setup

Needed before the first run of any session:

```bash
# every session — loads the personal GLM key + proxy + judge model
source ~/.config/harbor/env
```

This sets:
- `OPENAI_API_KEY` — personal LiteLLM proxy key
- `OPENAI_BASE_URL` — the team proxy
- `JUDGE_MODEL=openai/glm-5.2` — **must** be set or every judged rubric silently scores 0

Also required: Docker running, the `harbor` CLI installed, a `glm-harbor-config.json`
pointed at the current task (`tasks[0].path` and `job_name` are the two fields that change
per task), and signed in to the Shannon QC platform with a `@turing-gpt-git.com` Google
account (the site holds its own key — nothing to paste there).

`docker ps --format '{{.Names}}'` is a **budget check**, not a status check — run it before
every launch to see what's already using the shared container budget.

---

## Phase 1 — Understand the task (before touching anything)

**1. Inventory and back up.** Confirm the five mined pieces are present (`task.toml`,
`instruction.md`, `environment/`, `solution/`, `tests/`). `cp -a` the whole folder to a
pristine backup before any edit — never lose the baseline.

**2. Cold-read the instruction and policy, alone.** Read `instruction.md` (and any
governing policy document) end to end, *before* opening the verifiers or the gold answer.
Write down, literally, every guess you have to make to answer it. **Every guess is an
ambiguity, and ambiguity is a defect, never a legitimate difficulty.** This is the single
highest-value 20 minutes of the whole task. Also flag anything handed over for free — a
pointer straight to a column, a named file, a sentence that does the model's thinking for
it. Those are first-round deletions.

**3. Read every input file and how they relate.** For each file, write one line: what one
row *is*, what identifies it, which rule(s) read it. A mined task usually scores 5/5
because someone already settled the hard parts before the model ever saw them — this step
is about finding out what was pre-settled, and by whom, so it can be un-settled fairly.

**4. Hand-trace one case yourself**, then open `solution/` and compare. Sketch your own
rough solution — it gives you an expected answer to sanity-check gold against, and shows
you which parts are genuinely hard vs. mechanical.

**5. Build an independent solver** that reads only `environment/input/` and reproduces the
gold answer. This becomes your fairness-invariant checker and your "does this wrong
reading actually change anything" simulator later — build it now, use it constantly later.

**6. Build the local grading harness** (see below) — sub-second local replay turns every
later question into a cheap experiment instead of an expensive battery.

**7. Delete every verifier tagged `"category": "secondary"`.** Only `"core"` ships. Do
this before the first Oracle run.

**8. Check coverage both directions** (do both — they catch different gaps):
   - **Forward:** from the instruction, write the list of checks it implies. Tick each one
     off against `tests/manifest.json` (or `verifier.json`). Anything on your list with no
     verifier = a coverage gap.
   - **Backward:** for every verifier in the manifest not on your list, decide whether it
     genuinely follows from the instruction, or delete it. A verifier grading something
     the model was never asked to do is unfair and the client will fail it.

**9. Minimize strict regex matching while you're in there.** A verifier that demands exact
wording rejects defensible correct answers — match on the value, not the phrasing. (Full
treatment in `04-verifier-design-and-fairness.md`.)

### Building the local grading harness

```bash
python3 -m venv .venv
.venv/bin/pip install pytest pytest-json-ctrf pydantic jsonpath-ng tenacity
```

Load the manifest with the task's own vendored engine and grade any candidate workspace
directly: `VerifierSpec.model_validate_json` → `effective_weights` →
`SourceRegistry(workspace)` → `verify_definition(v, REG, W[v.name])`.

- **The verdict is `out["result"]["success"]`.** Reading `out["passed"]` silently reports
  0/N for a perfect gold — a classic false alarm. If a result says "impossible," suspect
  your own instrumentation before suspecting the task.
- **CTRF is not useful for per-verifier detail** — pytest parametrization collapses to one
  entry with `retries: N`. Build your own summary by re-grading frozen artifacts directly.
- **Check what the agent can actually see** before treating something as a leak:
  `docker run --rm --network none <image> bash -lc 'ls /app; find / -name "*.json" ...'`
  settles "can the agent even reach this file?" in 30 seconds. Test fixtures are often
  injected only at grading time, not visible to the agent.

---

## Phase 2 — Run the baseline (before changing anything)

Run at least one trial, ideally a full battery, on the **untouched** task, and *read the
trajectories*, not just the score. Feels wasted on a task that already scores 5/5 — it's
actually the most useful run of the build:

- It hands you the model's own solving script — every assumption it made about the data,
  written out as code you can read.
- It shows where the model checks carefully (ground you won't win by planting a trap
  there) and where it moves fast (where something can sit unnoticed).
- It's the control for every later measurement — when a later run fails, you need to know
  whether that's reasoning or something you made unclear, and only a read baseline tells
  you which.

Keep every trajectory and every script the model wrote. You will come back to them at
every subsequent version.

---

## Phase 3 — Harden

This is the core design work. **Do not spend a battery per idea** — reason it through, dry
run it against your independent solver, *then* spend a battery. Full method, the three
lever families, and the honesty rules are in `03-hardening-strategy.md` — read that before
this phase, not after.

Before any battery in this phase:
- Local Oracle replay (via your own harness) must be all-pass.
- Render every declared "wrong reading" as a full deliverable set and confirm your local
  harness rejects each one, and confirm presentation variants (reordered columns,
  reformatted numbers, paraphrased prose) are still accepted.
- Confirm a policy-paste memo (an agent that just restates the policy instead of doing the
  work) fails.

---

## Phase 4 — Oracle, then the battery

> **An online "QC V2" mode can run both the Oracle and the GLM battery for you** in
> roughly 5–10 minutes, as an alternative to the local commands below — useful if your
> machine is slow, though local runs remain valid and can be faster on a strong machine.
> Whether it still expects a local `difficulty/` evidence folder uploaded alongside it was
> unresolved as of the most recent process update — see the "QC V2" section in
> `06-troubleshooting-and-glossary.md` before assuming either way, and confirm current
> behavior with the live tool.

```bash
# Oracle: the known-correct solution through the real verifiers. No model involved.
harbor run -p "$TASK" -a oracle \
  --ve OPENAI_API_KEY="$OPENAI_API_KEY" --ve OPENAI_BASE_URL="$OPENAI_BASE_URL" \
  -o /tmp/harbor-jobs --job-name oracle-<task> -n 1 -y
```

Below 1.0: open `verifier/test-stdout.txt`, find the failing assertion, and decide which
side is wrong — the gold, or the verifier. **`task.toml` is the tiebreaker.** Fix, re-run.
**Re-run the Oracle after every single change** to gold, verifiers, or the instruction —
no exceptions.

```bash
# Difficulty battery — smoke test one run first, then the real battery
harbor run -c glm-harbor-config.json -n 1 -y
harbor run -c glm-harbor-config.json -n <3-minus-running> -k 4 -y
```

- `-k 4` = total attempts (four, current standard). `-n` = how many run concurrently
  (budget-limited, not a total-count limit). Running five is not wrong, but only the first
  four are what get evaluated against the band.
- Read results: `cat /tmp/harbor-jobs/<job>/*/verifier/reward.txt` for the four rewards;
  `harbor view /tmp/harbor-jobs` for the browser UI (`:8080`).
- Per-verifier detail lives in `verifier/verifier_summary.json` — **read whole `items[]`
  entries**, don't grep for `"passed"`; the same verifier can appear under multiple
  groupings and a grep will miscount.
- Verify runs are actually parallel: `docker ps | grep <task>` should show ~4 containers
  at once; otherwise it's silently sequential and ~4× slower than you think.

### Interpreting a battery honestly

| What you see | What it usually means |
|---|---|
| Reward exactly 0.0 | Suspect a crash, not difficulty. Check `exception.txt` / missing `trajectory.json`. A crashed run never counts. |
| Zero artifacts produced | **Void, not failed.** Never score it — re-run. |
| All existence checks failing | Crash, not difficulty. |
| Numerically perfect but scored 0 | **Brittle verifier** — re-grade the frozen artifact with a fixed check. |
| Alternating 0.9 / 0.1 | Bimodal = a coin-flip on an ambiguity. Fix the prompt, this isn't calibrated difficulty. |
| Every failure lands on the SAME wrong answer | A designed firing mechanism working as intended. Good sign. |
| 4/4 passing | Too easy — rejected. Harden more. |
| 1/4, 2/4, or 3/4 passing | **In band. Stop.** Don't keep tuning. |
| 0/4 passing | Submittable, but needs a frontier-model re-run first; worth checking whether it's genuinely hard vs. unfair. |
| Steady 0.15–0.35, no full passes | A genuinely hard task — this is what good looks like. |
| >20% of runs infra-broken | Discard the battery and repair the infra; never average in the noise. |

Classify every non-passing run, in order:
1. Infra (`exception.txt` set, setup failed) → exclude, re-run.
2. Sizing (ran to timeout while work continued) → raise timeout, exclude, re-run.
3. Wedged (stale observations, no progress) → infra, exclude, re-run.
4. Harness limit (stopped for length before deliverables) → check input size, exclude,
   re-run.
5. Completed, no deliverables, sound attempt → **valid failure.**
6. Deliverables present, reward < 1 → normalize and compare against gold.

**Only MODEL failures are signal.** Confirm a failing run's output matches a
*pre-measured* wrong reading — that's what proves the trap fired on purpose rather than by
noise. A verifier-only fix can be re-graded against existing rollouts, no new battery
needed. Only a change to the instruction, the data, or what the verifiers ask for
invalidates existing rollouts and forces a re-run.

---

## Phase 5 — Package

Standard non-connector layout (connector tasks additionally carry `environment/_app/` —
see `06-troubleshooting-and-glossary.md`):

```
task/                        # ← zip THIS folder only
├── task.toml
├── instruction.md
├── review.csv               # human-written QC review — blocks submission if missing
├── qc_report.html           # Delivery Gate's own report — added LAST, client requires it
├── README.md                # change summary
├── tests/                   # manifest.json (or verifier.json for non-connector), test scripts
├── environment/              # Dockerfile, input/, (└ _app/ mirror for connector tasks)
├── solution/
│   ├── golden_trajectory.json   # required — a real reward-1.0 model run, never the oracle
│   └── solve.sh / solve.py
└── evaluations/               # named folders ONLY — nothing loose directly under here
    ├── solvability/r1/        # ONE reward-1.0 run, ANY non-oracle model, never GLM-only
    └── difficulty/r1..r4/     # four independent GLM-5.2 rollouts
```

Hard rules, all costly to get wrong:
- **Never put an oracle run in `solvability/`.** An oracle replays the gold answer, so it
  only proves the verifier can grade the gold — not that a model can solve the task. This
  is the single most common reason a finished bundle gets handed back.
- **Ship no `evaluations/oracle/` folder at all.** The golden is graded from
  `solution/golden_trajectory.json`; the client replays the oracle in their own
  infrastructure. Delete any leftover `evaluations/oracle/` from an older bundle.
- **`solvability/` is not GLM-only.** The bar is one reward-1.0 run from *any* non-oracle
  model or harness. If GLM never reaches 1.0 but another model does, that run is your
  solvability evidence — `difficulty/` is the GLM-specific measurement and still needs its
  own four GLM runs regardless.
- **`stability/` and Layer-2-Stability / Cross-trial-Calibration review rows are Turing's,
  not mine** — the platform stopped requiring them (26 Aug 2026). Leave the folder out
  unless I have *real* fresh-container re-grades of the same frozen answer to ship (two
  repeats agreeing is not stability evidence — don't fake it by copying the four difficulty
  rollouts in there).
- **Never add `evaluations/platform/`** until told the Delivery Gate has been updated to
  accept it — today it scores an unrecognized folder as a failed model run and can sink an
  otherwise clean bundle.
- **Redact before shipping:** no home paths, no job paths, no API keys — grep the
  *extracted* zip, not just the source folder.
- **Finish by extracting the zip to a fresh directory and running the Oracle against that
  copy.** That's the actual reproducibility claim being made to the client.
- Each rollout's `result.json` must carry the exact model name, a boolean `overall_pass`,
  the final answer, the reward, and judge provenance.

`README.md` is the change summary: what changed from the mined baseline to the final
version and why, why the task is genuinely hard, and a justification for any QC flag left
unfixed on purpose. **It must contain no answer** — no graded figure, no population count,
no reference-solution path, no methodology walkthrough. A reviewer finding an unflagged
weakness themselves is worse than one flagged proactively — state known weaknesses
plainly.

---

## Phase 6 — Delivery Gate, review.csv, submit

Full detail in `05-review-csv-and-package-standard.md`. Summary of the sequence:

1. Run the Delivery Gate on the finished bundle.
2. Write `review.csv` through the review form (not by hand) — one row per applicable area,
   every row `PASS` / `FIXED_AND_VERIFIED` / `N/A` (with a reason).
3. Download `qc_report.html` from the gate run, drop it at the task root next to
   `review.csv`.
4. Re-zip, upload as a **new version** of the task.
5. Run the Delivery Gate once more on *that* version.
6. Submit that version.

Submit refuses in a fixed order if greyed out: (1) not a Harbor bundle, (2) Delivery Gate
hasn't passed on this version, (3) score below floor, (4) `review.csv` missing or has
unresolved rows, (5) this exact version already submitted at this score. "Present" and
"resolved" are checked separately on purpose.

A `review.csv` **inside the bundle always wins** over one merely attached on the task
page — if the package ships both, fix the bundle copy.

---

## Phase 7 — If a task comes back rejected

Never edit a submitted task in place. **Upload a new version** — the old version's runs,
reports, and verdicts stay exactly as they were, so the scoring record stays honest. The
loop is otherwise the same as the first submission:

1. Read the pipeline's findings in full — a rejection expands to the complete finding set,
   not just a headline tag.
2. Group findings that share a root cause before making changes — several findings often
   collapse to one real fix.
3. Fix them in the bundle. Only change what's actually defective — don't touch a sound
   task because QC returned `INDETERMINATE` or an obvious capture failure; rerun first,
   and only record a platform-explanation note if the same engine problem repeats.
4. Refresh `qc_report.html` (Phase 6).
5. Update the affected `review.csv` rows to `FIXED_AND_VERIFIED` with the recheck evidence
   recorded — don't overwrite or delete the original finding, add to it.
6. Upload as a new version, re-run the Delivery Gate, submit that version.

Nothing carries across a version bump except the layout override and your own working
notes — runs, dispositioned findings, and report cards are deliberately left behind.

---

## The five things that save the most time (do these by default)

1. Cold-read the prompt and write your guesses down *before* running anything.
2. `docker ps` before every launch.
3. Sync the `_app/` mirror after every edit on connector tasks, via the script — never by
   hand.
4. Re-run the Oracle after every change. 1.0 or it isn't done.
5. Expect 4/4 on the first battery. Hardening is the job, not a setback — and stop the
   moment 1, 2, or 3 of 4 pass.
