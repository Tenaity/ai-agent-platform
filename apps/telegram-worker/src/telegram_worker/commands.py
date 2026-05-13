"""Deterministic Telegram command parsing for the local showcase worker."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar


class TelegramCommand(StrEnum):
    """Command names supported by the Telegram showcase console."""

    FREE_TEXT = "free_text"
    HELP = "help"
    SHOWCASE = "showcase"
    RAG = "rag"
    TOOL = "tool"
    BOOKING = "booking"
    TICKET = "ticket"
    HUMAN = "human"
    MEMO = "memo"
    SKILL = "skill"
    MCP = "mcp"
    A2A = "a2a"
    ACP = "acp"
    DEEPAGENT = "deepagent"
    TRACE = "trace"
    EVAL = "eval"


@dataclass(frozen=True)
class ParsedTelegramCommand:
    """Parsed Telegram text with command identity and remaining arguments."""

    command: TelegramCommand
    args: str
    raw_text: str


class TelegramCommandRouter:
    """Parse Telegram text into deterministic showcase commands."""

    _COMMANDS: ClassVar[dict[str, TelegramCommand]] = {
        command.value: command
        for command in TelegramCommand
        if command != command.FREE_TEXT
    }

    def parse(self, text: str) -> ParsedTelegramCommand:
        """Parse Telegram text without calling Telegram or Runtime APIs."""

        stripped = text.strip()
        if not stripped.startswith("/"):
            return ParsedTelegramCommand(
                command=TelegramCommand.FREE_TEXT,
                args=stripped,
                raw_text=text,
            )

        command_token, _, args = stripped.partition(" ")
        command_name = command_token.removeprefix("/").split("@", maxsplit=1)[0].casefold()
        command = self._COMMANDS.get(command_name)
        if command is None:
            return ParsedTelegramCommand(
                command=TelegramCommand.FREE_TEXT,
                args=stripped,
                raw_text=text,
            )

        return ParsedTelegramCommand(command=command, args=args.strip(), raw_text=text)
