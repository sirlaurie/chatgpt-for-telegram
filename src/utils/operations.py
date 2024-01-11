#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from typing import Dict, Iterable, List, Optional, Tuple, Union
import time
from ._db import DBClient
from src.constants.messages import NOT_ALLOWD, NOT_PERMITED


client = DBClient()


def is_allowed(user_id: int) -> Tuple[bool, bool, bool, str]:
    user = client.select_record(table="User", telegram_id=user_id)
    if not isinstance(user, Tuple):
        return (False, False, False, NOT_PERMITED)
    *_, allow, premium, waiting = user
    return (bool(allow), bool(premium), bool(waiting), NOT_ALLOWD)


def add_user(
    user_id: int, nickname: str, allow: int, premium: int, waiting: int
) -> None:
    client.insert_record(
        table="User",
        data={
            "role": "User",
            "nickname": nickname,
            "telegramId": user_id,
            "allow": allow,
            "premium": premium,
            "waiting": waiting,
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
