# Troubleshooting KB integration

## Request
Bundle the distilled DAMASK Discussions KB and make retrieval reliable for a weak agent without changing solver or example-library behavior.

## Plan
- Add the six-category sourced card bundle and a bounded standard-library search helper.
- Document deterministic retrieval and scientific safety boundaries.
- Cover ranking, fallback, no-match, limit, installation, and an error-950 eval.

## Outcome
Added 102 complete sourced cards, deterministic category/all-category retrieval, explicit upstream-status labels, docs, tests, an advanced eval case, and an MIT license. Unit tests, skill validation, arbitrary-CWD/installed-copy search, CLI edge cases, source-card parity, syntax, and diff checks pass.
