from typing import List, Tuple, Dict, Union, Optional
import os
import re
import sqlite3


def validate_identifier(identifier: str) -> str:
    # 使用正则表达式验证标识符，防止SQL注入攻击
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
        raise ValueError(f"Invalid identifier: {identifier}")
    return identifier


class DBClient:
    uri = os.environ.get("database_uri", "bot.db")

    def __init__(self) -> None:
        self.connection = sqlite3.connect(database=DBClient.uri)
        self.cursor = self.connection.cursor()
        user_table_exist = self.check_table("User")
        if not user_table_exist:
            self.create_table(
                "User",
                {
                    "role": "TEXT",
                    "nickname": "TEXT",
                    "telegramId": "INTEGER",
                    "allow": "INTEGER",
                    "premium": "INTEGER",
                    "waiting": "INTEGER",
                    "free_messages_used": "INTEGER DEFAULT 0",
                    "subscription_status": "TEXT DEFAULT 'free'",
                    "subscription_type": "TEXT",
                    "subscription_start_date": "INTEGER",
                    "subscription_end_date": "INTEGER",
                    "stripe_customer_id": "TEXT",
                    "last_message_date": "INTEGER",
                },
            )
        else:
            # Migrate existing User table - add new columns if they don't exist
            self._migrate_user_table()

        prompt_table_exist = self.check_table("Prompt")
        if not prompt_table_exist:
            self.create_table(
                "Prompt",
                {
                    "telegramId": "INTEGER",
                    "name": "TEXT",
                    "prompt": "TEXT",
                    "create_at": "INTEGER",
                    "share": "INTEGER",
                },
            )
        assistant_table_exist = self.check_table("Assistant")
        if not assistant_table_exist:
            self.create_table(
                "Assistant",
                {
                    "telegramId": "INTEGER",
                    "name": "TEXT",
                    "assistant_id": "TEXT",
                    "create_at": "INTEGER",
                    "share": "INTEGER",
                },
            )

        # Create Payment table
        payment_table_exist = self.check_table("Payment")
        if not payment_table_exist:
            self.create_table(
                "Payment",
                {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "telegramId": "INTEGER",
                    "stripe_payment_id": "TEXT",
                    "stripe_subscription_id": "TEXT",
                    "amount": "REAL",
                    "currency": "TEXT DEFAULT 'USD'",
                    "status": "TEXT",
                    "payment_type": "TEXT",
                    "created_at": "INTEGER",
                    "updated_at": "INTEGER",
                },
            )

        # Create Subscription table
        subscription_table_exist = self.check_table("Subscription")
        if not subscription_table_exist:
            self.create_table(
                "Subscription",
                {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "telegramId": "INTEGER",
                    "stripe_subscription_id": "TEXT UNIQUE",
                    "stripe_customer_id": "TEXT",
                    "status": "TEXT",
                    "plan_type": "TEXT",
                    "current_period_start": "INTEGER",
                    "current_period_end": "INTEGER",
                    "cancel_at_period_end": "INTEGER DEFAULT 0",
                    "created_at": "INTEGER",
                    "updated_at": "INTEGER",
                },
            )

    def _migrate_user_table(self) -> None:
        """Migrate existing User table to add new subscription-related columns"""
        # Get existing columns
        self.cursor.execute("PRAGMA table_info(User)")
        existing_columns = {row[1] for row in self.cursor.fetchall()}

        # Define new columns to add
        new_columns = {
            "free_messages_used": "INTEGER DEFAULT 0",
            "subscription_status": "TEXT DEFAULT 'free'",
            "subscription_type": "TEXT",
            "subscription_start_date": "INTEGER",
            "subscription_end_date": "INTEGER",
            "stripe_customer_id": "TEXT",
            "last_message_date": "INTEGER",
        }

        # Add missing columns
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE User ADD COLUMN {validate_identifier(column_name)} {column_type}"
                    self.cursor.execute(sql)
                    self.connection.commit()
                except sqlite3.OperationalError as e:
                    # Column might already exist, ignore
                    pass

    def __del__(self) -> None:
        self.connection.commit()
        self.connection.close()

    def check_table(self, table: str) -> bool:
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.cursor.execute(sql, (table,))
        row = result.fetchone()
        return bool(row)

    def create_table(self, table: str, fields: dict[str, str]) -> None:
        # 验证字段类型，确保它们是合法的数据类型
        valid_field_types = ["INTEGER", "TEXT", "REAL", "BLOB", "NULL", "PRIMARY", "AUTOINCREMENT", "UNIQUE"]
        for field_type in fields.values():
            # Extract the base type (first word) from field definition
            # e.g., "INTEGER DEFAULT 0" -> "INTEGER"
            base_type = field_type.strip().split()[0].upper()
            if base_type not in valid_field_types:
                raise ValueError(f"Invalid field type: {field_type}")

        fields_sql = ", ".join(
            [
                f"{validate_identifier(field_name)} {field_type}"
                for field_name, field_type in fields.items()
            ]
        )
        sql = f"CREATE TABLE IF NOT EXISTS {validate_identifier(table)} ({fields_sql})"

        self.cursor.execute(sql)
        self.connection.commit()

    def insert_record(self, table: str, data: Dict[str, Union[str, int]]) -> None:
        """
        插入记录
        """
        columns = ", ".join(data.keys())
        values = ", ".join(["?" for _ in range(len(data))])
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        self.cursor.execute(query, tuple(data.values()))
        self.connection.commit()

    def update_record(
        self, table: str, telegram_id: int, data: Dict[str, Union[str, int]]
    ) -> None:
        """
        更新记录
        """
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE telegramId = ?"
        self.cursor.execute(query, tuple(data.values()) + (telegram_id,))
        self.connection.commit()

    def delete_record(self, table: str, telegram_id: int) -> None:
        """
        删除记录
        """
        query = f"DELETE FROM {table} WHERE telegramId = ?"
        self.cursor.execute(query, (telegram_id,))
        self.connection.commit()

    def select_record(self, table: str, telegram_id: int) -> Optional[Tuple]:
        """
        查询记录
        """
        query = f"SELECT * FROM {table} WHERE telegramId = ?"
        self.cursor.execute(query, (telegram_id,))
        result = self.cursor.fetchone()
        if result:
            return result
        else:
            return None

    def readall(self, table: str) -> List[Tuple]:
        sql = f"SELECT * FROM {table};"
        res = self.cursor.execute(sql)
        return res.fetchall()

    def query(self, table: str, column: str, value: Union[int, str]) -> List[Tuple]:
        sql = f"SELECT * FROM {table} WHERE {column} = ?"
        res = self.cursor.execute(sql, (value,))
        return res.fetchall()

    def execute_query(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        """Execute a custom SQL query with parameters"""
        res = self.cursor.execute(sql, params)
        self.connection.commit()
        return res.fetchall()

    def execute_one(self, sql: str, params: Tuple = ()) -> Optional[Tuple]:
        """Execute a custom SQL query and return one result"""
        res = self.cursor.execute(sql, params)
        return res.fetchone()

    def get_column_value(self, table: str, telegram_id: int, column: str) -> Optional[Union[str, int]]:
        """Get a specific column value for a user"""
        sql = f"SELECT {validate_identifier(column)} FROM {validate_identifier(table)} WHERE telegramId = ?"
        result = self.cursor.execute(sql, (telegram_id,))
        row = result.fetchone()
        return row[0] if row else None

    def update_column(self, table: str, telegram_id: int, column: str, value: Union[str, int]) -> None:
        """Update a specific column for a user"""
        sql = f"UPDATE {validate_identifier(table)} SET {validate_identifier(column)} = ? WHERE telegramId = ?"
        self.cursor.execute(sql, (value, telegram_id))
        self.connection.commit()

    # def read_one(self, telegram_id: int, table: str = "User") -> Optional[Tuple]:
    #     sql = f"SELECT * FROM {table} WHERE telegramId = ?"
    #     res = self.cursor.execute(sql, (telegram_id,))
    #     return res.fetchone()
