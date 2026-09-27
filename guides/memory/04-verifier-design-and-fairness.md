# Verifier design and fairness

*Sources: A_Guide_About_Verifier_Quality_and_Transformation.pdf, trainGPTCOMMAND.md
(§5), Non-Connector_Task_Standard.pdf (Stages 6–8, 11).*

A verifier is only as good as its ability to survive this test: **would every output that
genuinely satisfies the instruction pass it, and would every substantively wrong output
fail it?** Almost every verifier defect is a violation of one half of that sentence.

## What a high-quality verifier must establish

1. The task is clearly defined.
2. The verifier checks what the task actually requires.
3. Valid solutions are accepted regardless of harmless presentation differences.
4. Substantive errors are rejected.
5. The verifier is stable and reproducible.
6. The environment and harness make the task genuinely executable.
7. Rewards reflect task performance, not infrastructure or evaluator artifacts.
8. An agent cannot obtain a high reward without genuinely completing the intended work.

---

## The seven ways verifiers break (in order of how often they show up)

| # | Failure mode | Typical share | One-line symptom |
|---|---|---|---|
| 1 | Brittle regex / exact-string grading | ~50% | Correct answer rejected over word order, Markdown, a synonym, hyphenation, or numeric notation. |
| 2 | Instruction–verifier mismatch | ~25% | Grades the final chat message (or the wrong file) when the instruction sent output elsewhere. |
| 3 | Infrastructure/harness failures scored as model results | ~15% | API error, verifier timeout, or a harness quirk → scored 0.0 as if it were a real failure. |
| 4 | Undocumented policy assumptions | ~7% | Verifier asserts a rule the instruction never states. |
| 5 | All-or-nothing aggregation | ~3% | 63/64 checks pass → total reward 0.0. |
| 6 | LLM judge missed the trajectory | recurring | Judge claims work didn't happen when the trajectory shows it did. |
| 7 | Dead / hollow deterministic checks | recurring | Empty or disabled buckets silently renormalize weight onto one rubric item. |

**Failure mode 1 alone accounts for roughly half of all verifier defects — start every
verifier review there.**

### 1. Brittle regex / exact-string grading

Typical false negatives: date-format variants ("3 August" vs "3 Aug"); a correct
paraphrase failing a narrow synonym whitelist; negation-blind matching ("this is NOT a
gap" still matches "gap" as a positive finding); plurals/hyphenation breaking exact
matches; a regex alternation collapsing to its weakest branch so a wrong answer slips
through.

**Fix:**
- **Grade the fact structurally, not the prose.** If it's a number or an exact field,
  assert `equals`/`approx_equals` on a parsed JSON value — never grep a memo for it.
- When you must match prose, normalize first (Markdown, hyphens, whitespace, dates,
  numeric notation) then accept an equivalence *set*, not one literal string.
- Prefer an LLM judge for explanations/justifications. If a human reviewer would accept a
  reasonable paraphrase, a regex must not be the grader.
- **Anchor and lengthen every regex you keep.** Use `\b` word boundaries and a stem long
  enough to mean something; require two concepts to co-occur for a stronger check.
- **The weakest branch of an alternation is the strength of the whole pattern** — judge it
  by that branch, not the strongest one.
- Make prose matching negation-aware — evaluate each clause, not a whole section scanned
  for isolated failure words — and keep matches scoped to the correct record/topic so one
  paragraph can't accidentally pass or fail an unrelated one.
- For `contains`, match an identifier ("ESC-105", "2026-06-30"), never a plain English
  word ("interest", "gap") that can appear in an unrelated, negated, or coincidental
  context.

### 2. Instruction–verifier mismatch

The verifier grades a different deliverable than the instruction asked for — most often
the final chat message when the instruction said to write output to a file, or an exact
label/title the instruction never actually specified.

**Fix:** grade the deliverable exactly where the instruction put it (use a file source).
Or change the instruction to explicitly require the content in chat — pick one, don't let
the two drift. Do not require literal titles/labels the instruction never specified;
accept whatever naming the source data itself uses. For every check, be able to quote the
exact instruction sentence that creates the requirement, and confirm the grading target
matches it.

### 3. Infrastructure/harness failures scored as model results

A crashed run, a verifier timeout, or a harness quirk should never silently read as a real
model failure. Distinguish **errored** from **failed**: an errored check should be
recorded distinctly (e.g. CTRF "other," a non-zero exit) and the run marked ineligible —
never folded into the difficulty count as if the model actually got it wrong. A judge
outage in particular must trigger an errored check, never a failure.

### 4. Undocumented policy assumptions

The verifier may only assert what a capable agent could actually infer from the
instruction and the environment. A check encoding a hidden, undisclosed rule fails an
agent that followed the *written* policy literally — and that's the verifier's fault, not
the agent's.

**Fix:** every verifier requirement must trace to an instruction (or governing-document)
sentence. If it doesn't, either add that sentence to the instruction, or delete the check.
Resolve ambiguity *before* it reaches the grader (boolean vs. count, the scope of a notes
section) — make the instruction unambiguous, or accept both readings. Don't re-check in
prose what a structured field already proves (e.g. requiring the digit "3" somewhere near
a keyword in a memo when `results.json` already carries the count).

### 5. All-or-nothing aggregation

Reward is 1.0 only if *every* check passes, so one defective check zeroes an otherwise
materially correct run. Most "63/64 passed, reward 0.0" cases are a defective check, not
an incomplete answer.

**Fix:** fix the underlying brittle/mismatched checks first (that removes most of these).
Where supported, weight and aggregate so one non-critical check cannot zero an otherwise
correct run — reserve hard gates for genuinely load-bearing facts, and make secondary
prose/format checks non-fatal or semantic.

### 6. LLM judge missed the trajectory

The judge must actually read the trajectory and cite observable evidence, not assume.

**Fix:** judge scoped/search calls and value reuse, not only direct literal reads or
literal hardcoding. Never treat null/missing metadata as evidence of *absence* — grade
whether the target record was actually retrieved, or fix the metadata pipeline. Accept
unambiguous aliases, or score identity resolution as its own explicit item. Confirm the
judge's rationale cites the trajectory, and run repeats to make sure verdicts don't flip on
identical deliverables.

### 7. Dead / hollow deterministic checks

A check that never actually runs, or that grades a self-authored transcript the model can
simply fabricate (e.g. checking that a text file says "9 passed" — the model can just type
that string), measures nothing while inflating the apparent rigor of the manifest.

**Fix:** delete or fill empty weighted buckets before shipping — empty SQL/state buckets
silently renormalize their weight onto one remaining rubric item. Execute the real suite
against the model's actual code/output at grading time, don't grep it. Never grade a file
the model authors *about* its own run — reduce that, at most, to an existence check.

---

## Decision framework — pick the right grader

| The requirement is… | Use | Never use |
|---|---|---|
| A derived number / exact field | `equals` (`approx_equals` for floats) on a JSON value | A regex over the memo |
| A money / ratio figure | `approx_equals` with a stated tolerance | Exact `equals` on a float |
| A record exists in a CSV | Row-anchored, quote-tolerant regex | An ID matched anywhere in the blob |
| A concept must appear in prose | Anchored word/phrase regex with a meaningful stem | Bare `contains` on an ordinary English word |
| An explanation/justification is correct | LLM judge citing evidence | A synonym-whitelist regex |
| A behavior is implemented in code | Execute a real test suite | Grep the source |
| A record must NOT be flagged | `not_regex_match` on the delimited field | — |
| Identity / alias resolution | Explicit item accepting valid aliases | Exact-name substring |

When staring at an ambiguous check, find its row here first before inventing a bespoke
comparator.

---

## The three-question test — every check must answer all three, or it doesn't ship

**A. What requirement is this checking?** You must be able to point to the specific
instruction/task-specification sentence.

**B. Why is this check sufficient?** Explain why passing it actually establishes the
requirement.

**C. Why is this check appropriately permissive?** Explain why a valid alternative
solution wouldn't be rejected merely for different wording, ordering, formatting, valid
aliasing, or an equivalent implementation.

---

## Reward-hacking review — do this on every high-weight check

Adversarially review every high-weight verifier: what's the cheapest way to pass without
doing the work? Confirm the agent cannot:

- Hardcode the expected answer.
- Read golden data (check whether it's actually reachable in the container — don't assume).
- Write directly to verifier state.
- Fabricate a placeholder or a self-authored transcript artifact.
- Spoof a required string.
- Satisfy a rubric while skipping a required side effect.
- Exploit stale state left over from a prior run.
- Exploit a path mismatch.
- Manipulate an LLM judge via prompt injection hidden in an input.
- Get credit without actually retrieving the underlying evidence.

Also specifically watch for **row-stuffing**: a per-key regex that matches *any* line lets
an agent dump many candidate rows and pass every per-key check for free. Pair per-key
checks with an exact `row_count == N` core check so the pigeonhole principle forces one
correct row per key.

---

## Spread the suite across four evidence sources — never lean on one

- **Trajectory** — proves the work actually happened (right records retrieved, right side
  effects issued).
- **Deliverable** — the files the instruction actually named; primary content should live
  here.
- **DB / environment state** — proves side effects actually landed; the strongest
  anti-spoof source.
- **Final answer** — only when the instruction explicitly asks for content in the chat
  reply.

Aim for a small, structured, load-bearing gate on the deliverable or DB state, backed by
trajectory checks and secondary checks. Don't let one weak surface decide the whole score.

---

## The grade-time recomputation suite (the single most valuable check type)

A pytest (or equivalent) module that, at grading time:
- reads the task's raw inputs and **recomputes the whole answer under the policy itself**;
- asserts the delivered table matches row-for-row, **read by column name** (order
  independent);
- asserts delivered summary figures match the recomputation;
- does **not** import the solver, read `solution/`, or read the manifest;
- is wired into the actual test entry point, so the reward genuinely depends on it.

This closes the hardcoded-constant fabrication path, makes per-row grading order
independent, and removes the need for brittle per-row regexes. Verify it actually works by
building a submission with the reference memo paired with a deliberately wrong table — it
should still fail.

---

## Engine mechanics worth remembering

- Use the engine's built-in parsers wherever possible (`json.read_file`,
  `csv.inspect_table`, `xlsx.read_cell`) rather than hand-rolled parsing.
- JSON checks: anchor JSONPath to a single unambiguous match.
- CSV content: grade rows via a **tolerant** regex template — anchored per line,
  order-free (multiline mode), optional quotes, flexible whitespace.
- **Pair every row-level presence check with a total row/key count** to stop an agent from
  hedging by dumping every possible answer (same principle as row-stuffing above).
- Compare parsed numbers numerically (`approx_equals`/`equals`) with stated tolerances,
  never as strict strings.
- **Always pair a "must not contain" check with a positive existence check** — otherwise an
  empty file passes the negative check for free.
- Validate paths with `lstat` before grading — reject symlinks, directories, oversized
  files as a matter of course, not as an afterthought.
- Fold pure existence checks into their corresponding content checks rather than letting
  them inflate a proportional denominator as separate "free points" (see
  `03-hardening-strategy.md` and `06-troubleshooting-and-glossary.md` for the "free
  points" concept in full).
- Ensure every declared check actually executes and fails the specific decoy it was
  designed to catch — a check that never fires is dead weight (failure mode 7).
- Cap text extractions at whatever the engine's limit is (commonly ~90,000 characters) —
  don't exceed it, and route large tabular content to JSON summaries or
  `inspect_table`-style counts instead of raw text extraction.

## Judge-based (LLM rubric) checks

Use an LLM judge only when a deterministic check genuinely cannot express the
requirement, and document *why* in the task's README. Because a single check flip can zero
an otherwise-perfect strict-pass run, judge stability is paramount:

- **Prompt design:** ask one coarse, unconditional, binary yes/no question about
  substance. Never grade layout or length. Never enumerate answer-key specifics in the
  prompt. Explicitly state that extra content beyond the minimum is tolerated.
- **Context control:** the judge reads only the full, untruncated artifact it is grading,
  through its native source. Never pass the golden key to the judge.
- **Validate before shipping:** probe the rubric heavily — it must pass every real correct
  output and fail naive/wrong outputs consistently across repeats, without flipping
  verdicts.
- **Environment:** use a provider-valid model ID, override it with the judge-model
  environment variable at runtime rather than hardcoding a literal model string (a
  hardcoded judge model ID is a known flag risk). If the network is otherwise no-network,
  open a specific route to the judge host rather than opening the whole environment.
  Judge outages trigger an errored check, never a scored failure (see failure mode 3).

---

## Seventeen patterns that pass your golden and fail a correct agent

These are the classic ways a verifier accidentally over-specifies *presentation* instead
of *substance*. Each one should be tolerated unless the instruction explicitly pins that
exact representation.

| Pattern | You wrote | Agent wrote | Fix |
|---|---|---|---|
| Numeric format fixed by string compare | `1000` | `1000.00` | Parse and compare numerically, or explicitly state the format. |
| Float exact equality | `0.30000000000000004` | `0.3` | State precision; compare with a tolerance. |
| Unstated rounding rule | 2.5 → 2 | 2.5 → 3 | State half-up or half-even explicitly. |
| Date format | `2024-01-15` | `15/01/2024` | State the exact format, with an example. |
| Enum case sensitivity | `none` | `None` | State the literal(s) verbatim in the instruction. |
| Boolean/null representation | `false` | `False`, `0`, `""`, `null` | State the exact token for each. |
| Currency/unit decoration | `1000` | `$1,000.00` | State whether symbols/separators are allowed. |
| Row order dependence | input order | sorted by id | Compare as a set, or state the sort order. |
| Column order dependence | your order | alphabetical | Compare by column name, or state the order. |
| JSON key order or value type | `"count": 8` | `"count": "8"` | State JSON types; assert on parsed values. |
| Encoding / line endings | LF, no BOM | CRLF or a BOM | Normalize before comparing; state the encoding. |
| CSV quoting style | `a,b,c` | `"a","b","c"` | Tolerate quotes in the template; never a rigid line match. |
| Whitespace / trailing newline | none | trailing newline | Strip before comparing. |
| Prose graded by keyword | one word | a synonym/other wording | Grade the figures inside the prose, never vocabulary. |
| Unstated tie-break/precedence | your resolution | the other defensible one | State the canonical rule, or accept both. |
| Unstated boundary (greater vs at least) | your side | the other side | State inclusive/exclusive in words. |
| Extra files or intermediates | none | a scratch/skipped file | Assert only on the named deliverables. |

---

## Two local test suites to run before any battery

### The equivalence suite — a perturbed-but-still-correct output must still pass

Perturb the golden output in ways that *preserve meaning*, then confirm the verifier still
accepts it:

- Shuffle data row order.
- Reorder columns, keeping headers, wherever the instruction leaves order open.
- Reorder JSON keys.
- Quote every CSV field.
- Convert LF to CRLF; prepend a UTF-8 BOM.
- Add or remove a trailing newline; pad fields with surrounding spaces.
- Reformat integers as `N.0` and back, and add/strip trailing decimal zeros, wherever the
  format is genuinely open.
- Paraphrase every sentence of a prose deliverable while keeping all the figures.
- Delete an unrequired intermediate file; add an unrelated scratch file to the workspace.

### The breaking suite — a genuinely wrong output must now fail

Break the golden output for real; each break must fail on the *specific* check written for
it (not incidentally on a different one):

- Flip one classification/answer value.
- Delete one data row; append one spurious row.
- Change one summary count by one.
- **Flip the boundary-case row to the other side** — run this one first; boundary rows are
  the most common source of an unwritten rule or an underspecified instruction.
- Empty every deliverable file.
- Delete one deliverable entirely.
- Replace all output with `{}` or a bare header.

If any breaking-suite perturbation still passes, the corresponding requirement is
ungraded — fix that before touching difficulty at all.

---

## Using the transform script instead of hand-prompting

When a verifier suite needs a broad rewrite against the failure taxonomy above, use the
provided transform tooling rather than hand-writing a rewrite prompt:

```bash
# Dry run — writes a draft, touches nothing live
python verifier_transform/apply_transform.py --task "<task path>"

# Review transformed_tasks/<task_name>/, then apply for real (keeps a .bak)
python verifier_transform/apply_transform.py --task "<task path>" --write
```

- `--lean` for large connector tasks that would otherwise time out.
- `--render-only` to inspect the filled prompt without calling the model.
- `--folder <dir>` to run the same transform concurrently over every task under a
  directory.

The script validates shape automatically (every regex compiles, every `deterministic.path`
is a valid JSONPath, any rubric-type verifier carries the required judge config, no
weighted bucket is left empty, coverage only references verifier names that actually
exist) — but **the validator checks shape, not judgment**. It will not catch a weakened
correctness check or an invented requirement.

**Never accept transformed output blindly, even when validation passes.** Always: review
every changed check against the decision framework and the three-question test above,
re-run the Oracle (must still be exactly 1.0), and run the reward-hacking review on every
high-weight check that was touched.
