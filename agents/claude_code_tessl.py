"""
Custom Claude Code agent with Tessl MCP tools enabled.
"""

import os
import shlex

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.agents.installed.base import ExecInput
from harbor.models.trial.paths import EnvironmentPaths


class ClaudeCodeTessl(ClaudeCode):
    """Claude Code agent with Tessl MCP tools allowed."""

    ALLOWED_TOOLS = ClaudeCode.ALLOWED_TOOLS + [
        "mcp__tessl__query_library_docs",
        "mcp__tessl__search",
        "mcp__tessl__install",
        "mcp__tessl__status",
    ]

    @staticmethod
    def name() -> str:
        return "claude-code-tessl"

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
        """Override to add TESSL_TOKEN to environment."""
        escaped_instruction = shlex.quote(instruction)

        env = {
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", ""),
            "FORCE_AUTO_BACKGROUND_TASKS": "1",
            "ENABLE_BACKGROUND_TASKS": "1",
            # Pass TESSL_TOKEN for MCP authentication (required for query_library_docs)
            "TESSL_TOKEN": os.environ.get("TESSL_TOKEN", ""),
        }

        # Remove empty auth credentials
        env = {k: v for k, v in env.items() if v}

        if self.model_name:
            env["ANTHROPIC_MODEL"] = self.model_name.split("/")[-1]
        elif "ANTHROPIC_MODEL" in os.environ:
            env["ANTHROPIC_MODEL"] = os.environ["ANTHROPIC_MODEL"]

        if "MAX_THINKING_TOKENS" in os.environ:
            env["MAX_THINKING_TOKENS"] = os.environ["MAX_THINKING_TOKENS"]

        env["CLAUDE_CONFIG_DIR"] = (EnvironmentPaths.agent_dir / "sessions").as_posix()

        return [
            ExecInput(
                command=(
                    "mkdir -p $CLAUDE_CONFIG_DIR/debug $CLAUDE_CONFIG_DIR/projects/-app "
                    "$CLAUDE_CONFIG_DIR/shell-snapshots $CLAUDE_CONFIG_DIR/statsig "
                    "$CLAUDE_CONFIG_DIR/todos"
                ),
                env=env,
            ),
            ExecInput(
                command=(
                    f"claude --verbose --output-format stream-json "
                    f"-p {escaped_instruction} --allowedTools "
                    f"{' '.join(self.ALLOWED_TOOLS)} 2>&1 </dev/null | tee "
                    f"/logs/agent/claude-code.txt"
                ),
                env=env,
            ),
        ]

