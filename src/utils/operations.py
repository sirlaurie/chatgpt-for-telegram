#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from typing import Dict, Iterable, List, Optional, Tuple, Union
import time
from ._db import DBClient
from ..constants.messages import NOT_ALLOWD, NOT_PERMITED


client = DBClient()


def is_allowed(user_id: int, nickname: str = "Unknown") -> Tuple[bool, bool, bool, str]:
    """
    Check if user is allowed to use the bot.

    For public bot mode:
    - New users are automatically created with allow=1
    - Admins are always allowed (cannot be banned)
    - Only check if user is banned (allow=0)

    Returns:
        (is_allowed, is_premium, is_waiting, error_message)
    """
    import os

    # Check if user is admin - admins are always allowed
    admin_id = int(os.getenv("DEVELOPER_CHAT_ID", 0))
    is_admin = (user_id == admin_id) if admin_id else False

    if is_admin:
        return (True, True, False, "")

    user = client.select_record(table="User", telegram_id=user_id)

    if not isinstance(user, Tuple):
        # New user - auto-create with allow=1 (public bot mode)
        add_user(user_id, nickname, allow=1, premium=0, waiting=0)
        return (True, False, False, "")

    # Parse user data - need to handle new subscription fields
    # Old format: role, nickname, telegramId, allow, premium, waiting
    # New format: role, nickname, telegramId, allow, premium, waiting,
    #             free_messages_used, subscription_status, subscription_type,
    #             subscription_start_date, subscription_end_date, stripe_customer_id, last_message_date

    if len(user) >= 6:
        role = user[0]
        allow = user[3]
        premium = user[4]
        waiting = user[5]
    else:
        # Fallback for incomplete data
        role, allow, premium, waiting = "User", 0, 0, 0

    # Check if user has admin role
    if role == "admin":
        return (True, True, False, "")

    # Only check if user is banned (allow=0)
    if not allow:
        return (False, bool(premium), bool(waiting), NOT_ALLOWD)

    return (True, bool(premium), bool(waiting), "")


def add_user(
    user_id: int, nickname: str, allow: int, premium: int, waiting: int
) -> None:
    """
    Add a new user to the database.

    For public bot mode, new users are created with:
    - allow=1 (automatically allowed)
    - free_messages_used=0 (start with 0 free messages used)
    - subscription_status='free' (start as free tier)
    """
    import time
    client.insert_record(
        table="User",
        data={
            "role": "User",
            "nickname": nickname,
            "telegramId": user_id,
            "allow": allow,
            "premium": premium,
            "waiting": waiting,
            "free_messages_used": 0,
            "subscription_status": "free",
            "subscription_type": None,
            "subscription_start_date": None,
            "subscription_end_date": None,
            "stripe_customer_id": None,
            "last_message_date": int(time.time()),
        },
    )


def add_prompt(user_id: int, prompt: dict[str, Union[str, int]]) -> None:
    client.insert_record(
        table="Prompt",
        data={
            "telegramId": user_id,
            "createAt": int(time.time()),
            **prompt,
        },
    )


def update_user(telegram_id: int, allow: int, premium: int, waiting: int) -> None:
    client.update_record(
        table="User",
        telegram_id=telegram_id,
        data={
            "allow": allow,
            "premium": premium,
            "waiting": waiting,
        },
    )


def query(table: str, maps: Dict[str, int]) -> List[Tuple]:
    if not isinstance(maps, Iterable):
        return []
    column, value = next(iter(maps.items()))
    data = client.query(table=table, column=column, value=value)
    return data


def query_user(telegram_id: int) -> Optional[Tuple]:
    user = client.select_record(table="User", telegram_id=telegram_id)
    return user
