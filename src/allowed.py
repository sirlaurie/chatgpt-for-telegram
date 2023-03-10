from typing import Tuple

from db import DBClient
from constants.messages import NOT_ALLOWD, NOT_PERMITED


quota_exceeded = (
    "You exceeded your current quota, please check your plan and billing details."
)

client = DBClient()


def allowed(user_id) -> Tuple[bool, str]:
    user = client.read_one(table="User", telegram_id=user_id)
    if not isinstance(user, Tuple):
        return (False, NOT_PERMITED)
    *_, allow = user
    return (bool(allow), NOT_ALLOWD)


def add(user_id, nickname, allow) -> int:
    res = client.insert("User", nickname, user_id, allow)
    return res.rowcount


if __name__ == "__main__":
    print(allowed(0))
