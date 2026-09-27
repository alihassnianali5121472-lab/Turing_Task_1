# Breaking GLM-5.2 on audit tasks — a trainer's playbook

*A generic, reusable handbook for taking an auto-mined Harbor "audit" task from trivially-easy
(GLM-5.2 4/4) to in-band (1–3/4), fairly and honestly. It carries three fair lever families, each proven on
a shipped task: a **convention coin-flip** (`gen-g571-otc-label-translation-audit`, mined 4/4 → 1/5), a
**hidden unit-of-analysis** (`code-c485-podcast-autosync-job-audit`, 24 versions → 1/5, gate 100/100), and —
the deepest, most reliable against a capable model — a **recognition fork** (`gen-g1239-...` capitalization
audit → 3/4, aggregate ~2/4; modelled on `fin-f27-earnings-per-share`, the EPS bonus-element task). Every
shipped task: oracle 1.0, in band, all QC findings dispositioned.*

*Author: Najeeb Ahmed — Computer Bench, Turing. Distilled across fin-f27, g77, g304, h69, g571, c485, g1239.*

---

## 0. The laws that govern everything

> **Law 1 — GLM-5.2 correctly EXECUTES anything precisely specified, and DISCOVERS clean structure (joins,
> merges, group-bys) just as reliably. So difficulty cannot come from *more* specification or *more* rules.**

GLM reads a policy, turns each rule into (usually code) computation, runs it, and verifies its own work.
Every *stated* trap — sign conventions, unit scaling, 1-cent edges, tie-breaks, exemptions, dedup — it
handles, because "defensibly specified" is by definition "precisely specified." **Stacking independent rules
does not raise difficulty: N rules = N easy scripts.** Don't grind there.

> **Law 2 — a capable model solves by BOTH scripting AND hand-working, then reconciling. That cross-check
> catches EXECUTION slips but NOT method-RECOGNITION errors.**

This is the deepest lesson (g1239, 14 rebuilds). When the model both scripts a computation and re-derives it
by hand and they agree, it is confident. So a difficulty that lives in *execution* — even a fair coin-flip or
a hidden join — is one the model can self-correct. The difficulty that survives is one where the model must
**recognise which method/treatment applies**, and where the wrong (default) reading is **self-consistent** —
so its script and its hand-working both use the wrong method, agree, and it is *confidently* wrong. The
cross-check *confirms* the error instead of catching it.

> **Law 3 — the harder your eval endpoint's model, the more you must lean on RECOGNITION over EXECUTION.**

Our local GLM endpoint runs ~2 notches easier than the client's calibration endpoint (my repeated observation, maybe wrong). On an easy endpoint, execution levers
(coin-flips, joins, dedup) frequently self-correct to 4/4; the recognition fork is the one family that held
below 4/4. If a fair, well-built execution lever s till reads 4/4 locally, rather than grinding, go for a recognition lever.

**The three fair lever families, in increasing robustness against a capable model:**

| Family | Mechanism | Holds because | Example |
|---|---|---|---|
| **Convention coin-flip** | one fully-specified step with a defensible *wrong* convention the model defaults to (rounding, aggregation order, tie-break, inclusive bound, dedup-before-aggregate) | the intuitive reading diverges from the specified one on tuned data ~30–50%/run | g571 (round-then-sum / half-up) |
| **Hidden unit-of-analysis** | the true audit unit is reached by merging on a hidden key; the obvious grouping over-counts and *self-reconciles to a row count* (false confidence) | the model must *reconstruct* the unit, not read it | c485 (series across feeds) |
| **Recognition fork** *(deepest)* | a treatment/classification the model must RECOGNISE by a domain rule; the naive reading is self-consistent so the cross-check confirms the mistake | execution cross-check can't catch a method-choice error | g1239 (capitalise vs repair, IRS BAR test), f27 (bonus element) |

**Difficulty must be legitimate** — never from ambiguity, hidden info, a flaky environment, or truncation. A
lever is fair *only when the correct reading is fully determinable from the materials* and the model simply
has to recognise and apply it. If two domain experts could defensibly disagree, it's an ambiguity fork (a
defect), not a lever.

---

## 1. The lifecycle of a task

```
claim → pilot the UNCHANGED package → diagnose the mined defect → mine peer tasks for levers
      → rebuild inputs so every graded value must be DERIVED (not looked up)
      → plant ONE lever (coin-flip | hidden-unit | recognition fork) → 3-run pilot to tune
      → de-hint pass, prose AND data (exam analogy) → oracle 1.0 → 4-run bigtok battery (-k 4 -n 4)
      → Delivery Gate + 14-row review.csv → disposition findings → ship + trainer note
```

**Band (current, 4-run):** ComputerBench accepts **1/4, 2/4, or 3/4** fully passing (reward exactly 1.0).
**4/4 = too easy** (keep hardening); **0/4 = submittable but Turing re-runs on another frontier model first.**
A run counts only at reward exactly 1.0. Oracle must always be exactly 1.0.

**Grading harness (current):** ship the **Gen-2 FRACTIONAL + core-gate harness** (`tests/run_verifier.py`):
reward = weighted fraction of verifiers passed, scaled ×0.5 when any `core`-tagged verifier fails. This is
the client-preferred aggregation (fractional over all-or-nothing) and it clears the recurring "all-or-nothing
reward collapse" finding. Peers use it (e.g. g362, 100/100). Gotcha: Harbor parses `reward.json` as a FLAT
map of numbers — write the full payload to `reward_detail.json` and keep `reward.json` `{"reward": x, ...}`
numeric-only, or the trial CRASHES *after* scoring.

**Submission:** run the Delivery Gate on the QC platform; ship a 14-row `review.csv` at the task root (every
applicable check PASS / FIXED_AND_VERIFIED / N/A, high-effort notes citing trials/logs/files). Only tasks
Submitted through the platform with a valid review.csv + accepted Delivery Gate are acceptance-eligible.

---

## 2. Step 1 — diagnose the mined defect (why is it 4/4?)

Cold-read `instruction.md` alone and write your own answer checklist *before* opening the verifiers or gold
(Shannon North Star §2a). Then find why the model wins for free. Usual mined defects:

- **Answer is in the input.** The CSV already has the computed columns; the verifier grades a verdict the
  model can copy.
- **Free points.** A verifier that always passes ("file exists") raises the floor for every run. If you
  can't describe a plausible attempt that *fails* a verifier, it's a free point — it makes the number lie.
- **Everything is stated, nothing is derived.** The prompt hands the method as a recipe.
- **An ambiguity fork masquerading as difficulty.** A mined "1/4" is often two contradictory clauses on a
  boundary case, tuned by row order — a defect, not a lever. Confirm gold is the *only* defensible reading.

Rebuild target: **the model must derive every graded value from raw inputs**, and there must be one place a
correct derivation can still go wrong on recognition/convention.

---

## 3. Step 2 — mine peer tasks *before* building (biggest time-saver)

Don't invent levers from scratch. Open the tracker sheet, find same-family **Completed** (in-band) tasks,
read their hardened task files + trajectories to see *how* they broke the model; read **Discarded** rows to
learn what's unbreakable-or-unfair.

- Look for the *lever*: what single mechanism carries the sub-4/4 result. Confirm from **files, not just  from tracker prose** — notes summarize, files prove.
- Analyze the **hardened, in-band version** of the peer task (the "Modified Task" link) — NOT the trivial
  mined baseline (the plain "Task" link). Confusing the two costs a wasted pass.
- **Access:** however you get the peer task ids/links (agent handing them to
  you), download those task files and trajectories and hand them to your agent assistant for the teardown — or, if
  you have a Google Drive connector with your AI assistant set up, automate the fetch with it. For a heavy zip, delegate the pull to
  a **subagent** so the bulk lands in its context, not yours.
- **Verify the peer's result is FAIR before porting.** Some shipped 1/5s are disguised ambiguity forks; some
  are brittle-memo artifacts (a run that computed everything right but failed one prose regex — read the
  per-assertion detail, don't trust the headline number). Cold-read the peer's policy against its data: "is
  gold the *only* defensible reading?" Spin up one subagent per peer for parallel teardowns.

---

## 4. Step 3 — the reasoning build: load vs breaker

Split mechanisms into two roles. Most are **legitimacy load** (make the audit real derivation, not a lookup
— necessary for a fair non-trivial task, but GLM scripts each → not the breaker). Exactly one is the
**breaker** (a coin-flip, a hidden unit, or a recognition fork). Keep the whole method in a **policy doc**,
not the prompt. Budget effort accordingly: the load makes it honest; **only the breaker moves the pass rate.**

To make the breaker robust, make **findings depend on it** (a Part-A/Part-B compounding inside one
deliverable): if several graded dimensions require the breaker step, an imperfect read fails multiple ways,
not one — so the model can't route around it.

---

## 5. The three breakers in depth

### 5a. Convention coin-flip

One fully-specified step with a defensible *wrong* convention the model reaches for. Classic forks:
**round-half-up vs banker's** (`round(16.65,1)`→16.6 in Python, but 16.7 by print convention),
**round-then-sum vs sum-then-round**, tie-break selection, inclusive-vs-exclusive bound, semver ordering
(1.9 < 1.10), date-boundary arithmetic, **dedup-before-aggregate** (a late-discovered exclusion invalidates
an earlier sum). Tune data so the ±differences accumulate and **flip a verdict at the boundary**: a model
that audits every field perfectly still gets the aggregate wrong unless it reads and applies the exact
convention. *Grade the decision/integer, not the exact float* (see §6). **Amplify by adding coin-flip cases,
not by tightening a tolerance.** Caveat (Law 2): a thorough model may catch a coin-flip via its cross-check —
this family is least robust on an easy endpoint.

### 5b. Hidden unit-of-analysis

The obvious row key is wrong; the true unit is reached by merging on a hidden key, and the wrong grouping
*self-reconciles to a row count* (false confidence). Three conditions, each hard-won on c485:
1. **The deliverable must not hand back the unit.** Ship a **banded-cell aggregate** (bands × findings =
   fixed grid), never one row per unit — a per-row output *is* the unit list.
2. **The data must be realistically MESSY, not synthetic-clean** — see §9. GLM *discovers* clean merges, so a
   too-regular dataset lets it pattern-match the key instead of reasoning it. This is the single hardest
   lesson: **de-hint the DATA, not just the prose.**
3. **Findings must depend on the merge** — so an imperfect merge fails several dimensions.

### 5c. Recognition fork *(the deepest lever — g1239 / f27)*

The one family that reliably survives a cross-checking model on an easy endpoint. The model must **recognise
which treatment/classification applies** by a **domain-expert rule**, where the naive default is
**self-consistent when wrong**. Construction (proven on g1239, modelled on f27):

- **Graft an expert rule.** f27: a share issue priced below fair value carries a *bonus element* (IAS-33), not
  plain cash. g1239: a change is a *capital improvement* vs a *repair* by the IRS tangible-property BAR test
  (Betterment / Adaptation / Restoration) — decided by *what the work does*, NOT its cost or whether it
  "sounds structural." The naive heuristic (*expensive/structural ⇒ capitalise*) is wrong and self-consistent:
  an $18k comparable-part replacement is a *repair*; a $950 new-use conversion is a *capital adaptation*.
- **You can graft an expert rule onto a common-sense domain.** g1239 kept the "change-order approval" theme
  and injected the tax-treatment determination; the expert rule need not be the task's surface subject.
- **Source the rule (and its worked cases) from a REAL authority** — real regs / standards with definitive
  examples. This gives an *authoritative, determinable golden* (the fairness problem real messy data usually
  creates), and de-hints the data automatically (real prose isn't reverse-engineerable — see §9).
- **State the principle, make the model derive the classification.** Put the *principle* in the policy doc
  ("what the sign-off protects", "what makes work a capital improvement"), and DO NOT spell out the
  decision meta-hint ("cost doesn't decide it") — that is the giveaway that turns recognition into a lookup.
- **Keep the golden objectively determinable.** Every case must be unambiguous to a domain expert (oracle
  1.0, no ambiguity fork), while non-scriptable from surface features.
- **Compound it.** Make downstream findings cascade from the recognition (g1239: the approval finding depends
  on the capital-vs-repair call), so a misrecognition is self-consistently wrong across several cells.

Diagnostic that this is *recognition*, not execution: in a failing run's trajectory, the model computes
cleanly but *classifies wrong the same way in its script and its hand-check* — no arithmetic tell. That's the
agreement trap. (Execution levers instead show the model catching and fixing its own slips.)

---

## 6. Step 4 — verifier design (fair, not fussy)

- **File checks forgiving, gold strict.** Memo/existence checks use tolerant *alternation* regex, never one
  fixed phrase — brittle memo strings are the #1 unfair-failure on this family (~50% of client rejections).
  Prefer structural grading from `results.json`/CSV; an LLM judge for prose semantics is *suggested, not
  required*. All graded difficulty lives in the deterministic value checks.
- **Grade the *decision/integer*, not an exact derived float** (avoid narrow-to-golden: no run reproduces the
  gold float and you get 0/4). The lever survives (the decision still flips) but a correct-method run passes.
- **Every numeric check has a tolerance** — money/floats `approx_equals` + `{absolute:0.01}`; integer counts
  exact. Make CSV cell regex quote- and decimal-tolerant (accept `2400`, `2400.0`, `2400.00`).
- **Anchor row-level regex to a UNIQUE row, or add a row-count core check.** A `^CO-XXX,...` regex matches
  ANY line, so a model can stuff several lines per key and pass every per-key check with zero work. Add a
  `core` `csv.inspect_table` `row_count == N` check: N rows + all N per-key checks passing forces one correct
  row each (pigeonhole). (g1239 QC finding.)
- **Count-in-memo checks must be robust, not brittle.** If you require a computed total in the memo, accept
  **digit OR English word**, require only *distinctive* totals, and do NOT bind a count to a keyword by a
  character-distance/proximity window the instruction never states (a small number like "3" collides with a
  standard name like "DCO-3"). Both over-weak and over-strict forms get flagged; digit-or-word on distinctive
  totals is the stable middle. (g1239 iterated this across two gate rounds.)
- **1:1 mapping.** Every verifier traces to a sentence in the prompt/policy; nothing extra. If you add a
  memo-content or row-count requirement, add the sentence to the policy so it traces.
- **No leakage in agent-readable files.** The prompt/policy/inputs the model sees state NO counts, answer, or
  method-with-numbers. `tests/verifier.json` is verify-time only (Dockerfile COPYs `input/` only), so answer
  tokens there are fine. **Do NOT ship a root-level `verifier.json` copy** (Aug-28 directive — it reads as an
  answer-key-discoverable leak). Ship `tests/verifier.json` only; **never a `manifest.json`** (the uploader
  rejects a bundle carrying both).

---

## 7. Step 5 — amplification is bimodal

The **count of breaker cases** (coin-flip cases / trap density / how many findings depend on the structural
or recognition step) is the difficulty dial. The distribution jumps with little in between — expect no smooth
middle. **1/4, 2/4 and 3/4 are ALL fully acceptable — ship a fair result, do not tune it down** (a fair 1/4
is not "risky"; only 4/4 = too easy and 0/4 = escalate are out of band). Reserve re-tuning for out-of-band
results. **Never re-run to fish for a prettier number (curating runs is prohibited)** and **never amplify by
adding unrelated verifiers (denominator gaming)** — amplify the *lever*, keep the *denominator* honest. Run-
to-run variance is real; report the honest count and, if useful, the aggregate across batteries.

---

## 8. The task prompt — engineered for reasoning, de-hinted for fairness

The prompt does three things at once: read like a real colleague's request, force genuine derivation, and
leak **nothing** about the answer or the breaking step.

- The prompt states *what to produce*; the **policy doc** states *how*; **nothing** states the answer.
- Point to each input by name and role; never dump its columns or `/app/input/` paths.
- Name the breaker check in plain words ("once each field's text is typeset", "decide whether the change is a
  capital improvement") — never its convention/rule-application.
- Real human voice, ~90–150 words; a recipe reads as machine-written and becomes scriptable.
- Ask for a memo that *names set-aside records by id* / *summarises the distinctive totals* — gradeable
  without leaking (the model still has to find/compute them), and defeats a hollow-memo shortcut.

> **The exam analogy (governing philosophy):** the question doesn't hand you the method — it checks whether
> you know the method and can reach the answer yourself. The method must be **examinable from the materials**,
> never spoon-fed on the prompt surface.

**The load-bearing guard: de-hinting ≠ deleting the method.** Remove the convention/rule entirely and the
task becomes genuinely *ambiguous* (two defensible answers) → broken, not hard. Keep it fully specified in the
policy; only strip it from the prompt surface and from any answer-leaking tell. (Prompt-stage QC judges read
only `instruction.md`, never the policy — so an "undefined method" flag there is a false positive; it's
defined, in the policy.)

**The de-hint sweep (do it as a dedicated final pass — remove every tell, even minor):**
- Delete leading trap sentences that pre-frame the hard case.
- Move formulas / rules into the policy doc in prose — no boxed formula, no worked numeric example anywhere
  the model reads before it reasons.
- Remove the *meta-hint* that turns recognition into a lookup (e.g. "cost does not decide it").
- Grep **every mounted file, including stale ones**, for convention/answer leakage — a leftover policy copy
  that states the convention stops the coin-flip (all runs land on one answer). If stating a convention "for
  fairness" is itself the breaking point, don't state it on the prompt surface.

---

## 9. De-hint the DATA — and prefer real, curated data

A capable model **reverse-engineers a synthetic generator's regularity**, so prose de-hinting is not enough.

- **Grep every ref/id string for the answer.** Don't embed the unit/answer in identifiers (c485 wrote
  `SER-100000` into every ref; the model just extracted it). Use **opaque tokens** that reveal nothing.
- **Ensure the discriminating key isn't "the only column that repeats/differs."** Add **confounder
  collisions** so other columns coincidentally repeat too; the model must reason about *which* link matters,
  not run a distinct-count. Audit the emitted data: distinct-count per column, check for sequential/constant-
  diff patterns, and **scramble** them into non-monotonic permutations.
- **In a diagnostic trajectory, watch for the model enumerating your templates** ("only a limited number of
  unique patterns — let me handle each") — that means your data is too templated; it hard-codes the ~N
  templates instead of generalising.
- **The strongest de-hint is real data.** Hand-curated scopes/records drawn from a real authority (real regs,
  real filings, real registers) are genuinely varied (no template to enumerate, no generator to reverse-
  engineer) AND carry an authoritative determinable golden. This is how the recognition fork (§5c) sidesteps
  the fairness problem messy data usually creates. Avoid embedded commas / quotes in CSV input fields — a QC
  snapshot parser dropped a quoted row and reported it "missing"; keep inputs unquoted and unambiguous.

---

## 10. Operator discipline (how to drive the build)

*(The principles that ship tasks — distilled, tool-agnostic. These are the difference between a task that
gets discarded and one that ships.)*

0. **"Unbreakable" is a hypothesis, not a verdict.** A build agent (or you) will conclude a task can't be
   broken after a few clean 4/4 runs — usually correctly *for the idea tried so far*. Don't accept it: open
   the task files and the eval trajectories yourself, and hand back a **concrete new axis**, not "try harder."
   The redirections that have overturned "unbreakable": *mine a fresh peer*, *read the trajectory for a leak*,
   *de-hint the prose*, *de-hint the DATA*, *change the KIND of difficulty (execution → recognition)*, *graft
   an expert rule*, *curate from a real source*. An agent's exhaustion is bounded by the ideas it has already
   had; a fresh axis can be worth more than any grinding. (g1239 shipped after ~14 "definitive dead-ends";
   c485 after five discard recommendations — every override was a new axis, most surfaced by a trajectory.)
2. **Read the model's THINKING, not just the reward.** The single most productive diagnostic: open a
   *passing* run's trajectory and ask "why did it win?", a *failing* run's and ask "reasoning slip or
   truncation?". The lever, the leak, and the over-specification all reveal themselves there. This is the move
   that finds what theory misses.
3. **Distinguish execution difficulty from recognition difficulty** (Law 2). If the model self-corrects via
   its cross-check, you have an execution lever — change the *kind*, don't harden the same one.
4. **Name the band, not "hard."** "Make it hard" drifts to 0/4 or 4/4; "1/4–3/4, a run counts only at
   reward 1.0" produces controlled amplification.
5. **Mine peers first, always.** Reuse a proven, *verified-fair* lever; don't reinvent.
6. **Guard the intent.** Keep the rebuild a faithful evolution of the mined task's subject, even while porting
   a peer's structure or grafting an expert rule — a Frankenstein prompt reads unrealistic and the client
   catches it.
7. **De-hint prose AND data, together with max legitimate difficulty** — not as separate phases.
8. **Ground every operational claim in the docs/sheet before acting.** Norms shift (band, harness, root-
   verifier, manifest); re-verify "it's fixed" Slack claims empirically. A green QC score does NOT prove the
   golden is right — re-derive a couple of edge cases by hand against the written policy yourself.
9. **QC your own artifacts adversarially** — the gate runs an adversarial reward-hacking pass. Before
   submitting: reproduce the empty-memo / row-stuffing / duplicate-row shortcuts against your verifier;
   confirm each is core-gated. Catch stale numbers (grep the README/review.csv against the *shipped* battery),
   stray files, and any convention the model shouldn't know leaking into a mounted file.
10. **Cadence:** back up before any risky change → one change per iteration → pilot (`-k 3`) before the full
    battery → oracle 1.0 → 4-run bigtok battery. Keep hands on the expensive runs so nothing is misreported.
11. **Honesty bars are never negotiable:** oracle exactly 1.0; discard truncations/no-file runs (re-run, don't
    count); never curate runs; never fabricate a golden trajectory (promote a real reward-1.0 run and take any
    step-count deduction); dispositions go in the review.csv + README + sheet note — don't invent files.

---

## 11. Tips & tricks the hard way (each cost real time)

- **Truncation is not breakage.** A `reason=length` run with missing deliverables is a token-ceiling artifact
  — excluded as non-evidence. A run that did almost nothing (one command, no deliverables) is an infra
  non-run — discard and re-run; never let it enter the pass rate. **Run the battery bigtok (`max_tokens:
  96000`)** so no run dies to the ~32k reasoning ceiling.
- **Trim mechanical load.** If the model runs out of budget on arithmetic that isn't where it fails, strip it
  — you want the failure to be the *reasoning slip*, not exhaustion.
- **Run the battery in parallel.** Set `-k 4 -n 4` (attempts × concurrency); verify ~4 containers run at once
  (`docker ps | grep <task>`), else it's sequential (~4× slower). Confirm a fresh job dir, `reason=stop`,
  0 exceptions, no `exception.txt` before trusting a count.
- **Archive every job immediately** to a durable evidence folder outside the job output dir — `/tmp` clears
  on restart, and the lead/QC will ask for the trajectories weeks later.
- **Reward-invariant verifier fixes don't need a battery re-run**, but *input* changes (register, prompt) DO —
  re-run so the shipped evidence matches the shipped task. Adding a stricter core check can change a passing
  run's reward if it now fails that check — verify against the actual passing runs, or re-run.

---

## 12. Reusable checklist (tape this to the wall)

1. Cold-read the prompt; write your own answer list; find why it's 4/4 (answer-in-input? free points? all
   stated? ambiguity fork?).
2. Mine completed peer tasks in the same family for the lever — from **files**, verified **fair**, not notes.
3. Rebuild inputs so every graded value must be **derived** from raw data.
4. Assume independent rules fail (GLM scripts them) and clean joins are discovered. Plant **one breaker**:
   **convention coin-flip** | **hidden unit-of-analysis** (banded-cell + hidden merge key + merge-dependent
   findings) | **recognition fork** (expert rule from a real source + self-consistent-wrong default +
   cascading findings). On an easy endpoint, prefer the recognition fork.
5. Specify the convention/rule **fully in a policy doc**, **never on the prompt surface**, **never leak the
   answer or the meta-hint**.
6. Grade the **decision/integer** with tolerances, not an exact float. Anchor rows uniquely or add a
   `row_count == N` core check. Memo count checks: digit-or-word, distinctive totals, no proximity window.
   Every verifier traces to a policy sentence. `tests/verifier.json` only — no root copy, no manifest.
7. File checks forgiving (alternation regex); gold strict; no free points; ship the fractional + core-gate
   harness (flat numeric `reward.json`).
8. Dial difficulty with the **count of breaker cases**; bimodal — no smooth middle. **1/4–3/4 all fine; ship
   a fair result, don't tune it down.** No curating, no denominator gaming.
9. De-hint prose (strip trap sentences, formulas, decimal tells, stated totals, hint columns, meta-hints;
   grep every mounted/stale file) AND data (opaque ids, confounder collisions, scrambled values; prefer real
   curated data; no embedded commas/quotes in CSV inputs).
10. Pilot (`-k 3`) → tune → **oracle 1.0** → **4-run bigtok battery `-k 4 -n 4`**; verify fresh, `reason=stop`,
    0 exceptions, discard non-runs.
11. QC your own bundle adversarially (empty memo, row-stuffing, leakage). Archive the job; back up the task.
12. Delivery Gate + **14-row `review.csv`** (PASS / FIXED_AND_VERIFIED / N/A, high-effort notes); `README.md`
    at root; add `environment/_app/` mirroring instruction.md + task.toml + input/ (no solution/ files);
    fill the sheet + trainer note. Disposition false positives with source evidence; never edit to appease
    one blindly; never fabricate or curate.

---

## Pitfalls that cost the most time (don't repeat)

- **Believing an execution lever's "unbreakable" after clean 4/4 runs** — GLM cross-checks its own work, so
  execution difficulty self-corrects. Change the KIND (→ recognition fork), don't harden the same idea.
- Grading exact derived floats → 0/4 narrow-to-golden. **Grade the decision.**
- Expecting independent rules to compound. **They don't — find the one lever.**
- De-hinting into ambiguity. **Move the method to the policy; don't delete it.**
- Spoon-feeding the convention/meta-hint "for fairness" — that *is* the breaking point.
- Counting truncation / infra non-runs as difficulty. **Run bigtok; discard and re-run.**
- **De-hinting only the prose while the DATA leaks the answer** — audit emitted data (opaque ids, confounder
  collisions, scrambled values); or curate from a real source.
- Analyzing a peer's **mined baseline** instead of its hardened **modified version**.
- Row-level regex matching ANY line → **row-stuffing exploit; add a `row_count == N` core check.**
- Brittle / proximity-bound memo count checks → flagged both over-weak and over-strict. **Digit-or-word,
  distinctive totals only.**
- Treating a fair 1/4 as risky and tuning it down — 1/4–3/4 are all valid; only 0/4 / 4/4 are out.
- Shipping stale evidence — **grep the README/review.csv against the actual shipped battery.**
- Fabricating a golden trajectory or curating runs — **promote a real run; report the honest count.**
