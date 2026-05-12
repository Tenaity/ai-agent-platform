"""Tests for Telegram update normalization."""

from telegram_worker.normalizer import normalize_update


def test_telegram_text_update_normalizes_to_runtime_request_payload() -> None:
    update = {
        "update_id": 1001,
        "message": {
            "message_id": 55,
            "text": "tracking container ABCU1234567",
            "chat": {"id": 123456},
            "from": {"username": "demo_user"},
        },
    }

    payload = normalize_update(update, tenant_id="demo")

    assert payload == {
        "tenant_id": "demo",
        "channel": "telegram",
        "user_id": "telegram:123456",
        "thread_id": "telegram:123456",
        "message": "tracking container ABCU1234567",
        "metadata": {
            "telegram_update_id": 1001,
            "telegram_chat_id": 123456,
            "telegram_message_id": 55,
            "telegram_username": "demo_user",
        },
    }


def test_missing_text_update_is_ignored_safely() -> None:
    update = {
        "update_id": 1002,
        "message": {
            "message_id": 56,
            "photo": [{"file_id": "photo-id"}],
            "chat": {"id": 123456},
        },
    }

    assert normalize_update(update, tenant_id="demo") is None


def test_non_message_update_is_ignored_safely() -> None:
    update = {"update_id": 1003, "callback_query": {"id": "callback-id"}}

    assert normalize_update(update, tenant_id="demo") is None
