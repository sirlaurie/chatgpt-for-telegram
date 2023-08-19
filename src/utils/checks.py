#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from typing import Tuple
from .db import DBClient
from src.constants import NOT_ALLOWD, NOT_PERMITED


client = DBClient()


def is_allowed(user_id: int) -> Tuple[bool, bool, str]:
    user = client.read_one(table="User", telegram_id=user_id)
    if not isinstance(user, Tuple):
        return (False, False, NOT_PERMITED)
    *_, allow, premium = user
    return (bool(allow), bool(premium), NOT_ALLOWD)


def add(user_id: int, nickname: str, allow: int, premium: int) -> int:
    res = client.insert("User", nickname, user_id, allow, premium)
    return res.rowcount
