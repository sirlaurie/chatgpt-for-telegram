import sys
from typing import Tuple
sys.path.append("..")
from bot import DBClient # type: ignore

client = DBClient()


def allowed(user_id) -> bool:
    user = client.read_one(table="User", telegram_id=user_id)
    if not isinstance(user, Tuple):
        return False
    *_, allow = user
    return bool(allow)

def add(user_id, nickname) -> int:
    res = client.insert('User', nickname, user_id)
    return res.rowcount

if __name__ == '__main__':
    print(allowed(82315261))
