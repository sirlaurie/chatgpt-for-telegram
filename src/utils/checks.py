#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from typing import Iterable, List, Tuple
from .db import DBClient
from src.constants import NOT_ALLOWD, NOT_PERMITED


client = DBClient()


def is_allowed(user_id: int) -> Tuple[bool, bool, bool, str]:
    user = client.read_one(table="User", telegram_id=user_id)
    if not isinstance(user, Tuple):
        return (False, False, False, NOT_PERMITED)
    *_, allow, premium, waiting = user
    return (bool(allow), bool(premium), bool(waiting), NOT_ALLOWD)


def add(user_id: int, nickname: str, allow: int, premium: int, waiting: int) -> int:
    res = client.insert(nickname, user_id, allow, premium, waiting)
    return res


def update(telegram_id: int, allow: int, premium: int, waiting: int) -> int:
    res = client.update(telegram_id, allow, premium, waiting)
    return res

def query(maps: dict) -> List[Tuple]:
    if not isinstance(maps, Iterable):
        return []
    column, value = next(iter(maps.items()))
    users = client.query(column=column, value=value)
    return users


def query_one(telegram_id: int) -> Tuple | None:
    user = client.read_one(telegram_id)
    return user
