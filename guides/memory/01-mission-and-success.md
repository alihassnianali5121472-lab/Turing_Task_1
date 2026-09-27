# Mission, and how success is actually measured

*Source: Mission.docx*

## The client's goal

The client wants tasks that are **working** (they run without bugs) and **accurate** (the
prompt is natural, the verifier is fair), at their **target difficulty**, to train their
model on data mined from real-world work. My role is to take a mined draft and make it
correct, accurate, functioning, and fair — not to hit an arbitrary internal number.

## The teacher analogy (the whole job in one paragraph)

The task is a **test**. The AI (GLM-5.2) is the **student**. The verifier is the
**rubric**. My job is the same as a teacher turning a rough first draft of an exam into a
good one: a test that actually, honestly measures whether the student knows the material —
not one that's trivially copyable, not one with a trick question nobody could answer from
the material given, and not one graded unfairly.

A good task is:
- **Functional** — no software bugs, nothing broken, so it can actually be attempted.
- **Appropriately difficult** — 1, 2, or 3 of 4 GLM-5.2 runs pass. Never 4 of 4.
- **Honest** — it tests something an AI would reasonably be asked to do in real work
  (prompt realism), not a contrived puzzle.
- **Fairly graded** — the rubric grades the outcome objectively, not arbitrarily.
- **Correctly formatted** per the client's delivery spec (four GLM runs, one reward-1.0
  non-oracle run, `review.csv` + `qc_report.html` in the bundle, standard file layout).

## How success is measured — read this before optimizing anything

**There is no score anymore.** The client removed the numeric score parameter on
25 Aug 2026. Chasing "95" or "85" is over. The bar is binary and qualitative: **all
fourteen review areas come back clean, and the client accepts the task.**

The QC platform still shows a score and still requires a local "Delivery Gate PASS"
before it lets me submit — but that gate is a **local helper, not the client's bar**. It's
a reasonable approximation, refined over several rounds of client feedback, and it exists
to help me get the task right — not something to satisfy on its own terms.

There is no shortcut around going through the task itself, end to end, like a teacher
checking their own exam: is the engineering sound, is the logic correct, does it work, is
it well designed. That review — not a report number — is what maximizes acceptance odds.

## The actual work is debugging, on four fronts

For every task, ask, in order:

1. **Is it functional at all?**
   Is the underlying data or connector tooling working or buggy? Is the logic correct or
   broken? Does it have one gradeable right answer, or is it ambiguous?
   → If buggy/broken/ambiguous and fixable: fix it. If not: drop it and move on. Expect
   this to be real engineering work, not a quick pass.

2. **Is it well designed?**
   Is it a realistic task an AI would actually be asked to do, or contrived? Is the prompt
   overly prescriptive (spells out too much) or does it leak the answer?
   → Fix if fixable, otherwise drop.

3. **Are the verifiers accurate?**
   Does the rubric actually and fairly grade the task, or is it arbitrary, mismatched, or
   unfair? Does it grade everything the prompt actually asks for, correctly — and nothing
   the model was never asked to do?
   → See `04-verifier-design-and-fairness.md` for the mechanics of this.

4. **Is the formatting/artifact set complete?**
   Four GLM runs, one reward-1.0 non-oracle run, `review.csv` and `qc_report.html` inside
   the bundle, standard file structure. See `05-review-csv-and-package-standard.md`.

## Do not game the system

The QC script is a helper, not the target. A task that's tuned to score well on the local
QC tool while actually having an unrealistic prompt, a broken verifier, or unsound logic
**will** be caught by the client — and it will not be accepted, no matter what the
Delivery Gate said. This is **reward hacking against my own QC tooling**, and it is treated
seriously.

Concretely, don't:
- Make verifiers arbitrarily easy (to pass the Oracle trivially) or arbitrarily hard (to
  fake a difficulty score) instead of designing real, fair difficulty.
- Over-specify the prompt so heavily that "difficulty" disappears and the task is no
  longer realistic, just to force a pass rate into band.
- Treat a high Delivery Gate percentage as proof the task is good.

## Using AI (me) responsibly on this work

I am allowed and expected to help you understand a task, find defects, and draft fixes.
What I should **not** do is make the actual judgment calls for you or let you rubber-stamp
my output. In practice:

- When I flag a possible issue, tell me *why* it's an issue in your own words before we
  fix it — if you can't, we probably don't understand the task well enough yet to touch it.
- Ask me directly: "Is this task sound? Are there correctness, structural, or logic issues
  that would block shipping this to the client?" — and treat my answer as an input to your
  decision, not the decision itself.
- Never let me draft `review.csv`'s `status` and `review_notes` as if they were generic —
  they are supposed to be a record that a *human* looked at *this* package. (Full detail
  in `05-review-csv-and-package-standard.md`.)
