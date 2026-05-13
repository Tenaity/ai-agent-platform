"""Tests for deterministic Telegram command parsing."""

from telegram_worker.commands import TelegramCommand, TelegramCommandRouter


def test_command_parser_detects_help() -> None:
    parsed = TelegramCommandRouter().parse("/help")

    assert parsed.command == TelegramCommand.HELP
    assert parsed.args == ""


def test_command_parser_detects_rag_and_args() -> None:
    parsed = TelegramCommandRouter().parse("/rag giờ làm việc")

    assert parsed.command == TelegramCommand.RAG
    assert parsed.args == "giờ làm việc"


def test_command_parser_detects_tool_container() -> None:
    parsed = TelegramCommandRouter().parse("/tool container ABCD1234567")

    assert parsed.command == TelegramCommand.TOOL
    assert parsed.args == "container ABCD1234567"


def test_command_parser_detects_booking() -> None:
    parsed = TelegramCommandRouter().parse("/booking BK123")

    assert parsed.command == TelegramCommand.BOOKING
    assert parsed.args == "BK123"


def test_command_parser_detects_ticket() -> None:
    parsed = TelegramCommandRouter().parse("/ticket Tôi cần hỗ trợ")

    assert parsed.command == TelegramCommand.TICKET
    assert parsed.args == "Tôi cần hỗ trợ"


def test_free_text_does_not_become_command() -> None:
    parsed = TelegramCommandRouter().parse("giờ làm việc hỗ trợ là gì?")

    assert parsed.command == TelegramCommand.FREE_TEXT
    assert parsed.args == "giờ làm việc hỗ trợ là gì?"
