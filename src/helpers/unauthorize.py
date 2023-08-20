#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.constants import (
    APPROVE,
    DECLINE,
    NOT_PERMITED,
    ASK_FOR_PERMITED,
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
)
from src.utils import add, update as update_user


async def warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    await update.message.reply_text(
        text=NOT_PERMITED.format(user_id=context._user_id), pool_timeout=3600.0
    )
    add(int(update.effective_user.id), str(update.effective_user.first_name), 0, 0, 1)
    return await apply_to_approve(update, context)


async def apply_to_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    if not update.message:
        return
    bot = context.bot
    admin_id = int(os.getenv("DEVELOPER_CHAT_ID", 0))
    telegram_id = update.effective_user.id
    inline_markup = [
        [
            InlineKeyboardButton(
                text="Approved", callback_data=f"{APPROVE} {telegram_id}"
            ),
            InlineKeyboardButton(
                text="Decline", callback_data=f"{DECLINE} {telegram_id}"
            ),
        ]
    ]
    await bot.send_message(
        chat_id=admin_id,
        text=ASK_FOR_PERMITED.format(
            name=update.message.chat.first_name, user_id=context._user_id
        ),
        reply_markup=InlineKeyboardMarkup(inline_markup),
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    return


async def approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    callback_query = update.callback_query
    if not callback_query:
        return
    await callback_query.answer()
    bot = context.bot
    admin_id = os.getenv("DEVELOPER_CHAT_ID", 0)
    query_data = callback_query.data
    if not query_data:
        return
    act, telegram_id = query_data.split()
    if act == APPROVE:
        update_user(int(telegram_id), 1, 0, 0)
        await bot.send_message(
            chat_id=int(telegram_id),
            text=APPROVED_MESSAGE,
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
    if act == DECLINE:
        update_user(int(telegram_id), 0, 0, 0)
        await bot.send_message(
            chat_id=int(telegram_id),
            text=DECLINE_MESSAGE,
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
    await bot.send_message(
            chat_id=int(admin_id),
            text="As your wish, Sir",
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
    return
