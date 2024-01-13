#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
from functools import wraps
from typing import Callable, cast

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler, ExtBot

from src.constants.constant import (
    WAITING,
    PERMITTED,
    PREMIUM,
    APPROVE,
    DECLINE,
    UPGRADE,
    DOWNGRADE,
    WAITING_COLUMN,
    ALLOW_COLUMN,
    PREMIUM_COLUMN,
)
from src.constants.messages import (
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
    UPGRADE_MESSAGE,
    DOWNGRANDE_MESSAGE,
)
from src.utils import update_user, query_user, query


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
        return await func(
            bot=bot,
            callback_query=callback_query,
            query_data=query_data,
            *args,
            **kwargs,
        )

    return wrapper


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        _ = context  # no meaning. just for LSP to ignore unaccessed params
        return -1

    if not update.effective_user:
        return -1

    admin_id = int(os.getenv("DEVELOPER_CHAT_ID", 0))
    admins = [admin_id, 67466212]
    if update.effective_user.id not in admins:
        await update.message.reply_text(text="Opops! you are not my master!")
        return -1

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
async def query_list(
    bot: ExtBot, callback_query: CallbackQuery, query_data: str
) -> int:
    _ = bot  # no meaning. just for LSP
    maps = {}
    if query_data == WAITING:
        maps.update({WAITING_COLUMN: 1})
    if query_data == PERMITTED:
        maps.update({ALLOW_COLUMN: 1})
    if query_data == PREMIUM:
        maps.update({PREMIUM_COLUMN: 1})

    users = query(table="User", maps=maps)

    extra_row = [
        InlineKeyboardButton("Back", callback_data="back"),
        InlineKeyboardButton("Finish", callback_data="finish"),
    ]

    if not users:
        await callback_query.edit_message_text(
            text=f"目前{query_data}没有用户",
            reply_markup=InlineKeyboardMarkup([extra_row]),
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
        return MANAGER

    inline_keyboard = [
        [
            InlineKeyboardButton(
                f"👤 {users[i][1]} - {users[i][2]}", callback_data=str(users[i][2])
            ),
            InlineKeyboardButton(
                f"👤 {users[i+1][1]} - {users[i+1][2]}",
                callback_data=str(users[i + 1][2]),
            ),
        ]
        for i in range(0, len(users) - 1, 2)
    ]

    if len(users) % 2 == 1:
        user_index = len(users) - 1
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    f"👤 {users[user_index][1]} - {users[user_index][2]}",
                    callback_data=str(users[user_index][2]),
                )
            ]
        )

    inline_keyboard.append(extra_row)

    await callback_query.edit_message_text(
        text=f"这是{query_data}: ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    return MANAGER


@check_callback
async def manage_user(
    bot: ExtBot, callback_query: CallbackQuery, query_data: str
) -> int:
    _ = bot  # no meaning. just for LSP
    user = cast(tuple, query_user(int(query_data)))
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
async def action(bot: ExtBot, callback_query: CallbackQuery, query_data: str) -> int:
    act, telegram_id = query_data.split()
    inline_keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="back"),
            InlineKeyboardButton("Finish", callback_data="finish"),
        ],
    ]
    try:
        if act == APPROVE:
            update_user(int(telegram_id), 1, 0, 0)
            await bot.send_message(chat_id=int(telegram_id), text=APPROVED_MESSAGE)
        if act == DECLINE:
            update_user(int(telegram_id), 0, 0, 1)
            await bot.send_message(chat_id=int(telegram_id), text=DECLINE_MESSAGE)
        if act == UPGRADE:
            update_user(int(telegram_id), 1, 1, 0)
            await bot.send_message(chat_id=int(telegram_id), text=UPGRADE_MESSAGE)
        if act == DOWNGRADE:
            update_user(int(telegram_id), 1, 0, 0)
            await bot.send_message(chat_id=int(telegram_id), text=DOWNGRANDE_MESSAGE)
        await callback_query.edit_message_text(
            text="As you wish, Sir",
            reply_markup=InlineKeyboardMarkup(inline_keyboard),
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
    except Exception as e:
        await callback_query.edit_message_text(
            text=f"the action was successfully done, but a error was happen, here is the reson\n{e}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard),
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
    return MANAGER


@check_callback
async def back(bot: ExtBot, callback_query: CallbackQuery, query_data: str) -> int:
    _ = bot, query_data  # no meaning. just for LSP
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
async def finish(bot: ExtBot, callback_query: CallbackQuery, query_data: str) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    _ = bot, query_data  # no meaning. just for LSP
    # await callback_query.answer()
    await callback_query.edit_message_text(text="Good bye, Sir!")
    return ConversationHandler.END
