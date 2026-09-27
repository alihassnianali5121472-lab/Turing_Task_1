# Turing Harbor Task Trainer — Operating Memory

You are working alongside me on **Turing / ComputerBench Harbor benchmark tasks**: mined
task packages that must be reviewed, hardened, verified, and packaged for a client that
trains frontier models. This file (and the files it imports) is the accumulated,
hard-won knowledge for that job. Read it as operating instructions, not background color.

Detailed material lives in `memory/` and is loaded automatically below. Treat each
imported file as equally binding — this file is the index and the non-negotiables,
not the whole story.

@memory/01-mission-and-success.md
@memory/02-workflow-lifecycle.md
@memory/03-hardening-strategy.md
@memory/04-verifier-design-and-fairness.md
@memory/05-review-csv-and-package-standard.md
@memory/06-troubleshooting-and-glossary.md

---

## What "a task" means here

One task = one folder = one ZIP. It is a realistic work package (instruction + input
files + a Docker environment) that an AI agent (GLM-5.2, the client's target model) must
complete, and an automated **verifier** grades the output. My job on each task is to make
it **functional, fair, and appropriately difficult** — then prove that in a package the
client's QC pipeline and a human reviewer can both audit.

Tasks arrive already "mined" (auto-generated) and are almost always too easy (4/4 GLM
passes) and often have some defect (leaked answers, ambiguity, broken verifiers). The
work is diagnosis and repair, not authorship from scratch.

**Two task families exist and they are NOT interchangeable:**
- **Non-connector tasks** — self-contained, files-only, no external services. Governed by
  the full stage-by-stage standard in `05-review-csv-and-package-standard.md`.
- **Connector tasks** — involve MCPs/CLIs/external services, have an `environment/_app/`
  mirror of `instruction.md` + `tests/manifest.json` that must be kept in sync via
  `sync_app_mirror.sh` (never hand-edited — see `06-troubleshooting-and-glossary.md`).

Always ask or check which family a given task belongs to before assuming a rule applies —
category-specific rules (e.g. the `_app/` mirror, the Connectors review row) only fire for
one family.

---

## The two gates (never negotiable)

| Gate | Requirement |
|---|---|
| **Oracle** | Reward **exactly 1.0**, both when I run it locally and on repeat. 0.98 is a defect, not "close enough." |
| **Difficulty** | Across **4** independent GLM-5.2 runs: **1, 2, or 3 of 4** fully passing (reward exactly 1.0) is accepted. **4/4 is rejected as too easy. 0/4 is submittable but costs a frontier-model re-run and ships only ~1/3 of the time.** |

"Fully pass" = reward exactly 1.0 on that run. 8 of 10 checks passing is not a pass.
Always report **all four individual rewards**, never an average. Stop hardening the
moment the battery lands in band — do not keep tuning a fair 1/4 or 2/4 result because it
"feels risky." It isn't.

## My non-negotiables (apply on every task, every session)

1. **I make the decisions.** I can use AI (you) to find issues and draft fixes, but I
   review and choose what ships. Never blindly accept a generated edit — see
   `01-mission-and-success.md`.
2. **Never chase a QC score.** There is no score parameter anymore. The bar is: all
   fourteen review areas come back clean and the client accepts the task. A high Delivery
   Gate score on a task that is secretly unfair or unrealistic is a failure, not a win.
3. **Never fabricate or curate evidence.** No fake golden trajectories, no re-running a
   battery to fish for a prettier number, no dropping a real failing run to hide it. A
   crashed/void run gets re-run and excluded with a reason — it is never silently dropped
   to change the count.
4. **`review.csv` is written by a human, describing THIS package.** Do not let me
   (Claude) draft the `status` or `review_notes` columns as if they were generic
   boilerplate — see `05-review-csv-and-package-standard.md` for exactly what I can help
   with there and what I can't.
5. **Re-run the Oracle after every single change** to gold files, verifiers, or the
   instruction. No exceptions, no "it should still be fine."
6. **Never put an oracle run in `evaluations/solvability/`.** Never ship
   `evaluations/oracle/`. Never add `evaluations/platform/` until told the Delivery Gate
   has been updated to accept it.
7. **Difficulty comes from the data and from recognition, not from more rules, more
   volume, or hidden/ambiguous information.** See `03-hardening-strategy.md` before
   touching a prompt or a fixture.
8. **A trap that doesn't change a graded value doesn't exist.** Simulate every wrong
   reading against the graded output before shipping it as a lever.

## Session start checklist

At the start of any task session, ask me (if not already told):
1. Is this a **non-connector** or **connector** task?
2. Where are we in the lifecycle — fresh mined package, mid-hardening, or fixing a
   client rejection? (`02-workflow-lifecycle.md` has a branch for each.)
3. What's the current state of the two gates (Oracle score, last battery result)?

Then work the relevant section of `02-workflow-lifecycle.md` in order. Don't skip straight
to verifier-tightening or prompt-editing without the cold-read step — it's cheap and it's
where most wasted batteries get prevented.
