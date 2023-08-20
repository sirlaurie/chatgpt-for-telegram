#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


from functools import wraps
from typing import Callable, cast
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.constants import (
    WAITING,
    PERMITTED,
    PREMIUM,
    APPROVE,
    DECLINE,
    UPGRADE,
    DOWNGRADE,
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
    UPGRADE_MESSAGE,
    DOWNGRANDE_MESSAGE,
    WAITING_COLUMN,
    ALLOW_COLUMN,
    PREMIUM_COLUMN,
)
from src.utils import update, query, query_one


CHOOSING, MANAGER = range(2)


def check_callback(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ) -> int:
        callback_query = update.callback_query
        if not callback_query:
            return -1
        await callback_query.answer()
        query_data = callback_query.data
        if not query_data:
            return -1
        bot = context.bot
        return await func(bot, callback_query, query_data, *args, **kwargs)

    return wrapper


async def admin_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None | int:
    if not update.message:
        return

    inline_keyboard = [
        [
            InlineKeyboardButton(WAITING, callback_data=WAITING),
            InlineKeyboardButton(PERMITTED, callback_data=PERMITTED),
            InlineKeyboardButton(PREMIUM, callback_data=PREMIUM),
        ],
        [
            InlineKeyboardButton("Back", callback_data="back"),
            InlineKeyboardButton("Finish", callback_data="finish"),
        ],
    ]
    await update.message.reply_text(
        text="选择需要管理的名单: ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
    )

    return CHOOSING


@check_callback
async def query_list(bot, callback_query, query_data) -> int:
    maps = {}
    if query_data == WAITING:
        maps.update({WAITING_COLUMN: 1})
    if query_data == PERMITTED:
        maps.update({ALLOW_COLUMN: 1})
    if query_data == PREMIUM:
        maps.update({PREMIUM_COLUMN: 1})

    users = query(maps)

    inline_keyboard = []

    if not users:
        await callback_query.edit_message_text(
            text=f"目前{query_data}没有用户",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Back", callback_data="back"),
                        InlineKeyboardButton("Finish", callback_data="finish"),
                    ]
                ]
            ),
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
        return MANAGER

    for user_index in range(len(users)):
        if user_index % 2 == 0:
            user_1 = users[user_index]
            if user_index < len(users) - 1:
                user_2 = users[user_index + 1]
                user_row = [
                    InlineKeyboardButton(
                        f"👤 {user_1[1]} - {user_1[2]}", callback_data=str(user_1[2])
                    ),
                    InlineKeyboardButton(
                        f"👤 {user_2[1]} - {user_2[2]}", callback_data=str(user_2[2])
                    ),
                ]
            else:
                user_row = [
                    InlineKeyboardButton(
                        f"👤 {user_1[1]} - {user_1[2]}", callback_data=str(user_1[2])
                    ),
                ]

            inline_keyboard.append(user_row)

    inline_keyboard.append(
        [
            InlineKeyboardButton("Back", callback_data="back"),
            InlineKeyboardButton("Finish", callback_data="finish"),
        ]
    )

    await callback_query.edit_message_text(
        text=f"这是{query_data}: ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    return MANAGER


@check_callback
async def manage_user(bot, callback_query, query_data) -> int:
    user = cast(tuple, query_one(int(query_data)))
    inline_keyboard = [
        [
            InlineKeyboardButton(f"{APPROVE}", callback_data=f"{APPROVE} {user[2]}"),
            InlineKeyboardButton(f"{DECLINE}", callback_data=f"{DECLINE} {user[2]}"),
            InlineKeyboardButton(f"{UPGRADE}", callback_data=f"{UPGRADE} {user[2]}"),
            InlineKeyboardButton(
                f"{DOWNGRADE}", callback_data=f"{DOWNGRADE} {user[2]}"
            ),
        ],
        [
            InlineKeyboardButton("Back", callback_data="back"),
            InlineKeyboardButton("Finish", callback_data="finish"),
        ],
    ]
    await callback_query.edit_message_text(
        text=f"选择对用户 {user[1]} 的操作: ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    return MANAGER


@check_callback
async def action(bot, callback_query, query_data) -> int:
    act, telegram_id = query_data.split()
    if act == APPROVE:
        update(int(telegram_id), 1, 0, 0)
        await bot.send_message(chat_id=int(telegram_id), text=APPROVED_MESSAGE)
    if act == DECLINE:
        update(int(telegram_id), 0, 0, 1)
        await bot.send_message(chat_id=int(telegram_id), text=DECLINE_MESSAGE)
    if act == UPGRADE:
        update(int(telegram_id), 1, 1, 0)
        await bot.send_message(chat_id=int(telegram_id), text=UPGRADE_MESSAGE)
    if act == DOWNGRADE:
        update(int(telegram_id), 1, 0, 0)
        await bot.send_message(chat_id=int(telegram_id), text=DOWNGRANDE_MESSAGE)
    inline_keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="back"),
            InlineKeyboardButton("Finish", callback_data="finish"),
        ],
    ]
    await callback_query.edit_message_text(
        text="As you wish, Sir",
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    return MANAGER


@check_callback
async def back(bot, callback_query, query_data) -> int:
    inline_keyboard = [
        [
            InlineKeyboardButton(WAITING, callback_data=WAITING),
            InlineKeyboardButton(PERMITTED, callback_data=PERMITTED),
            InlineKeyboardButton(PREMIUM, callback_data=PREMIUM),
        ],
        [
            InlineKeyboardButton("Back", callback_data="back"),
            InlineKeyboardButton("Finish", callback_data="finish"),
        ],
    ]
    await callback_query.edit_message_text(
        text="选择需要管理的名单: ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    return CHOOSING


@check_callback
async def finish(bot, callback_query, query_data) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    await callback_query.answer()
    await callback_query.edit_message_text(text="Good bye, Sir!")
    return ConversationHandler.END
