from typing import List, Tuple, Union
from collections.abc import Iterable
import sqlite3
import sys
sys.path.append("..")

from bot.allowed import add # type: ignore

from telegram import Update
from telegram.ext import ContextTypes
from telegram._replykeyboardmarkup import ReplyKeyboardMarkup


async def waring(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
            text=f"你没有权限访问此bot.请将你的id {context._user_id} 发送给管理员, 等待批准. 最长耗时约1小时🤔"
        )

async def apply_to_prove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    yes_or_no_keyboard = [["Approved", "Decline"]]
    markup = ReplyKeyboardMarkup(
        yes_or_no_keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await bot.sendMessage(
        chat_id=82315261,
        text=f"User {update.message.chat.first_name}, id: {context._user_id} want to chat with me, would you like to allow it?",
        reply_markup=markup,
        pool_timeout=3600.0,
    )
    updater = await bot.get_updates(pool_timeout=3600.0)
    if not isinstance(updater, Iterable):
        await update.message.reply_text(text=f"到目前为止, 管理员尚未处理你的请求.🤯")
    if isinstance(updater, Iterable):
        reply_obj = updater[0]
        message = reply_obj.message
        if message.chat.id == 82315261 and message.text == "Approved":
            allow_to_chat = add(context._user_id, update.message.chat.first_name)
            await update.message.reply_text(
                text=f"管理员已经批准了你的请求, 现在你可以和我聊天啦.🥳"
            ) if allow_to_chat else await update.message.reply_text(
                text=f"抱歉, 管理员拒绝了你的请求. 可能他并不认识你🫢"
            )


class DBClient():
    def __init__(self) -> None:
        database_uri = 'user.db'
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

