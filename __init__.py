__package__ = 'bot'

from typing import List, Tuple, Union
import sqlite3


class DBClient():
    def __init__(self) -> None:
        database_uri = 'src/user.db'
        self.connection = sqlite3.connect(database=database_uri)
        self.cursor = self.connection.cursor()

    def __del__(self) -> None:
        self.connection.commit()
        self.connection.close()

    def readall(self, table) -> List:
        sql = f'select * from {table}'
        res = self.cursor.execute(sql)
        return res.fetchall()

    def read_one(self, table, telegram_id) -> Union[Tuple, None]:
        sql = f'select * from {table} where telegramId = {telegram_id}'
        res = self.cursor.execute(sql)
        return res.fetchone()

    def insert(self, table, nickname, telegram_id) -> sqlite3.Cursor:
        sql = f'insert into {table} (role, nickname, telegramId, allow) values (?, ?, ?, ?)'
        res = self.cursor.execute(sql, ("User", nickname, telegram_id, 1))
        self.connection.commit()
        return res

    def update(self, table, telegram_id, allow) -> sqlite3.Cursor:
        sql = f'update {table} set allow = {allow} where telegramId = {telegram_id}'
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res

    def delete(self, table, telegram_id) -> sqlite3.Cursor:
        sql = f'delete from {table} where telegramId = {telegram_id}'
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res

