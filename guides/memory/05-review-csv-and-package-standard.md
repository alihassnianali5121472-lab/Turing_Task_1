# review.csv, the 14 review areas, and package delivery standard

*Sources: A_Guide_about__review_csv_.pdf, How-to.docx, trainGPTCOMMAND.md (§10),
Non-Connector_Task_Standard.pdf (Stages 0, 13–15, Appendix A.15 PKG).*

> **Process-detail note:** these source documents were written at different times and
> occasionally disagree on the fine print (exactly which rows can be `N/A`, whether
> Stability is required). Where they conflict, this file follows the **most recently
> dated** guidance (How-to.docx, dated 24–26 Aug 2026 in several places) and flags the
> older framing as superseded. **Always double-check the live review form and current team
> guidance before trusting a static date in any of these files** — this whole area is one
> where the rules visibly move over time.

---

## What review.csv is, and who writes it

`review.csv` is the auditable record of what was checked, what failed, what changed, and
whether the fix actually worked. It is attached to the task package at every review
checkpoint and lives at the task root.

**It must be written by a human, describing this specific package — not generated.** The
whole reason the client requires it is that a person actually looked. A generic-sounding
row ("checked verifiers, looks fine") is functionally indistinguishable from a row nobody
wrote, and the client's own automated reading of the file specifically checks whether the
notes describe *this* package or could have been copy-pasted onto any task.

### What I (Claude) can and cannot do here

- **Cannot:** draft the `status` or `review_notes` columns as if I were the reviewer. That
  defeats the purpose of the artifact.
- **Can, and should:** help assemble the evidence a human reviewer needs to write real
  findings quickly — fill in candidate `change_made` text (the exact correction, named by
  file) and `what_to_record` text (what was run and what came back, with bundle paths) as
  drafts for you to confirm, point to the specific bundle paths / trial IDs / verifier
  output that back a claim, and hand you a per-area evidence pack. You still write (or at
  minimum personally verify and finalize) `status` and `review_notes` yourself.

### Don't hand-write the CSV — use the review form

The form enforces the exact header and the full area list, so its output can't be
rejected on shape:

1. Open the review form and sign in with the Turing Google account.
2. Paste the Drive link to the **extracted task folder** (the folder, not the zip).
3. Fill Status, Review notes, Changes made, and What to record for each applicable area.
4. "Submit and upload to Google" writes `review.csv` straight into that Drive folder, or
   "Download review CSV" gives you the file to place yourself.
5. To edit later: paste the same folder link, use "Fetch review CSV" to reload what's
   already written.
6. **Confirm the file ends up inside the ZIP you upload.** Attaching it on the task page
   unblocks Submit, but only the archive that's actually uploaded reaches the client. A
   `review.csv` bundled *inside* the ZIP always wins over one merely attached to the task
   page — if a package somehow ships both, fix the bundled copy.

---

## The five audit layers, at a glance

| Layer | What it means | Human role |
|---|---|---|
| **Layer 1** | Task-package validity and semantic consistency — do `task.toml`, `instruction.md`, `solution/`, `tests/`, inputs, outputs, and environment jointly define one coherent, realistic, gradable task? | **Human review required.** |
| **Layer 2** | Checked-in vendor QC evidence — difficulty rollouts, a non-oracle passing trajectory (solvability), repeated grading for stability. | Difficulty: **human.** Solvability, Stability: programmatic/Turing-run — see ownership note below. |
| **Layer 3** | Oracle validation — the oracle solution scores exactly 1.0 in both E2B and Modal. | Your own local oracle run (1.0) is yours; the cross-mode replay is Turing's. |
| **Layer 4** | Model-and-harness runtime evaluation — do saved rollouts look reasonable/grounded, do tools/files/connectors work, are failures genuinely task-related rather than infra artifacts? | **Human review required.** |
| **Layer 5** | Qualitative analysis of every Layer-4 trial — rollout reasonableness, verifier fairness, environment/connector behavior, artifact integrity, failure attribution. | **Human review required.** |

## Current ownership split (12 areas are yours)

**Yours, with a written finding:** Layer 1 (Package consistency, Clarity and scope,
Realism and leakage), Layer 2 Difficulty, Layer 3 Oracle Mode *(your own oracle-1.0
evidence — still required, even though the cross-mode replay is Turing's)*, Layer 4
(Environment and files, Connectors/MCPs/CLIs, Deliverables and artifact quality), Layer 5
(Verifier coverage and fairness, LLM judge consistency, Reward hacking and
exploitability).

**Turing's — you may leave these two blank/omitted, they no longer block submission:**
Layer 2 Stability, Cross-trial · Calibration. If you *did* happen to look at either, write
it down anyway (it gets read, it just can't hold up Submit).

**Turing's, fully, N/A no matter what an older doc says:** Layer 2 Solvability (this one
is genuinely not yours to evidence at all).

> An older merged guide describes a simpler rule — "put N/A in every cell for Solvability,
> Stability, and Oracle Mode, no explanation needed." That framing predates the split
> above and specifically gets Oracle Mode wrong for current process: your own oracle run
> is real evidence you own, so that row should carry a real `PASS`/`FIXED_AND_VERIFIED`
> finding, not a bare N/A. Trust the ownership split above over the older three-way N/A
> rule.

---

## The 14 review areas — what to check on each

Use this as the working checklist. Each becomes exactly one row in `review.csv` (extra
rows are fine if something outside the standard 14 needs recording — held to the same
bar).

**Layer 1 · Package consistency** — Do `task.toml`, `instruction.md`, every file under
`solution/`, and every file under `tests/` describe the same executable, gradable task?
Compare required outputs, paths, formats, inputs, services, timeouts, scoring rules, and
expected values across all four. Red flags: undeclared required files/fields,
contradictory paths/formats, verifier-only requirements, stale manifests, missing
dependencies. Record: cite the conflicting files and the exact requirement, explain the
impact, propose one canonical fix.

**Layer 1 · Clarity and scope** — Is the task well defined for an agent that only sees the
declared instruction and environment? A capable agent should identify the goal, available
evidence, required deliverables, and completion criteria without guessing hidden rules.
Red flags: ambiguous terms, missing units/date ranges, unstated assumptions, multiple
plausible answers, hidden precision/formatting demands. Record: the ambiguity, plausible
alternate interpretations, and the smallest fix that resolves it.

**Layer 1 · Realism and leakage** — Does the task resemble real useful work without
exposing the answer or relying on artificial traps? Check instruction, packaged inputs,
seeded data, filenames, environment image, solution visibility, test fixtures. Red flags:
contrived identifiers/traps, impossible access assumptions, answer-bearing filenames,
golden files mounted into the workspace, toy output with no practical value. Record:
whether it's realistic, any leakage/contrivance found, a more natural framing if needed.

**Layer 2 · Difficulty (the 4 GLM runs)** — Is the task difficult for GLM-5.2? Pass
criteria: GLM-5.2 passes ≤ 3 of 4 runs (current band — see `02-workflow-lifecycle.md`).
Red flag: passes ≥ 4 of 4 (too easy). Record: how many of the 4 runs passed, with pointers
to the reward files.

**Layer 2 · Solvability** *(Turing's — N/A)* — Not yours to evidence.

**Layer 2 · Stability** *(Turing's — optional/blank allowed)* — Not required to block
submission; note it if you looked.

**Layer 3 · Oracle Mode** — Your own local oracle run scores exactly 1.0. (The cross-mode
E2B/Modal replay is Turing's, but your own evidence is still a required row.)

**Layer 4 · Environment and files** — Can the agent reliably use the sandbox,
dependencies, inputs, workspace, and required output paths? Check trajectory setup steps,
filesystem operations, dependency installs, logs, produced artifacts, exceptions, E2B
metadata. Pass: inputs present/readable, tools run, writes persist, the verifier sees the
intended artifacts, and failures are task-related rather than infrastructure-related. Red
flags: missing files, incompatible architecture, dependency-build failures, permission
errors, outputs written to the wrong workspace, artifacts disappearing before
verification. Record: name the failed interaction and classify it (packaging, sandbox,
dependency, harness, or agent error).

**Layer 4 · Connectors, MCPs, and CLIs** *(N/A on any non-connector task — say why)* — Are
intended connectors discoverable, usable, and sufficient? Check declared MCP/CLI metadata,
tool discovery, calls/responses, auth behavior, pagination, state changes, verifier-side DB
checks. Red flags: service never starts, missing auth, wrong endpoint, incomplete
pagination, unusable schemas, silent tool errors, a verifier expecting state the connector
can't actually create. Record: connector name, operations and their outcomes, affected
trial, and whether the issue is data/service/auth/interface/agent-usage.

**Layer 4 · Deliverables and artifact quality** — Are the requested outputs complete,
realistic, and usable in their declared formats? Check the instruction's output list
against actual workspace artifacts, golden files, JSON structure, and any
PDF/DOCX/spreadsheet/HTML/Markdown/text deliverables. Red flags: placeholder or malformed
files, JSON-only grading that ignores a required rich output, polished-looking artifacts
lacking substance, a verifier checking the wrong or stale path. Record: missing/weak
artifacts, distinguishing content-quality vs. format-validity vs. path vs.
materialization issues.

**Layer 5 · Verifier coverage and fairness** *(most important review area)* — Does the
verifier measure the task requirements accurately and proportionately? See
`04-verifier-design-and-fairness.md` for the full mechanics. A reward of 1.0 is evidence,
not proof of task quality — a fractional or zero reward may reflect an agent error, a task
defect, a verifier defect, or an infra problem. Record: each verifier's justification
against the specific instruction sentence it checks; identify ambiguous, defective, or
missing checks; quote the requirement in your own words; propose a concrete fix.

**Layer 5 · LLM judge consistency** *(N/A if the task has no judge-based check)* — Are
qualitative judgments grounded in the actual artifact and stable enough to trust? Check
vendor stability repeats, judge model/config, artifacts, verifier stdout. Red flags:
factually wrong rationale, the judge overlooking present content, a rubric demanding
unstated detail, inconsistent repeats, invalid model/provider configuration. Record: the
disputed rubric item, artifact evidence, repeat behavior, recommended rubric/judge
configuration change.

**Layer 5 · Reward hacking and exploitability** — Could an agent earn a high reward
without genuinely completing the intended task? Run the reward-hacking review from
`04-verifier-design-and-fairness.md`. Red flags: agent reads golden data, writes directly
to verifier state, mimics expected strings without doing the work, exploits unchecked
fields, skips a required side effect and still passes. Record: the exploit path, affected
checks and reward impact, severity, and an acceptance test that closes it.

**Cross-trial · Calibration** *(Turing's — optional/blank allowed)* — Across the four
trials, is the difficulty/behavior profile healthy (neither trivially universal nor
universally blocked, plausible model differences, understandable fractional
scores/exceptions)? Note it if you looked; not required to block submission.

---

## The review.csv file format

Header, exact, five columns, in this order:

```
review_check,status,review_notes,change_made,what_to_record
```

| Column | Required content |
|---|---|
| `review_check` | The applicable layer/check name (loosely matched on case/spacing/`·`, but keep the standard wording). |
| `status` | `PASS`, `FIXED_AND_VERIFIED`, or `N/A`. |
| `review_notes` | What was inspected and the conclusion — a running history of the review, specific enough that someone else could confirm the review without redoing it. "Looks good," "fixed," "reran" are not sufficient notes. |
| `change_made` | The exact correction made, named by file. Blank **only** when nothing needed changing. |
| `what_to_record` | The evidence, tied to the "What to record" guidance for that check above — bundle paths, trial/harbor IDs, reward files. |

### Status definitions

- **`PASS`** — checked, already correct, nothing changed. `review_notes` and
  `what_to_record` both must say something concrete (what was looked at, what was run to
  confirm). `change_made` stays empty.
- **`FIXED_AND_VERIFIED`** — a real problem was found, the package was changed, **and the
  original check that exposed it was re-run with the issue confirmed gone.** All five
  columns are filled in, `change_made` included — a blank `change_made` here contradicts
  the status. Making the change is not enough by itself; the fix has to be *verified*.
- **`N/A`** — the check genuinely doesn't apply (the connector row on a non-connector
  task, the judge-consistency row when there's no judge-based check). `review_notes` must
  say why. **An `N/A` with nothing beside it is treated as unresolved and blocks Submit.**

**There is deliberately no `FAIL` status.** A row you can't honestly resolve means the task
isn't finished, not something to record as failing — you only submit tasks you've actually
finished, so every row lands positive by the time it ships.

### Quoting

Any cell containing a comma must be wrapped in double quotes; a literal double quote
inside a cell is doubled (`""`). Writing the file in a spreadsheet and exporting as CSV
handles both automatically — hand-editing raw CSV text is where "could not be read as
CSV" errors usually come from. (This is exactly why the review form, not manual editing,
is the recommended path.)

### A worked pair of rows

```csv
review_check,status,review_notes,change_made,what_to_record
Layer 1 · Package consistency,PASS,"task.toml, instruction.md and tests/manifest.json name the same three deliverables (recliner_fit_audit.csv, recliner_fit_memo.md, results.json). No drift, nothing renamed.",,"Read all three side by side and compared declared deliverable names, paths and types."
Layer 2 Difficulty,FIXED_AND_VERIFIED,"First GLM-5.2 battery passed 4/4. Cause: environment/input/invoices.csv shipped a pre-aggregated total_due column, so the model copied a number instead of computing it. Rewards after the fix in evaluations/difficulty/r1..r4/verifier/reward.json; harbor trial 8f2c1e.","Dropped the total_due column from environment/input/invoices.csv, re-ran the _app mirror sync, and rewrote verifier 4 to recompute the total from the line items.","Oracle re-run plus a fresh 4-run GLM-5.2 battery from clean containers. Oracle 1.0; GLM-5.2 passed 2 of 4 — rewards 1.0, 1.0, 0.83, 0.50."
"Layer 4 · Connectors, MCPs, and CLIs",N/A,"This is a native (non-connector) task — no connector manifest, no environment/mcp/ folder, so there is nothing here to review.",,
```

---

## Fix-and-verification protocol (for every failed check, in order)

1. Record the original failure and its evidence.
2. Record the exact change made.
3. Re-run the relevant check — via the automated QC check or a Harbor re-run.
4. Recheck any other backend, verifier, artifact, or rollout affected by the change.
5. Add the post-fix evidence and reference the original finding.
6. Mark the row `FIXED_AND_VERIFIED` **only** when the original issue no longer
   reproduces.

If the re-run fails or exposes a *new* issue, keep the item open and add the new result to
the notes — **never overwrite or remove the original finding.**

---

## Delivery / acceptance checklist

A task is ready for acceptance only when:
- Every applicable review check has a recorded status.
- Every failure has a documented cause and disposition.
- Every claimed fix has been re-run and verified.
- No original failure was overwritten or removed — new findings are added, never swapped
  in for old ones.
- The task runs through the required Harbor paths with no undocumented workarounds.
- `review.csv` has exactly one row per applicable layer/area, and every row is `PASS` or
  `FIXED_AND_VERIFIED` (or a properly-explained `N/A`).

A task with unresolved failures, unverified fixes, missing references, or incomplete notes
is not ready for acceptance, regardless of what a QC report percentage says.

---

## Package/delivery standard reference (from the full Non-Connector Task Standard)

### What you submit

One zipped folder, named for the task. Nothing else at the top level; nothing loose
directly inside `evaluations/`. Under `tests/` you may add harness scripts, a fixture
generator, and a discrimination harness — nothing else may be added anywhere:

```
<task-folder>/
├── task.toml
├── instruction.md
├── review.csv              # one row per applicable review area
├── qc_report.html          # the QC tool's report at the submitted checksum
├── README.md               # the change summary
├── environment/
│   ├── Dockerfile
│   └── input/               # everything the agent may see besides the instruction
├── solution/
│   ├── solve.sh
│   ├── files/                # the golden deliverables
│   └── golden_trajectory.json  # a real model reward-1.0 run, never the oracle
├── tests/
│   ├── verifier.json
│   ├── test_outputs.py
│   ├── test.sh
│   └── rl_world_verifiers/    # the vendored engine, unmodified
└── evaluations/
    ├── solvability/r1/         # one reward-1.0 run, any model, never the oracle
    └── difficulty/r1/ .. r4/   # four GLM-5.2 runs
    # oracle/rN/ and stability/rN/ are added later by Turing's team — never ship them yourself
```

### Core package rules (condensed from the PKG rule set)

- **Strict folder structure** — exactly the layout above; no scratch files, `.bak`
  backups, editor swap files, caches (`.pytest_cache`, `__pycache__`), `.DS_Store`, or
  unreferenced data anywhere in the package.
- **Deliverable name consistency** — every deliverable name spelled identically across
  `instruction.md`, `verifier.json`, `solution/files/`, and the `artifacts` list in
  `task.toml`.
- **README requirements:**
  - Logs every change from the mined baseline, file by file: what it was, what it is now,
    why it changed.
  - Every figure matches its supporting evidence file exactly — read values directly from
    files, never quote from memory, only describe shipped evidence.
  - Written for the reviewer: explicitly states what the agent cannot see (confirms
    `solution/` and `tests/` are absent from the agent's container).
  - Declares the reward shape, network mode, judge model (with reasoning), and the
    expected wrong readings — declared *before* running the trial battery, not
    reverse-fitted after.
  - No conflicting numbers anywhere in the package for the same quantity, even in
    historical notes — describe history qualitatively instead of with two different bare
    numbers.
- **`review.csv` honesty** — exactly as described above; every note cites a specific file,
  run, or check.
- **`qc_report.html`** — must be the unedited output generated by the QC tool at the
  submitted checksum, not hand-edited or stale.
- **`golden_trajectory.json`** — a real agent run scoring exactly 1.0, based solely on the
  instructions, distinct from the oracle run, containing no references to golden files or
  verifier logic.
- **Change propagation** — any edit to the instruction, inputs, verifier, golden files,
  harness, or Dockerfile changes the task's checksum and voids every existing trial,
  trajectory, and QC report. Regenerate all of it, don't patch around a stale checksum.
- **Mined template cleanup** — remove and log every inherited mining-template defect:
  ungradeable instructions ("must be your final action"), harness meta-lines, empty
  artifact lists, unpinned base images, boilerplate justifications, improperly-weighted
  existence-only checks, dead test variables, overly simplistic fixtures.

### Getting `qc_report.html` into the bundle (last step, always)

1. Run the Delivery Gate on the finished bundle.
2. Download `qc_report.html` from that run.
3. Drop it at the task root, next to `review.csv`.
4. Re-zip, upload as a **new version**.
5. Run the Delivery Gate once more on that version, and submit *that* one.

The report you ship therefore describes the version immediately before it — that's
expected, and it's what the client wants: the QC record traveling with the package, not a
file that references itself.
