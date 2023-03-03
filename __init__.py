__package__ = "bot"

from typing import List, Tuple, Union
import sqlite3


class DBClient:
    def __init__(self) -> None:
        database_uri = "user.db"
        self.connection = sqlite3.connect(database=database_uri)
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='User'"
        )
        result = self.cursor.fetchone()
        if result is None:
            self.cursor.execute(
                """CREATE TABLE User
                         (role TEXT NOT NULL,
                          nickname TEXT NOT NULL,
                          telegramId INTEGER PRIMARY KEY,
                          allow INT NOT NULL)"""
            )
            self.connection.commit()

    def __del__(self) -> None:
        self.connection.commit()
        self.connection.close()

    def check_table(self, table: str) -> Union[int, None]:
        result = self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name={table}"
            )
        return result.fetchone()

    def create_table(self, table: str, fields: dict) -> None:
        fields_sql = ', '.join([f'{field_name} {field_type}' for field_name, field_type in fields.items()])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({fields_sql})")
        self.connection.commit()

    def readall(self, table: str) -> List:
        sql = f"SELECT * FROM {table}"
        res = self.cursor.execute(sql)
        return res.fetchall()

    def read_one(self, table: str, telegram_id) -> Union[Tuple, None]:
        sql = f"SELECT * FROM {table} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        return res.fetchone()

    def insert(self, table: str, nickname: str, telegram_id) -> sqlite3.Cursor:
        sql = f"INSERT INTO {table} (role, nickname, telegramId, allow) VALUES (?, ?, ?, ?)"
        res = self.cursor.execute(sql, ("User", nickname, telegram_id, 1))
        self.connection.commit()
        return res

    def update(self, table: str, telegram_id: str, allow) -> sqlite3.Cursor:
        sql = f"UPDATE {table} SET allow = {allow} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res

    def delete(self, table: str, telegram_id) -> sqlite3.Cursor:
        sql = f"DELETE FROM {table} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res
