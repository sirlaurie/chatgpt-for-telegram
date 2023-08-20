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
                          allow INT NOT NULL,
                          premium INTEGER NOT NULL,
                          waiting INTEGER NOt NULL)"""
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
        fields_sql = ", ".join(
            [f"{field_name} {field_type}" for field_name, field_type in fields.items()]
        )
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({fields_sql})")
        self.connection.commit()

    def readall(self, table: str) -> List[Tuple]:
        sql = f"SELECT * FROM {table}"
        res = self.cursor.execute(sql)
        return res.fetchall()

    def query(self, column: str, value: str | int, table: str = "User") -> List[Tuple]:
        sql = f"SELECT * FROM {table} WHERE {column} = {value}"
        res = self.cursor.execute(sql)
        return res.fetchall()

    def read_one(self, telegram_id: int, table: str = "User") -> Union[Tuple, None]:
        sql = f"SELECT * FROM {table} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        return res.fetchone()

    def insert(
        self, nickname: str, telegram_id: int, allow: int, premium: int, waiting: int, table: str = "User"
    ) -> int:
        sql = f"INSERT INTO {table} (role, nickname, telegramId, allow, premium, waiting) VALUES (?, ?, ?, ?, ?, ?)"
        res = self.cursor.execute(sql, ("User", nickname, telegram_id, allow, premium, waiting))
        self.connection.commit()
        return res.rowcount

    def update(
        self, telegram_id: int, allow: int, premium: int, waiting: int, table: str = "User"
    ) -> int:
        sql = f"UPDATE {table} SET allow = {allow}, premium = {premium}, waiting = {waiting} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res.rowcount

    def delete(self, telegram_id: int, table: str = "User") -> int:
        sql = f"DELETE FROM {table} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res.rowcount
