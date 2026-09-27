# Troubleshooting, infra traps, and glossary

*Sources: How-to.docx, trainGPTCOMMAND.md (§8), Non-Connector_Task_Standard.pdf,
"Practical Approach for Task's Acceptance" all-hands, 11 Sep 2026 (Gemini notes +
transcript).*

## QC V2 — process update from the 11 Sep 2026 all-hands

This all-hands is the **most recent** process source in this memory set (dated after all
the "as of 24–26 Aug 2026" notes elsewhere). Where it conflicts with an older file here,
treat this section as current — but also treat parts of it as **genuinely still
unresolved** (marked below), not settled fact.

**The strategy content covered (task understanding → data relationships → baseline
battery → trajectory read → hardening → pen-and-paper testing) is a restatement of what's
already in `03-hardening-strategy.md`** — same method, same order, nothing new there.
What's new is tooling/process:

- **The QC tool now has an online "V2" mode** that can run the Oracle and the GLM battery
  **online**, returning a 4-run result in roughly 5–10 minutes, instead of requiring a
  full local `harbor run` battery (which can take an hour or more depending on machine
  power). Local runs still work and can be faster on a powerful machine — this is a
  convenience option, not a replacement requirement.
- **Whether the local `difficulty/` (GLM) evaluation folder must still be uploaded for V2
  processing was actively disputed in the meeting and left unresolved** — one presenter
  demonstrated processing without it, another reported the tool rejecting a submission
  without it. **Verify current behavior yourself before assuming either way**, and prefer
  whatever the live tool/team guidance says over this note.
- **False positives in the online tool are common and are explicitly not a blocker.**
  Reported example: a "missing stability folder" flag on a task that genuinely has one.
  Team guidance: if a false positive isn't blocking Submit, **submit anyway** — backend
  finalization re-runs the real validations independently of the tool's own flags. Don't
  burn time chasing every non-blocking flag to green.
- **If a battery run locally passes but the same task scores 4/4 ("too easy") online**,
  check once for a setup/config mismatch between local and online. If it's still 4/4 after
  one honest recheck, **stop spending effort on it** — hand it to a **partlet** for a spot
  check and move to another task rather than continuing to grind.
- **Token exhaustion + partial pass is an open question, not settled guidance.** The
  existing rule elsewhere in this memory set ("token exhaustion alone is not valid
  difficulty signal, but a run that solves the task inside budget while others exhaust
  tokens producing nothing *does* count") was restated as the working position, but a
  specific edge case — one run fully passes, two partially pass, one fails on token
  exhaustion at a 96K limit — was explicitly **escalated to higher management for
  confirmation** and unresolved as of this meeting. Don't treat either answer as final;
  check for a settled ruling before leaning on this case.
- **Infrastructure errors** (a check that never reaches a verdict, a run stuck for an
  hour) — log them through the **QC portal**, which is the primary tracking mechanism.
  If told a specific stuck task is "final" (no further action needed), that's a legitimate
  instruction, not something to keep poking at.
- **Yellow-marked / flagged tasks** that show remaining issues are resolved centrally by
  an automation script run by the backend/QC team — **no contributor action is required**
  on those, including if one gets rejected again after being marked yellow. Don't spend
  effort trying to manually patch a yellow-marked task; let the automation pass over it.

### A new role: "partlet"

A **partlet** is a team member/reviewer to route uncertain cases to — spot-checking a
task's readiness for finalization, reviewing detailed logs on an ambiguous failure (e.g. a
disputed token-exhaustion case), or judging whether a task that scores inconsistently
between local and online runs is actually good enough to proceed. When you've addressed an
issue once and are still unsure, the guidance is: **don't keep grinding solo — hand it to
your partlet and move to the next task.**

### Two likely transcription artifacts (not new terminology)

This source is an auto-generated meeting transcript and contains a couple of apparent
mis-hearings — don't treat these as real terms if you see them again elsewhere:

- **"Harvard check"** almost certainly means **Harbor check** (the `harbor` CLI/tool used
  throughout this whole memory set) — there's no other context suggesting an actual
  "Harvard" system.
- **"YOLO" task** and **"yellow-marked" task** were used interchangeably by the same
  speakers in the same exchange about tasks that passed an older QC version but got
  rejected under V2 — almost certainly one term ("yellow") mis-transcribed as "YOLO." Both
  refer to the same yellow-marked-task handling described above.

---

## Known errors and fixes

| Symptom | Cause & fix |
|---|---|
| QC site: "daily limit reached: N/100 gate runs in the last 24 hours" | Gate runs are rationed per reviewer: **100 gate runs** and **200 review.csv checks** per rolling 24h, **4 runs in flight** at once. Nothing's wrong with the task — the count frees up as older runs age out. Batch runs and free dry runs aren't counted. Ask an admin to raise the limit if genuinely needed. |
| Healthcheck failed (rc=7, in_start_period=True) repeating at startup | Normal — retries up to 40×. Only a real problem if it never passes; that's memory pressure, so lower concurrency (`-n`). |
| "all predefined address pools have been fully subnetted" | Leftover Docker networks from finished trials. `docker network prune -f`, then re-run. |
| Same, but after killing a job | Killed jobs leave exited containers whose networks survive the prune. `docker ps -a --filter status=exited` → `docker rm` the dead `gen-*__env-main-1` containers → prune → relaunch. |
| `AgentSetupTimeoutError` after 360s | Concurrent containers slow the agent's install step. Add `--agent-setup-timeout-multiplier 3`. |
| `NonZeroAgentExitCodeError` / "text part chatcmpl-... not found" / "Z.responses is not a function" | Used the literal provider name `openai` (e.g. `-m openai/glm-5.2`) — it gets special-cased into an OpenAI-only API path. Use the actual custom-provider model string instead. |
| Every judged/rubric verifier scores 0 | `JUDGE_MODEL` env var wasn't set. The proxy doesn't serve arbitrary models without it. |
| Model output truncates mid-reasoning, deliverables missing | Reasoning token ceiling hit. Raise `max_tokens` in the model config (commonly to ~96000, "bigtok"). |
| Your edit had no effect on the scores | On connector tasks: the `_app/` mirror wasn't synced. See "The mirror rule" below. |
| A run scored 0.0 and you assumed it was hard | Check `exception.txt` / missing `trajectory.json` first — it likely crashed. A crashed run is never difficulty signal. |
| A run stops without producing deliverables | Token ceiling exhaustion is **not** valid difficulty signal by itself — don't count it. But if one rollout solves the task within the ceiling while others run out producing nothing, *that* is a real, countable model failure. |
| Reasoning cut off mid-thought | Prefer to avoid it, but it's acceptable as long as at least one run in the battery succeeded; cut-offs aren't counted as failures either way. |
| Dread re-running the battery after a verifier change | You may not have to — a **verifier-only** change can be re-graded against existing rollouts. Only a major change to the instruction or to what the verifiers ask for invalidates existing rollouts. |
| QC V2 flags something false (e.g. "missing stability folder" on a task that has one) | Known, common, non-blocking false-positive class as of the 11 Sep 2026 all-hands. If it doesn't block Submit, submit anyway — backend finalization re-validates independently. Log it in the QC portal if you want it tracked, but don't burn a session chasing it to green. |
| Local battery passes; the same task scores 4/4 ("too easy") online | Check once for a local/online config mismatch. Still 4/4 after one honest recheck → stop, hand to a partlet for a spot check, move to another task rather than re-grinding the same task repeatedly. |

**Never run `docker image prune -a`** — it deletes the shared multi-GB benchmark-base image
that everyone depends on.

## Other infra traps that cost real time

- **Background launches can get silently killed.** A job started with `nohup ... &` from a
  tool call can die within ~90 seconds when the process group is torn down as the call
  returns. Use the harness's own proper background mechanism instead.
- **Contention starves runs.** Count containers and check available memory before trusting
  any result — two concurrent batteries on a small Docker allocation produce timeouts with
  no real artifacts, which then look like model failures but aren't.
- **Never `pkill -f "<runner>"`** — it isn't scoped to your job and can kill someone
  else's. Kill containers by task name only.
- **Check for the agent process, not CPU%**, when deciding if a run is alive. A stalled
  container can sit at 5–13% CPU from its own healthcheck loop and look busy while doing
  nothing. `pgrep -c <agent>` returning 0 means it never actually started.
- **Prune networks and exited containers between runs.** A compose teardown can segfault
  and leave networks behind until the address pool is exhausted and every subsequent trial
  dies at startup.
- **Digest-pin the base image, then re-run the Oracle** whenever the pinned image changes
  — a new base image can silently change behavior.
- **Agent setup may fetch its runtime over the network per container**, even if you
  believe you pre-baked the dependency — check what the setup script actually branches on
  before assuming a dependency is already satisfied.

## The mirror rule (connector tasks — silently invalidates everything if missed)

On **connector** tasks, `instruction.md` and `tests/manifest.json` also exist under
`environment/_app/` — and the `_app/` copy is the one that actually runs inside the
container. **Edit only the top-level copy and your change effectively never happened** —
you'll re-run and get identical scores, and lose time wondering why.

Sync it by running the package's `sync_app_mirror.sh`. **Never hand-edit the mirror.** If
the script is missing from a package, flag it — don't try to build the mirror manually.

**Non-connector tasks have no `_app/` mirror** and iterate directly on
`tests/verifier.json` instead. That file must be rewritten to `tests/manifest.json` as the
*last* packaging step, with the Oracle re-run immediately afterward against the rewritten
file.

## "Free points" — the one concept worth internalizing early

Every verifier is worth **1/N** of a run's score. A verifier that always passes ("the
output file exists") is therefore a **free point** — it raises the score floor for *every*
run, whether the model did any real work or not.

If 4 of 12 verifiers always pass, no run can score below 0.33, and an apparent "0.48" is
really about 0.22 of actual accomplished work. That inflates the reported difficulty and
makes the whole battery lie about what's actually hard.

**The test:** if you can't describe a plausible attempt that would *fail* a given
verifier, it's a free point. Content checks already fail cleanly on a missing file, so a
separate `*_exists` check is almost always a free point in disguise — fold it into the
content check instead. Target floor: **0**.

The flip side is equally bad: don't move a task into band by *adding* verifiers rather
than adding genuine difficulty. That's denominator gaming, and reviewers specifically look
for it (see the reward-hacking review in `04-verifier-design-and-fairness.md`).

**Related trap:** never grade the model's self-report. Recompute the graded fact from the
artifact it actually produced, not from a number it wrote into its own summary JSON.

---

## Glossary and identifier systems

### Core package files

| File | What it is |
|---|---|
| `task.toml` | The design doc / source of truth. When the gold answer and a verifier disagree, this file is the tiebreaker. |
| `instruction.md` | The work request, written as if a real colleague sent it — one paragraph of context, the asks, exact deliverable filenames. No `/app/input/` paths, no dumped column lists, no step-by-step recipe. |
| `tests/manifest.json` (connector) / `tests/verifier.json` (non-connector, pre-packaging) | The list of verifiers: name, source (what to read/query), assertion (what counts as correct). |
| `solution/` | The known-correct answer plus the script that produces it — what the Oracle run executes. |
| `solution/golden_trajectory.json` | A **real model run** that scored reward 1.0 — never the oracle itself. Required for packaging. |
| `environment/` | Dockerfile + `input/` (everything the agent may see) + on connector tasks, the `_app/` mirror. |
| `review.csv` | The human review record — see `05-review-csv-and-package-standard.md`. |
| `qc_report.html` | The Delivery Gate's own report, added to the bundle last, required by the client. |
| `README.md` | The trainer's change summary — what changed and why, no answers. |

### Severity levels (Non-Connector Standard)

- **Illegal** — the verifier grades something the disclosed materials never established. A
  correct agent literally cannot win this way. The package is returned automatically.
- **Blocking** — the package is returned, with both fix branches named.
- **Warning** — noted; fixed unless you record a specific reason to keep it as-is.
- **Policy** — a recorded decision rather than a pass/fail check.

### Rule inventory identifier families (Non-Connector Standard)

The full standard cites every rule by a short code + number (e.g. `VER-8`, `DIF-7`,
`INS-2`). If you see one of these codes in task documentation or a QC finding, here's what
family it belongs to:

| Prefix | Domain |
|---|---|
| `DIS` | The disclosure boundary — what the agent can legitimately see/know. |
| `INS` | Instruction content — required, prohibited, and edge-case rules for `instruction.md`. |
| `FIX` | Input fixture construction — how source data must be built. |
| `GLD` | Golden-answer derivation and validation. |
| `DIF` | Difficulty and coverage design (the sanctioned-pattern table, the pass band). |
| `VER` | Verifier construction — design principles, engine capabilities, scoring rules. |
| `LLM` | Judge-based (LLM rubric) check design and validation. |
| `HAR` | Harness and reward-shape construction. |
| `ENV` | Dockerfile / environment / network-mode rules. |
| `TOML` | `task.toml` field requirements. |
| `EXP` | Diagnostic probes, degenerate-solver measurement, state-spoofing runs. |
| `EVD` | Evidence layout, trial identity, replay validation, exclusions. |
| `TRL` | Trial classification (infra vs. sizing vs. valid failure) and comparison. |
| `SEC` | The security sweep (credentials, network calls, injected payloads, destructive ops). |
| `PKG` | Package artifacts — folder structure, README, `review.csv`, change propagation. |
| `RVW` | Reviewer-specific rules (in the separate Reviewer Document). |

### Team-role glossary

- **Partlet** — a reviewer/teammate you route uncertain cases to: spot-checking a task
  near finalization, reading detailed logs on a disputed failure, or judging whether a
  task that scores inconsistently between local and online runs is good enough to move
  forward. Once you've addressed an issue once and are still unsure, hand it off rather
  than keep grinding solo (see the QC V2 section above).
- **Yellow-marked task** — a submitted task the QC pipeline has flagged with a remaining
  issue that the backend/QC team resolves centrally via an automation script. Requires no
  contributor action, including if it's rejected again after being marked yellow. (Also
  appears mis-transcribed as "YOLO task" in at least one meeting source — same thing.)

### Verifier-pattern identifier families (also Non-Connector Standard)

- **O1–O17** — the "seventeen patterns that pass your golden and fail a correct agent"
  (presentation-format traps). Full table in `04-verifier-design-and-fairness.md`.
- **E1–E14** — the equivalence suite (perturbed-but-correct outputs that must still pass).
- **B1–B8** — the breaking suite (genuinely wrong outputs that must now fail).
- **T1–T15** — the difficulty "stumping tips" (hide the key case, craft realistic lures,
  supply conflicting sources with a stated tiebreaker, etc.) — see
  `03-hardening-strategy.md` for the generalized version of these.

### Difficulty-pattern names (Non-Connector Standard, Stage 3)

Sanctioned patterns for where a genuine, fair crux can live: **unit-of-analysis trap**
(the row key is one level below the unit the rules actually govern), **stale authority**
(use the revision in force at the relevant date, not the latest one), **wrong-default
lure** (the obvious heuristic is almost right, wrong on a few records), **latent crux** (a
real rule that never fires on the visible sample), **misdirection with a disclosed
tie-breaker** (a source that disagrees, plus a sentence saying which one governs),
**entangled rules** (one fact changes two rules at once), **ordering assumption** (data
isn't in the order a reader assumes). These map onto the lever families in
`03-hardening-strategy.md` — treat that file as the working version of this table.

### Status/version dates worth remembering (may drift further — verify current)

- Four GLM runs (not five) as the battery size, and `1/4–3/4` as the accepted band —
  effective 25 Aug 2026.
- Score parameter removed entirely — 25 Aug 2026.
- `review.csv` collapsed from seven columns to five (dropped
  `verification_performed`/`verification_result`/`evidence`, folded into
  `what_to_record`/`review_notes`) — 24 Aug 2026.
- Layer 2 Stability and Cross-trial · Calibration stopped being required rows — 26 Aug
  2026.
- `terminus-2` harness runs accepted alongside `opencode` — 19 Aug 2026.
- An online "QC V2" mode capable of running Oracle + GLM battery online (~5–10 min) exists
  and is recommended over local-only runs, though local runs remain valid — noted as of
  the 11 Sep 2026 all-hands. Whether the local `difficulty/` folder is still required for
  V2 processing, and how a specific token-exhaustion-plus-partial-pass battery should be
  scored, were both **open/disputed as of that same date** — confirm current status before
  relying on either.

These are exactly the kind of details that keep moving — treat any date-stamped rule as a
snapshot, and confirm against current team/platform guidance before relying on it for a
live task.
