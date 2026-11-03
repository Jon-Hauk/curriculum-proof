# Ladder: where the pipeline goes after Grade 12

The pipeline has so far worked Alberta Grade 12 diploma forms, which have one right answer per machine-scored item and an official key. This file sets out the rungs above that, in order, with the grader each rung needs. Nothing here has run. Each rung starts with a small pre-registered pilot under the same rules as now: director/answerer split, frozen protocol before any answer, one attempt per item, a recorded answer is never replaced, and the grader is not the answerer.

## Where it stands (2026-11-03)

| Rung | Material | Grader | Status |
|---|---|---|---|
| 0 | Alberta Grade 12 diploma forms (Math 30-1, Physics 30, Chemistry 30) | Official key, `grade_machine.py` / `grade_form.py` | 4 forms run (the 2022 form twice); m301-2017 pre-registered, not run |
| 1 | University calculus (MIT OpenCourseWare Scholar exams) | Final-answer equivalence in sympy, `grade_open.py` (to write) | Not prepared |
| 2 | Undergraduate pure mathematics in Lean 4 (ProofNet) | The Lean proof checker, `grade_lean.py` (to write) | Not prepared |
| 3 | Competition mathematics in Lean 4 (PutnamBench) | The Lean proof checker | Not prepared |

Rung 0 finishes with m301-2017, which tests the recording and check rules written after c30-2019 (see `PREREG-m301-2017.md`). The other prepared Alberta forms are the same level or lower (Mathematics 30-2 is the less advanced stream), so they widen rung 0 rather than climb.

There is no Alberta rung above Mathematics 30-1. Mathematics 31, Alberta's calculus course, has no diploma exam, so no Alberta form with an official key exists for it. Rung 1 covers the same ground and continues past it.

## Rung 1: university calculus

**Material.** MIT OpenCourseWare's 18.01SC Single Variable Calculus (Fall 2010) publishes its exams with solutions, including the final. The course's pages carry a Creative Commons licence link to CC BY-NC-SA 4.0. It covers what Mathematics 31 covers (limits, derivatives and their applications) and continues into integration and series. The same OpenCourseWare Scholar format exists for multivariable calculus, differential equations and linear algebra; confirm each course's exam pages and licence when preparing it.

**What changes.** These exams have no multiple-choice or numerical-response key. Items have open answers, and the solutions give worked results. So:

- The director writes, before the run, a key file with the final answer for each machine-scored item, taken from the published solutions, and a list of items that are not machine-scored (sketches, explanations, "show that" items). The unscored list is part of the pre-registration, as written responses are now.
- `grade_open.py` compares answers by meaning, not by string: an expression matches if sympy simplifies the difference to zero and the two agree numerically at a set of random points fixed in the protocol; a number matches within a tolerance fixed in the protocol; sets and intervals match as sets. It is tested before the pre-registration is published: the key must score full marks against itself, and a file of deliberately wrong answers must score zero.
- The answer format gets a recording rule from day one, learned from c30-2019's decimal points: every final answer is written as a sympy-parsable string, and the check compares that string as well as the value.

**What gets better.** The licence allows sharing adapted material with attribution, non-commercially, under the same licence. That means the per-item artifacts (scripts, checks, derivations), which are private for the Alberta forms, could be published for this rung, in their own folder carrying CC BY-NC-SA 4.0. The repository's MIT licence would still cover only the code. "Non-commercial" matters: settle whether a given use is commercial before relying on these artifacts in paid work.

**Pilot.** 18.01SC Exam 1, then the final.

## Rung 2: undergraduate pure mathematics in Lean 4

**Material.** ProofNet: 371 problems taken mainly from standard undergraduate textbooks in real and complex analysis, linear algebra, abstract algebra and topology. Each has a formal statement, a natural-language statement and a natural-language proof. MIT licence. The original repository is Lean 3, which is no longer maintained; it points to a Lean 4 port in the `deepseek-ai/DeepSeek-Prover-V1.5` repository.

**The grader is the proof checker.** No answer key is needed. An item counts as proved only if all of these hold, checked by `grade_lean.py`, which is not the answerer:

- The theorem statement is byte-identical to the frozen one (its hash is in the protocol). The answerer may never edit a statement.
- The file builds with the Lean version and Mathlib commit pinned in the protocol.
- The proof contains no `sorry` or `admit`.
- `#print axioms` for the theorem lists nothing beyond `propext`, `Classical.choice` and `Quot.sound`.

This is the property every earlier rule has been reaching for. A Python check can share the answerer's assumption, as c30-2019 NR 2 showed. A proof checker cannot be talked into agreeing.

**The remaining weak spot is the statement, not the proof.** A formal statement can say something other than the textbook theorem. A valid proof of a misformalized statement proves the wrong thing. Use the benchmark's statements as published, record any known errata in the protocol, and report proved items as "proved as formalized".

**Environment.** The protocol pins the toolchain. The answerer may run `lake build` but may not change the toolchain, the Mathlib version or the statements.

**Pilot.** A fixed sample of 20 items, chosen by a seeded random draw recorded in the pre-registration before any proof exists. Expect a much lower score than rung 0. It is published whatever it is.

## Rung 3: competition mathematics in Lean 4

**Material.** PutnamBench: 640 problems from the Putnam Mathematical Competition, formalized in Lean 4 and Isabelle for all problems and in Coq for a substantial subset (repository `trishullab/PutnamBench`). When it was published in 2024, established theorem provers solved only a handful. Its licence was not confirmed when this file was written; confirm it before publishing any artifacts.

**Grader.** The same as rung 2.

**Pilot.** A seeded random draw of 10 items, pre-registered.

## What the higher rungs cannot show

- Training data. The OpenCourseWare exams, the textbooks behind ProofNet and the Putnam problems are all public and widely copied. A score is not a claim about unseen problems. One way to measure the effect at rung 1: the director writes parameter-shifted variants of some items and keys them in sympy, and both versions are scored. Those keys are the director's, not official, and must be labelled that way.
- One run, one sample per item, no error bars, as at rung 0.
- At rungs 2 and 3, "proved" means proved as formalized.

## Next step after m301-2017

The director prepares 18.01SC Exam 1: download the exam and solutions, record their SHA-256 hashes, cut a questions-only extract, write the key file and the unscored list, write and test `grade_open.py`, then publish the pre-registration before the answerer sees anything.

## Sources

- MIT OpenCourseWare, 18.01SC Single Variable Calculus, Fall 2010, final exam solutions: https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/resources/mit18_01scf10_finalsol/
- ProofNet repository: https://github.com/zhangir-azerbayev/proofnet
- PutnamBench paper: https://arxiv.org/abs/2407.11214
