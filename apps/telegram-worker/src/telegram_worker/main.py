"""CLI entrypoint for the local Telegram polling worker."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from telegram_worker.client import RuntimeApiClient, TelegramClient
from telegram_worker.polling import run_polling
from telegram_worker.settings import TelegramWorkerSettings


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Telegram worker CLI."""

    parser = argparse.ArgumentParser(
        prog="telegram-worker",
        description="Run local Telegram getUpdates polling against the Runtime API.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level))
    settings = TelegramWorkerSettings()
    if not settings.telegram_bot_token:
        parser.exit(
            status=2,
            message="error: TELEGRAM_BOT_TOKEN must be set in the environment or .env\n",
        )

    telegram_client = TelegramClient(bot_token=settings.telegram_bot_token)
    runtime_client = RuntimeApiClient(base_url=settings.runtime_api_base_url)
    run_polling(
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
