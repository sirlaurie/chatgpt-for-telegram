import sys
from typing import Tuple

sys.path.insert(0, "..")
from bot import DBClient  # type: ignore

not_allowd = "not_allowd"
quota_exceeded = (
    "You exceeded your current quota, please check your plan and billing details."
)

client = DBClient()


def allowed(user_id) -> Tuple[bool, str]:
    user = client.read_one(table="User", telegram_id=user_id)
    if not isinstance(user, Tuple):
        return (False, not_allowd)
    *_, allow = user
    return (bool(allow), quota_exceeded)


def add(user_id, nickname) -> int:
    res = client.insert("User", nickname, user_id)
    return res.rowcount


if __name__ == "__main__":
    print(allowed(0))
