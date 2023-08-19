#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

# import re
from functools import wraps
import os
import json
import html
import logging
import sqlite3
from typing import Callable, List, Tuple, Union

from telegram.constants import ParseMode

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

# messages
NOT_PERMITED = "你没有权限访问此bot.请将你的id {user_id} 发送给管理员, 等待批准. 大约耗时一分钟.🤔\n PS: 如果你不知道管理员是谁, 说明这个bot并非一个公开的bot. \n\nYou do not have permission to access this bot. Please send your ID {user_id} to the my boss and wait for approval, which may take up to 1 min.\n PS: If you do not know who the boss is, it means that this bot is not a public bot."

NOT_ALLOWD = "你暂时不在允许聊天的列表中.\n\nYou are not on permit list."

YES_OR_NO_KEYBOARD = ["Approved", "Decline"]

TARGET_LANGUAGE_KEYBOARD = ["English", "Deutsch", "Française", "中文", "日本語"]

ASK_FOR_PERMITED = (
    "User {name}, id: {user_id} want to chat with me, would you like to allow it?"
)

PROCESS_TIMEOUT = "到目前为止, 管理员尚未处理你的请求.🤯\n\nthe administrator has not yet handled your request so far.🤯"

APPROVED_MESSAGE = "管理员已经批准了你的请求, 现在你可以和我聊天啦.🥳\n\nAdministrator has approved your request, now you can chat with me.🥳"

DECLINE_MESSAGE = "抱歉, 管理员拒绝了你的请求. 可能他并不认识你.🫢\n\nSorry, the administrator has denied your request. Perhaps they do not know you.🫢"

WELCOME_MESSAGE = "Hi, 你想和我说点什么吗"

NEW_CONVERSATION_MESSAGE = "好的, 已为你开启新会话! 请继续输入你的问题."

INIT_REPLY_MESSAGE = "hold my beer ... "


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
                          premium INTEGER NOT NULL)"""
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

    def readall(self, table: str) -> List:
        sql = f"SELECT * FROM {table}"
        res = self.cursor.execute(sql)
        return res.fetchall()

    def read_one(self, table: str, telegram_id) -> Union[Tuple, None]:
        sql = f"SELECT * FROM {table} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        return res.fetchone()

    def insert(
        self, table: str, nickname: str, telegram_id: int, allow: int, premium: int
    ) -> sqlite3.Cursor:
        sql = f"INSERT INTO {table} (role, nickname, telegramId, allow, premium) VALUES (?, ?, ?, ?, ?)"
        res = self.cursor.execute(sql, ("User", nickname, telegram_id, allow, premium))
        self.connection.commit()
        return res

    def update(self, table: str, telegram_id: str, allow: int, premium: int) -> sqlite3.Cursor:
        sql = f"UPDATE {table} SET allow = {allow}, premium = {premium} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res

    def delete(self, table: str, telegram_id) -> sqlite3.Cursor:
        sql = f"DELETE FROM {table} WHERE telegramId = {telegram_id}"
        res = self.cursor.execute(sql)
        self.connection.commit()
        return res


# Enable logging
logging.basicConfig(
    filename="error.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)

client = DBClient()


def allowed(user_id: int) -> Tuple[bool, bool, str]:
    user = client.read_one(table="User", telegram_id=user_id)
    if not isinstance(user, Tuple):
        return (False, False, NOT_PERMITED)
    *_, allow, premium = user
    return (bool(allow), bool(premium), NOT_ALLOWD)


def add(user_id: int, nickname: str, allow: int, premium: int) -> int:
    print(f"{user_id} - {nickname} has been approved")
    res = client.insert("User", nickname, user_id, allow, premium)
    print(res.rowcount)
    return res.rowcount


async def warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text(
            text=NOT_PERMITED.format(user_id=context._user_id), pool_timeout=3600.0
        )
        return await apply_to_prove(update, context)


async def apply_to_prove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    if not update.message:
        return

    bot = context.bot
    admin_id = os.getenv("DEVELOPER_CHAT_ID", 0)
    yes_or_no_keyboard = [YES_OR_NO_KEYBOARD]
    markup = ReplyKeyboardMarkup(
        yes_or_no_keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await bot.send_message(
        chat_id=admin_id,
        text=ASK_FOR_PERMITED.format(
            name=update.message.chat.first_name, user_id=context._user_id
        ),
        reply_markup=markup,
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )

    reply_from_admin = await bot.get_updates(timeout=10, pool_timeout=60.0)
    print(reply_from_admin)
    if reply_from_admin.text == "Approved":
        await admin_approved(update.effective_user.id, update.effective_user.first_name, 0, 0)
        await update.message.reply_text(text=APPROVED_MESSAGE)
        return
    if reply_from_admin.text == "Decline":
        await admin_declined(update.effective_user.id, update.effective_user.first_name, 0, 0)
        await update.message.reply_text(text=DECLINE_MESSAGE)
        return


async def admin_approved(user_id: int, nickname: str, allow: int, premium: int) -> None:
    print(f"update: {update.message.text}")
    # if update.effective_user.id == admin_id:
    _ = add(user_id, nickname, allow, premium)
    # await update.message.reply_text(text=APPROVED_MESSAGE)
    # await bot.delete_message(
    #     chat_id=update.effective_user.id, message_id=no_permit_message.id
    # )
    # await bot.delete_message(chat_id=admin_id, message_id=message.id)
    return


async def admin_declined(user_id: int, nickname: str, allow: int, premium: int) -> None:
    print(f"update: {update.message.text}")
    _ = add(user_id, nickname, allow, premium)
    return


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("请求超时")
    await update.message.reply_text(text=PROCESS_TIMEOUT)
    return


def check_permission(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(
        update: Update, context: CallbackContext, *args, **kwargs
    ) -> None | int:
        if not update.message:
            print("no message")
            return

        if not update.effective_user:
            print("no effective user")
            return

        permitted, _, msg = allowed(update.effective_user.id)
        if not permitted and msg == NOT_PERMITED:
            reply_from_admin = await warning(update, context)
            print(f"return {reply_from_admin}")
            return reply_from_admin
        if not permitted and msg == NOT_ALLOWD:
            await update.message.reply_text(text=NOT_ALLOWD)
            print("not allowed")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


@check_permission
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(text=WELCOME_MESSAGE)


def main() -> None:
    bot_token: str = os.environ.get("bot_token", "")
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            0: [
                MessageHandler(filters.Regex("^Approved$"), admin_approved),
                MessageHandler(filters.Regex("^Decline$"), admin_declined),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=False
    )
    # application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
