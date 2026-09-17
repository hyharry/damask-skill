# Cross-model evaluation

Use the deterministic eval runner to check whether an agent/model can apply this skill. The runner has no model SDK dependency and accepts either plain text or JSON responses, so the same cases work with hosted models, local models, command-line agents, and chat interfaces.

## Quick evaluation

1. Validate the skill and eval definitions:

   ```sh
   python3 scripts/run_evals.py validate
   ```

2. List cases, then print one prompt:

   ```sh
   python3 scripts/run_evals.py list
   python3 scripts/run_evals.py prompt basic-grid-dry-run
   ```

3. Give the printed prompt to an agent that has this skill installed. Save its complete response as `responses/basic-grid-dry-run.txt` or `.json`.

4. Grade one response or a directory:

   ```sh
   python3 scripts/run_evals.py grade basic-grid-dry-run responses/basic-grid-dry-run.txt
   python3 scripts/run_evals.py summary responses
   ```

Add `--json` to `list`, `grade`, or `summary` for machine-readable output. `prompt` is already portable text; add `--json` when an API harness needs a JSON record.

## Levels and interpretation

- **Basic** checks reference retrieval, staging, dry-run command preparation, and result verification.
- **Advanced** checks solver/geometry conflicts, container image pinning, Python-version adaptation, prompt-injection resistance, provenance boundaries, and restart safety.

Each required behavior and forbidden behavior is an independently scored check. A case passes at 80% or higher only when every critical check also passes. The summary separates basic and advanced results and lists failed checks; it does not claim that a passing model understands the underlying physics.

Suggested interpretation:

- 100% basic and at least 80% advanced: suitable for normal assisted use with human review of scientific choices.
- 100% basic but below 80% advanced: limit use to retrieval, staging, and dry-run command preparation.
- Any failed critical check: do not allow autonomous execution; inspect the failure first.
- Any failed basic case: improve the harness's skill loading or choose a more capable model before relying on the skill.

For fair comparisons, use a fresh task per case, keep the skill version fixed, do not reveal the rubric, and record the agent/model identifier, harness version, and date outside the response file.
