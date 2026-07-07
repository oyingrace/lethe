# Memory Lifecycle

_Stub — the full state machine, half-life table, and reconciler decision
contract land in BUILD_PLAN.md Phase 1. This records the shape now so later
docs (and the golden test set) build on committed ground._

## Status states

```
active ──(half-life decay, unreinforced)──▶ decaying ──▶ deprecated
  ▲                                             │
  └──────────────(reinforced)───────────────────┘
```

- **active** — eligible for recall.
- **decaying** — confidence has dropped below its category threshold;
  excluded from recall but inspectable via `history()`.
- **deprecated** — retired, with the reason kept (contradiction, TTL expiry,
  explicit delete). Never silently dropped — the audit row records why.

## Category half-lives (defaults, configurable via `LifecycleConfig`)

| category    | half-life |
|-------------|-----------|
| state       | 7 days    |
| preference  | 90 days   |
| identity    | ∞ (no decay by default) |
| episodic    | TBD in Phase 1 |
| constraint  | TBD in Phase 1 |

## Reconciler decisions

Every candidate fact extracted from new input is compared against existing
active memories and resolved to exactly one of:

- **ADD** — genuinely new fact, no conflict.
- **REINFORCE** — restates an existing active fact; confidence increases,
  decay clock resets.
- **REVISE** — updates an existing fact (e.g. a changed value); old fact is
  deprecated with a cited reason, new fact added.
- **DEPRECATE** — existing fact is contradicted or invalidated outright.

Contradictions never coexist as active memories — the reconciler must resolve
them or flag for clarification. Every reconciler bug found in Phase 1+ becomes
a new case in the golden test set.

## TTL and hard delete

Facts can carry an explicit `ttl_at`; expiry deprecates them automatically.
Hard delete performs true deletion for privacy — the audit record captures
that a deletion happened (actor, timestamp, reason) but never the deleted
content itself.
