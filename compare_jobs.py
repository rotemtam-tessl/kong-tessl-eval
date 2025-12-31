#!/usr/bin/env python3
"""
Compare two Harbor job runs and output results to CSV.

Usage:
    python compare_jobs.py <job_a_path> <job_b_path> [--output results.csv]
    
Example:
    python compare_jobs.py jobs/2026-01-05__12-35-11 jobs/2026-01-05__12-55-23
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

# Claude Opus 4.5 pricing (USD per 1M tokens)
PRICE_INPUT = 5.00
PRICE_OUTPUT = 25.00
PRICE_CACHE_READ = 0.50  # 10% of input price
PRICE_CACHE_CREATE = 6.25  # 1.25x input price


def calculate_cost(input_tokens: int, output_tokens: int, 
                   cache_read: int, cache_create: int) -> float:
    """Calculate estimated cost in USD based on Claude 3.5 Sonnet pricing."""
    cost = (
        (input_tokens / 1_000_000) * PRICE_INPUT +
        (output_tokens / 1_000_000) * PRICE_OUTPUT +
        (cache_read / 1_000_000) * PRICE_CACHE_READ +
        (cache_create / 1_000_000) * PRICE_CACHE_CREATE
    )
    return round(cost, 4)


def get_agent_time_from_trajectory(trajectory_file: Path) -> int:
    """Extract actual agent execution time from trajectory timestamps."""
    if not trajectory_file.exists():
        return 0
    
    try:
        with open(trajectory_file) as f:
            data = json.load(f)
        
        steps = data.get("steps", [])
        if not steps:
            return 0
        
        # Find first non-warmup step (is_sidechain=False)
        first_ts = None
        last_ts = None
        
        for step in steps:
            extra = step.get("extra", {})
            if extra.get("is_sidechain", False):
                continue  # Skip warmup/sidechain steps
            
            ts_str = step.get("timestamp", "")
            if not ts_str:
                continue
            
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            
            if first_ts is None:
                first_ts = ts
            last_ts = ts
        
        if first_ts and last_ts:
            return int((last_ts - first_ts).total_seconds())
        return 0
    except (json.JSONDecodeError, KeyError, ValueError):
        return 0


def extract_trials(job_dir: Path, variant: str) -> list[dict]:
    """Extract trial data from a job directory."""
    rows = []
    
    for trial_dir in sorted(job_dir.iterdir()):
        if not trial_dir.is_dir():
            continue
            
        result_file = trial_dir / "result.json"
        log_file = trial_dir / "agent" / "claude-code.txt"
        trajectory_file = trial_dir / "agent" / "trajectory.json"
        
        if not result_file.exists():
            continue
        
        with open(result_file) as f:
            data = json.load(f)
        
        # Get agent time from trajectory (actual agent execution time)
        duration = get_agent_time_from_trajectory(trajectory_file)
        
        # Fallback to wall-clock time if trajectory not available
        if duration == 0:
            agent_exec = data.get("agent_execution", {})
            start = agent_exec.get("started_at", "")
            end = agent_exec.get("finished_at", "")
            if start and end:
                s = datetime.fromisoformat(start)
                e = datetime.fromisoformat(end)
                duration = int((e - s).total_seconds())
        
        # Get reward
        reward = data.get("verifier_result", {}).get("rewards", {}).get("reward", None)
        
        # Get token usage from claude-code.txt
        input_tokens = 0
        output_tokens = 0
        cache_read = 0
        cache_create = 0
        
        if log_file.exists():
            with open(log_file) as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        if d.get("type") == "result":
                            u = d.get("usage", {})
                            input_tokens = u.get("input_tokens", 0)
                            cache_create = u.get("cache_creation_input_tokens", 0)
                            cache_read = u.get("cache_read_input_tokens", 0)
                            output_tokens = u.get("output_tokens", 0)
                    except json.JSONDecodeError:
                        pass
        
        # Extract trial ID from directory name (after __)
        trial_id = trial_dir.name.split("__")[-1] if "__" in trial_dir.name else trial_dir.name
        
        # Get step count from trajectory
        n_steps = 0
        if trajectory_file.exists():
            try:
                with open(trajectory_file) as f:
                    traj = json.load(f)
                n_steps = traj.get("final_metrics", {}).get("total_steps", 0)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Calculate cost
        cost_usd = calculate_cost(input_tokens, output_tokens, cache_read, cache_create)
        
        rows.append({
            "variant": variant,
            "trial_id": trial_id,
            "duration_sec": duration,
            "n_steps": n_steps,
            "reward": reward,
            "input_tokens": input_tokens,
            "cache_create_tokens": cache_create,
            "cache_read_tokens": cache_read,
            "output_tokens": output_tokens,
            "total_input_tokens": input_tokens + cache_create + cache_read,
            "cost_usd": cost_usd,
        })
    
    return rows


def main():
    parser = argparse.ArgumentParser(description="Compare two Harbor job runs")
    parser.add_argument("job_a", type=Path, help="Path to first job (variant 'a')")
    parser.add_argument("job_b", type=Path, help="Path to second job (variant 'b')")
    parser.add_argument("--output", "-o", type=Path, default=Path("results.csv"),
                        help="Output CSV file (default: results.csv)")
    parser.add_argument("--label-a", default="baseline", help="Label for job A (default: baseline)")
    parser.add_argument("--label-b", default="tessl", help="Label for job B (default: tessl)")
    
    args = parser.parse_args()
    
    if not args.job_a.exists():
        print(f"Error: Job A path does not exist: {args.job_a}")
        return 1
    if not args.job_b.exists():
        print(f"Error: Job B path does not exist: {args.job_b}")
        return 1
    
    print(f"Extracting trials from {args.job_a} ({args.label_a})...")
    rows_a = extract_trials(args.job_a, args.label_a)
    print(f"  Found {len(rows_a)} trials")
    
    print(f"Extracting trials from {args.job_b} ({args.label_b})...")
    rows_b = extract_trials(args.job_b, args.label_b)
    print(f"  Found {len(rows_b)} trials")
    
    all_rows = rows_a + rows_b
    
    # Write CSV
    fieldnames = [
        "variant", "trial_id", "duration_sec", "n_steps", "reward",
        "input_tokens", "cache_create_tokens", "cache_read_tokens",
        "output_tokens", "total_input_tokens", "cost_usd"
    ]
    
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\nWrote {len(all_rows)} rows to {args.output}")
    
    # Print summary stats
    for label, rows in [(args.label_a, rows_a), (args.label_b, rows_b)]:
        successful = [r for r in rows if r["reward"] == 1.0]
        durations = [r["duration_sec"] for r in successful if r["duration_sec"] > 0]
        steps = [r["n_steps"] for r in successful if r["n_steps"] > 0]
        tokens = [r["total_input_tokens"] for r in successful if r["total_input_tokens"] > 0]
        costs = [r["cost_usd"] for r in successful if r["cost_usd"] > 0]
        
        print(f"\n{label.upper()}:")
        print(f"  Success rate: {len(successful)}/{len(rows)} ({100*len(successful)/len(rows):.0f}%)")
        if durations:
            print(f"  Duration: mean={sum(durations)/len(durations):.0f}s, "
                  f"min={min(durations)}s, max={max(durations)}s")
        if steps:
            print(f"  Steps: mean={sum(steps)/len(steps):.0f}, "
                  f"min={min(steps)}, max={max(steps)}")
        if tokens:
            print(f"  Tokens: mean={sum(tokens)/len(tokens):.0f}, "
                  f"min={min(tokens)}, max={max(tokens)}")
        if costs:
            print(f"  Cost: mean=${sum(costs)/len(costs):.2f}, "
                  f"total=${sum(costs):.2f}, min=${min(costs):.2f}, max=${max(costs):.2f}")
    
    return 0


if __name__ == "__main__":
    exit(main())
