# Hardening strategy: how difficulty actually gets created

*Sources: task-approach-guide-updated.docx, breaking-playbook-trainer-copy.md,
trainGPTCOMMAND.md, Non-Connector_Task_Standard.pdf (Stage 3).*

**Read this whole file before editing a prompt, a fixture, or a verifier.** Everything
below is pattern/mechanism knowledge, generalized across many shipped tasks and several
trainers' independent notes. None of it is a recipe with fixed numbers to copy —
**your task's data is different, so the specific trick that worked on someone else's task
will very often not fire on yours.** What transfers is the *mechanism*; the concrete
values, columns, and thresholds have to be rebuilt from your own fixture every time.

---

## The three laws (why most first attempts land at 4/4)

> **Law 1 — GLM-5.2 correctly executes anything precisely specified, and discovers clean
> structure (joins, merges, group-bys) just as reliably. Difficulty cannot come from *more*
> specification or *more* rules.**

A model reads a policy, turns each stated rule into (usually) a script, runs it, and
checks its own work. Every *stated* trap — sign conventions, unit scaling, penny-edges,
tie-breaks, exemptions, dedup — gets handled correctly, because "defensibly specified" is
by definition "precisely specified." **Stacking N independent rules produces N easy
checks, not N× difficulty.** Don't grind there.

> **Law 2 — a capable model solves by BOTH scripting and hand-working, then reconciling.
> That cross-check catches execution slips but not method-recognition errors.**

This is the deepest and most expensive lesson available. When a model both scripts a
computation *and* re-derives it by hand, and the two agree, it becomes confident — and
correctly so, most of the time. So a difficulty that lives purely in **execution** (a fair
coin-flip convention, a hidden join) is one the model can self-correct: it scripts it one
way, hand-checks it, and if there's any doubt, the second method flags the first. The
difficulty that survives is one where the model must **recognize which method or
treatment applies in the first place**, and where the wrong (default/intuitive) reading is
**self-consistent** — so its script *and* its hand-check both use the wrong method, agree
with each other, and it is *confidently* wrong. The cross-check confirms the error instead
of catching it.

> **Law 3 — the harder your local eval endpoint's model behaves, the more you must lean on
> recognition over execution.**

A local eval endpoint often runs noticeably easier than the client's own calibration
endpoint. On an easy endpoint, execution-type levers (coin-flips, hidden joins, dedup
order) frequently self-correct back to 4/4. If a fair, well-built execution lever still
reads 4/4 locally, the fix is usually **not** more grinding on the same lever — switch to a
recognition-type lever instead.

---

## Two things that look like hardening and are not

**Adding rules or instructions.** A rule clear enough to be fair is a rule the model turns
into a few lines of code — it reads it, copies it out, runs it. What you actually buy is
**boundary risk**: runs failing on `>` vs `≥`, on which side of an as-of date a record
falls, on a phrase two honest readers could take two ways. That's vagueness dressed up as
difficulty. It points straight back to the sentence you added, and review will fail it as
an ambiguity, not credit it as difficulty.

**Adding data volume.** A script crunches two hundred thousand rows as fast as two
hundred. More rows of the same pattern moves nothing. If, after two build iterations, you
notice every change so far has been "add more of the same," stop turning that dial — it's
not going to move the pass rate.

---

## Where difficulty actually comes from: put it in the data, and in recognition

Go back to the baseline trajectory (Phase 2 of the workflow) and read what the model's own
script *assumed* about the shape of your data. Every script makes shape assumptions
quietly. List them, then make the real data honestly **not** like that — in a way the
policy still correctly describes and a careful reader could still work out. What's
available to exploit depends entirely on your specific task's data; that's the point, and
it's also why someone else's specific trick usually won't port over untouched.

### Three fair, reusable lever *families* — in increasing robustness against a capable model

| Family | Mechanism | Why it holds (or doesn't) |
|---|---|---|
| **Convention coin-flip** | One fully-specified step with a defensible *wrong* convention the model defaults to (rounding rule, aggregation order, tie-break, inclusive/exclusive bound, dedup-before-vs-after-aggregate). | The intuitive reading diverges from the specified one on tuned data some fraction of the time. **Least robust** — a thorough model's cross-check can catch a coin-flip, especially on an easy endpoint. |
| **Hidden unit-of-analysis** | The obvious row key is wrong; the true audit/analysis unit is only reached by merging on a hidden key, and the naive grouping *self-reconciles to a plausible row count* (false confidence). | The model must *reconstruct* the unit, not just read it off a column. Requires realistically messy data — a too-regular synthetic dataset lets the model pattern-match the key instead of reasoning about it. |
| **Recognition fork** *(deepest, most robust)* | A treatment/classification the model must *recognize* via a domain rule, where the naive/default reading is *self-consistent when wrong*. | Execution cross-checks can't catch a method-*choice* error — the model computes cleanly but classifies wrong the same way in both its script and its hand-check. This is the family that survives a cross-checking model even on an easier endpoint. |

**All three require the correct reading to be fully determinable from the disclosed
materials** — the model just has to recognize and apply it. If two competent, careful
readers could defensibly disagree, that's an ambiguity fork (a defect to fix), never a
lever to ship.

### Building a recognition fork (the most durable option)

1. **Graft a real, external, expert rule onto the task's domain** — not an invented
   in-house rule. Source it (and its worked examples) from an actual authority: a real
   regulation, standard, or policy with definitive worked cases. This buys you two things
   at once: an *authoritative, determinable* golden answer, and data that's naturally hard
   to reverse-engineer (see the data de-hinting section below).
2. **State the *principle* in the policy document, never the decision meta-hint.** E.g.
   state what a rule is *for* or what it protects — never spell out the tell that turns
   recognition into a lookup (a sentence like "cost alone does not decide this" is itself
   the giveaway; leave it out).
3. **Make the naive/default heuristic plausible and wrong on your specific data** — the
   heuristic a fast reader reaches for first should look reasonable and fail on at least
   some of your records.
4. **Compound it.** Wire downstream findings so they depend on the recognition call — a
   misrecognition should then be self-consistently wrong across several graded cells, not
   just one, so the model can't route around it by accident.
5. **Keep the golden objectively determinable** — every case must be unambiguous to a
   domain expert (Oracle stays 1.0, no ambiguity fork), while being non-scriptable from
   surface features alone.

**Diagnostic that a lever is genuinely "recognition," not "execution":** in a failing run's
trajectory, the model computes cleanly, but classifies the same way (wrong) in *both* its
script and its independent hand-check — there's no arithmetic tell to catch. (An execution
lever instead usually shows the model catching and correcting its own slip somewhere in
the trajectory.)

---

## What worked reliably as a first try: exact boundary cases

Independent of lever family, **values sitting precisely on a stated, strict comparison**
are a strong, cheap, and fully fair lever: a record exactly at a cap and one unit over; a
duration exactly at a limit and one over; a validity window ending exactly on the
reporting/as-of date — *with the comparison direction stated in the policy* ("may not
exceed," "more than 10," "in force means on or before, and not yet ended").

The distinction that decides fairness:
- **NEAR a line**, decided by rounding or floating-point fuzz → **always unfair. Forbid
  it.**
- **ON a line**, with the comparison direction stated in words → **decidable with
  certainty**, tests whether the model actually read the comparison, and is one of the
  strongest levers available.

Build boundary cases into the fixture from the *first* build, not after several rounds of
failed attempts at something more elaborate.

### Other load-bearing rules

- **A decoy must reconcile to the *wrong* answer.** A decoy whose own summary total
  matches the *correct* grain is an aid, not a trap — a model's trajectory will use it as a
  self-check and be *helped* by it. Verify this before shipping any decoy.
- **Define, never narrate.** Replace "a later record supersedes an earlier one, so the
  earlier one does not apply" with a flat definition: "in force at a date means the latest
  one dated on or before it." The moment a policy *warns* that a tricky case exists, the
  model resolves it correctly — narration is itself a leak.
- **Never signpost in the prompt.** A memo requirement that lists the hard parts is a
  checklist of your own traps.
- **Verify every trap is load-bearing before shipping it.** Simulate the wrong reading in
  your independent solver and confirm it actually moves a graded value. A trap that
  changes nothing is decorative — remove it. (On more than one real build, *every*
  declared trap initially produced identical output figures — this check catches that.)

---

## Legitimacy load vs. the breaker — split your effort

Most of what makes a task *realistic* (forcing genuine derivation rather than a lookup:
cross-referencing sources, computing intermediate values, applying stated rules) is
**legitimacy load** — necessary for the task to be fair and non-trivial, but the model will
script each individual piece, so load alone does not move the pass rate. Exactly **one**
mechanism should be the actual **breaker** (a coin-flip, a hidden unit, or a recognition
fork). Budget effort accordingly — the load makes the task honest, only the breaker moves
the number.

To make the breaker robust, make **multiple graded findings depend on it** (a
compounding effect inside one deliverable) — an imperfect read of the breaker should then
fail several graded dimensions at once, not just one, so the model can't accidentally route
around it.

---

## Fairness invariants — assert these in code, and fail the build if they don't hold

A violation here should break your local build/harness immediately, never surface later as
a mysterious battery result:

- No ties in any "latest wins" rule — a tie makes a row genuinely undecidable, which is
  broken, not hard.
- No value sits *near* (as opposed to exactly *on*) a threshold; on-the-line values are
  whole numbers or exact dates only.
- No single unit trips two rules at once unless the policy explicitly states the
  precedence between them.
- Float arithmetic agrees with exact (`Fraction`) arithmetic on every comparison that
  matters to a graded outcome.
- Derived ages/durations are never within 1 of a boundary unless they are *exactly* on it.
- Every unit resolves to exactly one record in force for each lookup it needs — no
  dangling or multiply-resolving lookups.
- Sibling rows agree — all rows belonging to one unit carry the same key fields.
- An independent solver reproduces every graded figure and every output row from the raw
  inputs alone, with no reference to the gold files.
- Any sequential/iterative rule uses a **total** order (no ties possible) and is
  **monotone** (removals are never restored), so it provably terminates on one answer.

---

## De-hinting: the data leaks as much as the prose, usually more

A capable model **reverse-engineers a synthetic generator's regularity**, so cleaning up
the prompt alone is not enough.

**De-hint the prose** (a dedicated final pass, not a running edit):
- Delete leading sentences that pre-frame the hard case.
- Move formulas/rules into the policy document as prose — no boxed formula, no worked
  numeric example anywhere the model reads before it reasons.
- Remove any meta-hint that turns recognition into a lookup.
- Grep **every mounted file, including stale/leftover ones**, for convention or answer
  leakage — an old policy copy that states the convention you're relying on kills a
  coin-flip lever outright (every run lands on the same, now-obvious, answer).

**De-hint the data** (equally important, more often missed):
- Grep every identifier/reference string for the answer — don't let an ID encode the unit
  or the answer (a model will just extract it). Use opaque tokens.
- Make sure the discriminating key isn't "the only column that repeats or differs" — add
  confounder collisions so other columns coincidentally repeat too, forcing the model to
  reason about *which* relationship matters rather than running a distinct-count.
- In a diagnostic trajectory, watch for the model **enumerating your templates** ("there
  are only a limited number of patterns here — let me handle each one"). That's a signal
  your data is too templated; it's being hard-coded around instead of generalized over.
- **The strongest de-hint is real data.** Hand-curated records drawn from a real source
  (real filings, real registers, real regulatory text) are genuinely varied — no template
  to enumerate, no generator to reverse-engineer — and carry an authoritative, determinable
  golden answer for free. This is how a recognition fork avoids the fairness problem that
  messy synthetic data usually creates. Avoid embedded commas/quotes inside CSV fields —
  they can be mis-parsed downstream and misreported as "missing" data.

---

## Amplification is bimodal — don't over- or under-tune

The **count of breaker cases** (how many coin-flip cases, how many findings depend on the
structural or recognition step) is the actual difficulty dial, and the resulting
distribution tends to jump rather than move smoothly — don't expect a gentle middle.

- **1/4, 2/4, and 3/4 are all fully acceptable outcomes. Ship a fair result — do not keep
  tuning a fair in-band result down** because it feels too easy or too risky.
- **Never re-run to fish for a prettier number** (curating runs is prohibited).
- **Never amplify by adding unrelated verifiers** (denominator gaming) — amplify the
  *lever*, keep the *denominator* (what's actually graded) honest.
- A four-trial sample carries roughly one trial's worth of noise. One unusually high
  battery next to two in-band ones is more often a sampling question than a real
  difficulty regression — it costs one more battery to find out, not a redesign.

---

## The gotchas that cost the most batteries

**The task is in band, but secretly unfair:**
- Two honest methods give different answers → fix the data so both agree, and keep values
  *off* thresholds generally, reserving on-threshold values for the deliberate boundary
  lever above.
- Every field a grade depends on must agree with itself across the *whole* input set —
  assert this *after* the last edit, not before it.
- Dates break stories: a record after the as-of date, an override dated after the thing it
  overrides, an order column that disagrees with its own timestamp. Assert all three,
  every time, after every edit.
- No two rules should be able to apply to the same input simultaneously without a stated
  precedence, or a run can be right about one and still wrong on the grade.
- **The last edit can create a new ambiguity in a rule you didn't touch.** Re-check every
  rule after the final edit, including ones you believe you left alone.
- The real test for all of the above is the *trajectory*, not the score. A run that
  reasons correctly and then writes something like "the spec would need to say X" is
  telling you the task is unfair, regardless of what it scored.

**The artifacts describe different tasks:**
- Prompt, solution, tests, manifest, and environment drift on filenames, paths, columns,
  or counts. Reconcile these on purpose — a green Oracle does not prove they agree, only
  that the gold matches the verifier's expectations.
- Confirm the solution actually follows the *required method*, not just that it earns the
  reward.
- The reference answer's own memo/write-up is not graded by anything — nothing catches it
  if it repeats the exact mistake the task is built around. Read it line by line against
  the policy and recompute every stated figure from the inputs yourself.

**The measurement itself is wrong:**
- One battery is not a result. Report a pass rate only once every failure is traced to a
  named model error.
- Timeouts, empty runs, provider errors, and memo-only failures are not "kills" — triage
  every failed run to a specific step and a specific wrong value before excluding it.
- Judge a failure by the delivered *file*, not by what the model said while it was working.
- Several edits at once make a result impossible to explain — change one thing per
  version, and batch all content edits before freezing for a battery (each edit voids the
  prior evidence).
- Pass rates multiply, not add — a second trap layered onto an already-working task often
  collapses straight to 0/5. Count traps that actually *fire*, not traps you merely
  planted.

**Nothing is moving:**
- After two build iterations with no change in outcome, stop turning the same dial — the
  tell is that every attempt so far has moved the same lever in the same way.
- Volume is never a rung on this ladder. More of the same pattern moves nothing, ever.

---

## Operator discipline

- **"Unbreakable" is a hypothesis, not a verdict.** A few clean 4/4 runs on one idea does
  not mean the task can't be hardened — it means *that specific idea* didn't work. Before
  accepting "unbreakable," try: a genuinely fresh data angle, reading a trajectory
  specifically for a leak, de-hinting the prose, de-hinting the data, and — most
  productively — changing the *kind* of difficulty (execution → recognition). Real shipped
  tasks have needed over a dozen rebuilds before the right axis was found; the point isn't
  to expect that every time, it's that persistence pays specifically when you change the
  *axis*, not the intensity.
- **Read the model's thinking, not just the reward, every time.** Open a *passing* run and
  ask "why did it win?" Open a *failing* run and ask "reasoning slip, or truncation?" The
  lever, the leak, and any over-specification all reveal themselves in the trajectory in a
  way the score alone never will.
- **Name the band, not "hard."** "Make it harder" drifts toward either 0/4 or 4/4;
  "1/4–3/4, and a run only counts at reward exactly 1.0" is a target that actually produces
  controlled amplification.
- **Guard the intent.** Keep any rebuild a faithful evolution of the mined task's original
  subject, even while grafting in an expert rule or a structural pattern learned from
  elsewhere — a Frankenstein prompt reads as unrealistic, and that gets caught in review.
- **De-hint prose and data together**, as one pass aimed at maximum legitimate difficulty —
  not as two separate phases done at different times.
- **Ground every operational claim in the current docs, not memory.** Norms shift (the
  band, the harness, which manifest file ships) — re-verify anything that sounds like an
  old rule of thumb before relying on it.
- **A green QC score does not prove the golden is right.** Before shipping, re-derive a
  couple of edge cases by hand against the written policy yourself, independent of any
  tooling.
- **QC your own bundle adversarially before submitting.** The Delivery Gate itself runs an
  adversarial reward-hacking pass — get there first: try the empty-memo shortcut,
  row-stuffing, and duplicate-row shortcuts against your own verifier and confirm each one
  is actually blocked (core-gated). Grep the README/`review.csv` against the *shipped*
  battery for stale numbers.
- **Cadence:** back up before any risky change → one change per iteration → small pilot
  battery to tune → Oracle 1.0 → full four-run battery. Stay hands-on with the expensive
  runs so nothing gets misreported.
- **Honesty bars, never negotiable:** Oracle exactly 1.0; discard (don't count) truncated
  or no-file runs and re-run them; never curate which runs get reported; never fabricate a
  golden trajectory — promote a real reward-1.0 run instead, even if that means taking a
  step-count hit; every disposition goes into `review.csv` + `README.md` — never invent
  supporting files.

## Truncation and infra are not signal

- A run cut off for `reason=length` with missing deliverables is a token-ceiling artifact,
  not evidence — exclude it, don't count it.
- A run that did almost nothing (one command, no deliverables) is an infra non-run —
  discard and re-run; never let it enter the pass rate.
- If your local endpoint has a low reasoning-token ceiling, size the run configuration
  ("bigtok"/high `max_tokens`) so no run dies to token exhaustion before you conclude
  anything about difficulty.
