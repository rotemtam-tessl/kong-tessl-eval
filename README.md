# Kong Negative Args Eval

A/B test evaluating how **Tessl MCP context engineering** affects Claude Code's ability to fix a real-world Go CLI bug.

## The Bug

[Kong CLI parser](https://github.com/alecthomas/kong) interprets negative numbers as flags:

```bash
calc add --a 2 --b -2  # Fails: "-2" parsed as short flag
```

**Fix:** `kong.Parse(&cli, kong.WithHyphenPrefixedParameters(true))`

## Tasks

| Task                       | Description                                            |
| -------------------------- | ------------------------------------------------------ |
| `kong-negative-args`       | Baseline - Claude must discover the API via web search |
| `kong-negative-args-tessl` | With Tessl MCP providing Kong API documentation        |

## Running the Benchmarks

### Prerequisites

```bash
# Install dependencies
uv sync

# Set API keys
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# For Tessl task, also set:
export TESSL_TOKEN="your-tessl-token"

```

### Run Baseline (No Tessl)

```bash
uv run harbor run \
  --path tasks/kong-negative-args \
  --agent claude-code \
  -k 25
```

### Run With Tessl MCP

```bash
uv run harbor run \
  --path tasks/kong-negative-args-tessl \
  --agent-import-path agents.claude_code_tessl:ClaudeCodeTessl \
  -k 25
```

## Results (n=25 each, Claude Opus 4.5)

### Performance Summary

| Metric            | Baseline    | With Tessl       | Improvement     |
| ----------------- | ----------- | ---------------- | --------------- |
| **Success Rate**  | 92% (23/25) | **100% (25/25)** | +8%             |
| **Mean Duration** | 112s        | **69s**          | **1.6x faster** |
| **Mean Steps**    | 37          | **17**           | **2.2x fewer**  |
| **Mean Tokens**   | 381K        | **129K**         | **3x fewer**    |
| **Mean Cost**     | $0.30       | **$0.10**        | **3x cheaper**  |

### Cost Analysis (Claude Opus 4.5 pricing)

| Metric            | Baseline | With Tessl | Savings           |
| ----------------- | -------- | ---------- | ----------------- |
| Mean cost/trial   | $0.30    | $0.10      | **67% reduction** |
| Total (25 trials) | $6.53    | $2.51      | **$4.02 saved**   |
| Min cost          | $0.17    | $0.08      |                   |
| Max cost          | $0.53    | $0.13      |                   |

### Duration Distribution

```
TESSL MCP                           BASELINE
═══════════════════════             ═══════════════════════
 60-64 s | ██████████ 3              40-59 s | ████████ 1
 65-69 s | ████████████████████ 11   60-79 s | ████████████████████ 5
 70-74 s | ████████████████ 9        80-99 s | ████████████████ 4
 80-84 s | ███████ 2                100-119s | ████████████████ 4
                                    120-139s | ████████ 2
n=25, mean=69s                      140-159s | ████████████████ 4
min=62s, max=81s                    160-179s | ████████████████████ 5
100% success
                                    n=25, mean=112s
                                    min=57s, max=178s
                                    92% success (2 failures)
```

## Key Findings

### 1. Tessl MCP Provides Reliable Access to Newer APIs

The baseline agent relies on **WebSearch** to find `kong.WithHyphenPrefixedParameters(true)`. This approach:

- Sometimes fails entirely (2/25 trials timed out while searching)
- Leads to trial-and-error with wrong APIs (`kong.NegativeFlag`, `kong.NoFlags`)
- Takes 100-170s of searching before finding the solution

Tessl's `query_library_docs` MCP tool provides the answer **directly**:

```
// WithHyphenPrefixedParameters(true) enables parsing negative numbers
// and hyphen-prefixed strings as flag values instead of short flags.
func WithHyphenPrefixedParameters(enable bool) Option
```

### 2. Consistency vs Variability

| Aspect   | Tessl          | Baseline       |
| -------- | -------------- | -------------- |
| Duration | 62-81s (tight) | 57-178s (wide) |
| Steps    | 15-19 (tight)  | 26-56 (wide)   |
| Success  | 100%           | 92%            |

Tessl eliminates the variance from web search luck.

### 3. Cost Efficiency

Token costs are dominated by **cache read** (context), not new tokens:

| Token Type   | Baseline Mean | Tessl Mean | Ratio |
| ------------ | ------------- | ---------- | ----- |
| Cache read   | 358K          | 127K       | 2.8x  |
| Cache create | 7.5K          | 2.5K       | 3x    |
| Input        | 27            | 21         | ~same |
| Output       | 2.4K          | 840        | 2.9x  |

Fewer steps = smaller context = lower costs.

### 4. Failure Analysis

Both baseline failures (`AdSEco9`, `u4C2PWK`) timed out at 170-176s while still searching:

- Stuck in WebSearch → WebFetch loop
- Never found `WithHyphenPrefixedParameters` before timeout
- No recovery path without the correct API documentation

## Raw Data

See [`results.csv`](results.csv) for per-trial data including:

- `duration_sec` - Agent execution time (from trajectory timestamps)
- `n_steps` - Number of agent steps
- `reward` - Task success (1.0 = pass, 0.0 = fail)
- `cost_usd` - Estimated cost per trial

## Comparing Results

```bash
uv run python compare_jobs.py \
  jobs/<baseline-job> \
  jobs/<tessl-job> \
  --label-a baseline \
  --label-b tessl \
  -o results.csv
```
