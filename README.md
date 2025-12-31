# Kong Negative Args Eval

A/B test evaluating how **Tessl context engineering** affects Claude Code's ability to fix a real-world Go CLI bug.

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
| `kong-negative-args-tessl` | With Tessl tile providing Kong API documentation       |

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
  -k 20 -n 4
```

### Run With Tessl

```bash
uv run harbor run \
  --path tasks/kong-negative-args-tessl \
  --agent-import-path agents.claude_code_tessl:ClaudeCodeTessl \
  -k 20 -n 4
```

## Results (n=20 each)

### Performance

| Metric      | Baseline | With Tessl | Δ        |
| ----------- | -------- | ---------- | -------- |
| Pass Rate   | 95%      | 90%        | -5%      |
| Median Time | 118s     | 62s        | **-47%** |
| Mean Time   | 132s     | 102s       | -23%     |
| Timeouts    | 1        | 2          | +1       |

### Token Consumption

| Metric            | Baseline | With Tessl | Δ        |
| ----------------- | -------- | ---------- | -------- |
| Mean Input/Trial  | 489K     | 376K       | **-23%** |
| Mean Output/Trial | 2,940    | 2,001      | **-32%** |
| Est. Cost/Trial   | $0.227   | $0.171     | **-29%** |

### Time Distribution

```
                Baseline    Tessl
    0-60s:          0          7   ← Fast path enabled
  60-120s:         11          8
 120-180s:          4          1
 180-240s:          3          2
 240-300s:          1          0
 timeout:           1          2
```

## Key Findings

1. **Tessl enables a "fast path"** - 35% of Tessl runs complete in under 60s vs 0% baseline
2. **Lower token usage** - 23% fewer input tokens, 32% fewer output tokens
3. **Cost savings** - ~$0.06 saved per task (~29% reduction)
4. **Failure mode persists** - Both variants suffer from "doubt spiral" where Claude questions correct solution

## Raw Data

See [`results.csv`](results.csv) for per-trial data including duration, reward, and token counts.
