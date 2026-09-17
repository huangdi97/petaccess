# Publish batches — explicit selection for real publishes

**Status (2026-09-17):** `R2-FINAL-R3-BATCH-01B` is the **first batch ever really
published**, on `petaccess`, 5 AccessRule + 3 RuleException, `REAL_PUBLISH_EXECUTED = YES`.
See `FIRST_REAL_PUBLISH_BATCH_01B_EXECUTION.md`.
`30_50_PLACE_EXPANSION = ALLOWED_NOT_STARTED` — not started.
`SEMANTIC_REMODEL_ISSUE` stays `OPEN`.

## Why a manifest exists

`--max-approve` is an **anti-blind-batch upper bound**. It caps how many rules one
run may create; it cannot say *which* ones. Before this round the only expressible
selection was "all approvals, up to N", so the identity of a publish batch would
have been decided by array order in the signed register — a decision nobody made.

A real publish therefore selects through a versioned manifest:

    docs/governance/publish_batches/<REVISION>_BATCH_<NN>.json

```json
{
  "revision": "R2-FINAL-R3",
  "batch_id": "R2-FINAL-R3-BATCH-01B",
  "reviewer": "huangdi97",
  "deferred": ["dl-pet-ban", "dl-sd-op", "fp-sd-op-firstparty", "lib-sd-op-guide"],
  "candidate_rule_ids": ["fp-legal-dog", "fp-pets-op-firstparty", "fp-sd-legal", "..."]
}
```

The manifest answers exactly one question — *which already-approved candidates
does this batch contain* — and nothing else.

**It deliberately does not store `final_decision`.** Permission still comes from
the signed register (`--registry`). A manifest can narrow a selection; it can
never widen it, so editing one cannot upgrade a HOLD into a publish.

`candidate_rule_ids` holds registry `rule_id` values (`dl-pet-ban`), not candidate
UUIDs: those are the stable human-facing identifiers, and resolving them to
candidates through the signed register keeps one source of truth.

**Position is execution order.** A carve-out must appear *after* the base it
carves out of, and that ordering is checked, not assumed.

## What is refused, and why each refusal is not a filter

Refusals are returned as findings, never repaired silently. A batch that silently
drops half its rows is not the batch anyone reviewed.

| Check | Refusal |
| --- | --- |
| revision mismatch | cross-revision selection |
| reviewer mismatch | the signing reviewer and the manifest's disagree |
| unknown `rule_id` | a typo must not select nothing and look like success |
| duplicate `rule_id` | the same candidate selected twice |
| `final_decision` = HOLD | a held candidate can never be published, in this round or any |
| `final_decision` = REJECTED | same |
| carve-out without its base | dependency closure: the base must be earlier in the batch, or already published |
| carve-out listed before its base | position is execution order |
| cross-layer binding | an OPERATOR_POLICY carve-out may not attach to a LEGAL base |
| base shipped without an approved carve-out | see below |
| **a carve-out in the batch that can never fire** | **ZERO INERT RULES — see below** |
| unknown manifest key | a misspelled key would silently select nothing |

### "No prohibition without its **reachable** approved carve-out"

If a base rule in the batch has a carve-out the human approved **and that carve-out
can actually fire**, it must also be in the batch or already published. Otherwise a
guide-dog handler is briefly told "prohibited" while a signed rule says otherwise.

*Reachable* is the operative word, and it is why this refusal was rewritten.

A carve-out is reachable only when the base **semantically governs the carve-out's
own subject** — measured with `app.rulespec.animal_scope.rule_governs` (ADR-025),
not with a second hand-written scope comparison. Under ADR-025 `ordinary_pet`
covers `{ordinary_dog, ordinary_cat, other_pet}` and deliberately excludes the
service roles, so a `guide_dog` carve-out bound to an `ordinary_pet` base can
never fire: it is **inert**.

| (base, carve-out) state | Effect on the base |
| --- | --- |
| `reachable` | obligation stands — the carve-out must ship in this batch or be already published |
| `unreachable` | recorded as `UNREACHABLE_APPROVED_CARVE_OUT` → `SEMANTIC_REMODEL_REQUIRED`; **does not block the base** |
| `unevaluable` (scope data missing) | obligation still stands — "cannot prove it is inert" is not a licence |

Blocking a base on an inert carve-out would let a modelling defect hold real rules
hostage. See `OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md` for the defect family.

A HOLD is **not** a carve-out anyone signed, so it does not create this
obligation either. That is exactly why `lib-sd-op-police` and
`lib-sd-op-military` — both HOLD — must not gate `lib-pets-op`.

Shipping a base without a *reachable* carve-out deliberately requires an explicit
override plus human authorisation. This round grants no override.

### "ZERO INERT RULES"

Releasing a base from an inert carve-out is one thing; **shipping** an inert
carve-out is another. A rule that can never fire is worse than no rule: it is
published, linked, audited and counted while silently promising access it does not
deliver. So a carve-out whose measured state is `unreachable` or `unevaluable` is
refused outright — it is recorded as `SEMANTIC_REMODEL_REQUIRED` and waits for the
semantic remodel.

`verify_publish_r3.py` carries this as the first-class gate `ZERO_INERT_RULES`
(alongside `CARVE_OUT_REACHABILITY`). Neither accepts `PASS_WITH_LIMITATIONS`.

Consequence for history: `R2-FINAL-R3-BATCH-01` (12, three inert) and
`R2-FINAL-R3-BATCH-01A` (10, two inert) are **now refused by this gate**. Both
files are kept as rehearsal history, and a test asserts they stay refused — the
guard must not quietly stop biting.

## Command forms

Dry run — the real plan against the real gate, no writes:

```bash
python scripts/publish_reviewed_r1.py \
  --dry-run \
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
  --max-approve 8
```

`--max-approve 8` is a **second-layer safety cap** on top of the manifest, not
the selection.

Real publish — three conditions, all required:

```bash
python scripts/publish_reviewed_r1.py \
  --execute \
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
  --max-approve 8 \
  --reviewer huangdi97
```

`--execute` without `--batch-file` is refused outright. A bare `--execute` would
publish every APPROVED row in the register in one shot.

`--reviewer` is the fourth condition in practice: in execute mode a reviewer that
does not match the register's signature is refused, so a real publish names the
human who signed.

## Narrowing a batch after a rehearsal

A rehearsal that fails narrows the batch. It never patches the resolver to make a
test pass, and it never rewrites a human decision.

| Batch | Size | Outcome |
| --- | --- | --- |
| `R2-FINAL-R3-BATCH-01` | 12 | rehearsal failed on `dl-pet-ban` / `dl-sd-op` (semantic defect) → **narrowed**, kept as history |
| `R2-FINAL-R3-BATCH-01A` | 10 | rehearsal green, but accepted `PASS_WITH_LIMITATIONS` on 2 inert carve-outs → **rejected on review**, kept as history |
| `R2-FINAL-R3-BATCH-01B` | 8 | current first real publish candidate — 5 base + 3 carve-out, `ZERO_INERT_RULES = PASS` |

Rows removed by narrowing stay `APPROVED` in the signed register. "Not selected"
is not a decision about the rule — narrowing can only defer a publish, never
reverse one. The four rows deferred out of BATCH-01B are recorded in the
manifest's `deferred` field and carry the follow-up state
`DEFERRED_APPROVED_SEMANTIC_REMODEL`.

The rejection of BATCH-01A is the point worth keeping: its rehearsal was green and
the end-user answers were correct, but two of its five carve-outs can never fire.
**"The answer happens to be right" is not evidence that a rule works** — the right
answer was coming from an independent LEGAL-layer rule. That round accepted a
`PASS_WITH_LIMITATIONS`; this round does not, which is why the gate now grades
inert rules as a failure and why BATCH-01 and BATCH-01A are refused by it.

The defect family — an `ordinary_pet` base does not cover a `guide_dog` subject
(ADR-025), so the carve-out is dead — is documented in
`OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md` (Disney instance:
`DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md`).

## Rehearsal

The first real `--execute` is never rehearsed against a database anyone depends
on. `scripts/rehearsal_db.py` guards a purpose-named clone with two independent
checks — a deny list *and* an allowlist pattern — because the incident that
created this discipline came from an unknown name being *accepted*.

```bash
# API stopped first: the clone needs an exclusive source database
bash scripts/rehearsal_r3_runbook.sh phase0
python scripts/dev_api_server.py --db-name petaccess_publish_rehearsal_r3 --port 8010
bash scripts/rehearsal_r3_runbook.sh phase1
```

`phase1` executes the batch, re-executes it to prove it is a no-op, and then runs
`scripts/verify_publish_r3.py` — linkage, resolver, engine consistency, rollback,
supersession, watch.

Evidence lands in `artifacts/`:

| File | What it proves |
| --- | --- |
| `rehearsal_db_fingerprint.json` | what was cloned, and from where |
| `rehearsal_execute_r3.json` | the plan and the write, per candidate |
| `rehearsal_execute_r3_receipt.json` | the execute receipt |
| `rehearsal_idempotency.json` | re-running the batch changed nothing |
| `publish_rehearsal_r3_verification.json` | the drills, with each expectation and what actually happened |

`phase1` takes `MANIFEST` and `MAX_APPROVE` from the environment, so a narrowed
batch is rehearsed on its own terms:

```bash
MANIFEST=docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
MAX_APPROVE=8 \
ART=artifacts/batch01b \
  bash scripts/rehearsal_r3_runbook.sh phase1
```

`MAX_APPROVE` must be at least the manifest's size — the cap is a second layer
over the manifest, not a way to refuse the batch for an unrelated reason.

The drills mutate the rehearsal database on purpose. `verify_publish_r3.py`
refuses to run on a database that already carries drill damage, because a
rollback drill run twice proves nothing the second time.

## After the first real publish

A whole-register dry-run is **not** constant after the first publish, and any
test that asserts a fixed count from it is asserting "nothing has ever been
published". After `BATCH-01B` the same command reports `NOOP = 8` and two
carve-outs newly `BLOCKED`, because the planner refuses to create a carve-out in
a run that is not also creating its base ("例外不得被间接带入"). Assert the
invariant instead: a carve-out is created only when its base is created in the
same run, and every approved row is counted exactly once as
created / NOOP / BLOCKED.

Publishing a snapshot of the real database before and after is done by
`scripts/real_publish_snapshot.py`, which produces both sides so they can be
diffed. It refuses to overwrite an existing file — a pre-publish snapshot that
can be silently replaced is not evidence of the state before the write.
