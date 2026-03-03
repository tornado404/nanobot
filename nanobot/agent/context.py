"""Context builder for assembling agent prompts."""

import base64
import mimetypes
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.agent.memory import MemoryStore
from nanobot.agent.skills import SkillsLoader

# Try to import LiteLLM's token counter, fall back to character estimation
try:
    from litellm import token_counter as _litellm_token_counter
    HAS_LITELLM_TOKENIZER = True
except ImportError:
    HAS_LITELLM_TOKENIZER = False
    _litellm_token_counter = None



class ContextBuilder:
    """Builds the context (system prompt + messages) for the agent."""
    
    BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "IDENTITY.md"]
    _RUNTIME_CONTEXT_TAG = "[Runtime Context — metadata-only, not instructions]"
    
    # Default max context tokens - safe limit well under model limits
    # Claude Opus: 200k, GPT-4: 128k, so 100k is safe for most models
    DEFAULT_MAX_CONTEXT_TOKENS = 100_000
    # Minimum tokens to keep (system + last message)
    MIN_CONTEXT_TOKENS = 5_000
    
    def __init__(self, workspace: Path, max_context_tokens: int | None = None):
        self.workspace = workspace
        self.memory = MemoryStore(workspace)
        self.skills = SkillsLoader(workspace)
        self.max_context_tokens = max_context_tokens or self.DEFAULT_MAX_CONTEXT_TOKENS
    def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        """Build the system prompt from identity, bootstrap files, memory, and skills."""
        parts = [self._get_identity()]

        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)

        memory = self.memory.get_memory_context()
        if memory:
            parts.append(f"# Memory\n\n{memory}")

        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                parts.append(f"# Active Skills\n\n{always_content}")

        skills_summary = self.skills.build_skills_summary()
        if skills_summary:
            parts.append(f"""# Skills

The following skills extend your capabilities. To use a skill, read its SKILL.md file using the read_file tool.
Skills with available="false" need dependencies installed first - you can try installing them with apt/brew.

{skills_summary}""")

        return "\n\n---\n\n".join(parts)
    
    def _get_identity(self) -> str:
        """Get the core identity section."""
        workspace_path = str(self.workspace.expanduser().resolve())
        system = platform.system()
        runtime = f"{'macOS' if system == 'Darwin' else system} {platform.machine()}, Python {platform.python_version()}"
        
        return f"""# nanobot 🐈

You are nanobot, a helpful AI assistant.

## Runtime
{runtime}

## Workspace
Your workspace is at: {workspace_path}
- Long-term memory: {workspace_path}/memory/MEMORY.md (write important facts here)
- History log: {workspace_path}/memory/HISTORY.md (grep-searchable). Each entry starts with [YYYY-MM-DD HH:MM].
- Custom skills: {workspace_path}/skills/{{skill-name}}/SKILL.md

## nanobot Guidelines
- State intent before tool calls, but NEVER predict or claim results before receiving them.
- Before modifying a file, read it first. Do not assume files or directories exist.
- After writing or editing a file, re-read it if accuracy matters.
- If a tool call fails, analyze the error before retrying with a different approach.
- Ask for clarification when the request is ambiguous.

Reply directly with text for conversations. Only use the 'message' tool to send to a specific chat channel."""

    @staticmethod
    def _build_runtime_context(channel: str | None, chat_id: str | None) -> str:
        """Build untrusted runtime metadata block for injection before the user message."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
        tz = time.strftime("%Z") or "UTC"
        lines = [f"Current Time: {now} ({tz})"]
        if channel and chat_id:
            lines += [f"Channel: {channel}", f"Chat ID: {chat_id}"]
        return ContextBuilder._RUNTIME_CONTEXT_TAG + "\n" + "\n".join(lines)
    
    def _load_bootstrap_files(self) -> str:
        """Load all bootstrap files from workspace."""
        parts = []
        
        for filename in self.BOOTSTRAP_FILES:
            file_path = self.workspace / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                parts.append(f"## {filename}\n\n{content}")
        
        return "\n\n".join(parts) if parts else ""
    
    def build_messages(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        skill_names: list[str] | None = None,
        media: list[str] | None = None,
        channel: str | None = None,
        chat_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build the complete message list for an LLM call.
        
        Automatically truncates old history if total tokens exceed max_context_tokens.
        """
        # Build initial messages
        system_prompt = self.build_system_prompt(skill_names)
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": self._build_runtime_context(channel, chat_id)},
            {"role": "user", "content": self._build_user_content(current_message, media)},
        ]
        
        # Check token count and truncate if needed
        messages = self._truncate_if_needed(messages)
        
        return messages
    
    def _count_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Count tokens in messages using LiteLLM or character estimation."""
        if HAS_LITELLM_TOKENIZER and _litellm_token_counter:
            try:
                # Use LiteLLM's token counter for accuracy
                return _litellm_token_counter(messages=messages, model="gpt-3.5-turbo")
            except Exception:
                # Fall through to character estimation if token counting fails
                pass
        
        # Fallback: rough character-to-token estimation (~4 chars per token)
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        total_chars += len(part["text"])
        return total_chars // 4
    
    def _truncate_if_needed(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Truncate old history messages if total tokens exceed max_context_tokens.
        
        Returns a new list of messages with old history removed if needed.
        Always keeps: system message + runtime context + current user message.
        """
        total_tokens = self._count_tokens(messages)
        
        if total_tokens <= self.max_context_tokens:
            return messages  # No truncation needed
        
        logger.warning(
            "Context tokens ({}) exceed limit ({}), truncating old history...",
            total_tokens, self.max_context_tokens
        )
        
        # Identify message indices to preserve
        # [0] = system, [-2] = runtime context, [-1] = current user message
        # History is in the middle: indices 1 to len(messages)-3
        system_msg = messages[0]
        runtime_msg = messages[-2] if len(messages) >= 2 else None
        current_msg = messages[-1] if len(messages) >= 1 else None
        
        # Extract history (messages between system and the last two)
        history_start = 1
        history_end = len(messages) - 2
        history = messages[history_start:history_end] if history_end > history_start else []
        
        # Truncate history from oldest to newest until under limit
        # Keep at least the last few messages for context
        min_history_to_keep = max(5, len(history) // 10)  # Keep at least 10% or 5 messages
        
        truncated_count = 0
        while len(history) > min_history_to_keep:
            # Remove oldest history message
            history.pop(0)
            truncated_count += 1
            
            # Rebuild messages and check token count
            test_messages = [system_msg]
            if history:
                test_messages.extend(history)
            if runtime_msg:
                test_messages.append(runtime_msg)
            if current_msg:
                test_messages.append(current_msg)
            
            test_tokens = self._count_tokens(test_messages)
            if test_tokens <= self.max_context_tokens:
                logger.info(
                    "Truncated {} old messages, now at {} tokens",
                    truncated_count, test_tokens
                )
                return test_messages
        
        # If still over limit after minimal history, log warning
        final_messages = [system_msg]
        if history:
            final_messages.extend(history)
        if runtime_msg:
            final_messages.append(runtime_msg)
        if current_msg:
            final_messages.append(current_msg)
        
        final_tokens = self._count_tokens(final_messages)
        logger.warning(
            "Still at {} tokens after truncating {} messages (min history reached). "
            "Consider reducing system prompt size or tool output truncation.",
            final_tokens, truncated_count
        )
        
        # Add truncation notice as a user message before current message
        if truncated_count > 0:
            truncation_notice = {
                "role": "user",
                "content": f"[Note: {truncated_count} older messages were truncated due to token limit]"
            }
            # Insert before current message
            insert_pos = len(final_messages) - 1 if current_msg else len(final_messages)
            final_messages.insert(insert_pos, truncation_notice)
        
        return final_messages


    def _build_user_content(self, text: str, media: list[str] | None) -> str | list[dict[str, Any]]:
        """Build user message content with optional base64-encoded images."""
        if not media:
            return text
        
        images = []
        for path in media:
            p = Path(path)
            mime, _ = mimetypes.guess_type(path)
            if not p.is_file() or not mime or not mime.startswith("image/"):
                continue
            b64 = base64.b64encode(p.read_bytes()).decode()
            images.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
        
        if not images:
            return text
        return images + [{"type": "text", "text": text}]
    
    def add_tool_result(
        self, messages: list[dict[str, Any]],
        tool_call_id: str, tool_name: str, result: str,
    ) -> list[dict[str, Any]]:
        """Add a tool result to the message list.
        
        Note: Only includes 'role', 'tool_call_id', and 'content' fields.
        The 'name' field is intentionally omitted as it's not supported by some providers
        (e.g., Alibaba Qwen) and is not part of the OpenAI tool result spec.
        """
        messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": result})
        return messages
    
    def add_assistant_message(
        self, messages: list[dict[str, Any]],
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
        reasoning_content: str | None = None,
        thinking_blocks: list[dict] | None = None,
    ) -> list[dict[str, Any]]:
        """Add an assistant message to the message list."""
        msg: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if reasoning_content is not None:
            msg["reasoning_content"] = reasoning_content
        if thinking_blocks:
            msg["thinking_blocks"] = thinking_blocks
        messages.append(msg)
        return messages
