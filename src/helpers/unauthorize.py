#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.constants import (
    APPROVE,
    DECLINE,
    NOT_PERMITED,
    ASK_FOR_PERMITED,
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
    PROCESS_TIMEOUT,
)
from src.utils import is_allowed, add, update as update_user


apply_timeout: float = 3600.0


async def warning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    global message_id
    user_id = update.effective_user.id
    msg = await update.message.reply_text(
        text=NOT_PERMITED.format(user_id=user_id), pool_timeout=3600.0
    )
    message_id = msg.id
    add(int(update.effective_user.id), str(update.effective_user.first_name), 0, 0, 1)

    async def execute_after_add():
        try:
            await apply_to_approve(update, context)
        except asyncio.CancelledError:
            pass

    async def sleep_and_edit_msg():
        await asyncio.sleep(apply_timeout)
        allow, *_ = is_allowed(user_id=user_id)
        if not allow:
            await msg.edit_text(text=PROCESS_TIMEOUT, pool_timeout=3600.0)

    asyncio.create_task(execute_after_add())
    asyncio.create_task(sleep_and_edit_msg())


async def apply_to_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    bot = context.bot
    admin_id = int(os.getenv("DEVELOPER_CHAT_ID", 0))
    telegram_id = update.effective_user.id
    username = update.effective_user.first_name
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
    msg = await bot.send_message(
        chat_id=admin_id,
        text=ASK_FOR_PERMITED.format(name=username, user_id=telegram_id),
        reply_markup=InlineKeyboardMarkup(inline_markup),
        read_timeout=3600.0,
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )

    async def edit_after_not_response():
        await asyncio.sleep(apply_timeout)
        allow, *_ = is_allowed(user_id=telegram_id)
        if not allow:
            await msg.edit_text(
                text=f"Sir, User {username} asked to chat with me, however you didn't approve it. now it has on waitlist",
                read_timeout=3600.0,
                write_timeout=3600.0,
                pool_timeout=3600.0,
            )

    asyncio.create_task(edit_after_not_response())

    return


async def approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    callback_query = update.callback_query
    if not callback_query:
        return
    message = callback_query.message
    if not message:
        return

    await callback_query.answer()
    bot = context.bot
    query_data = callback_query.data
    if not query_data:
        return
    act, telegram_id = query_data.split()

    if act == APPROVE:
        update_user(int(telegram_id), 1, 0, 0)
        await bot.send_message(
            chat_id=int(telegram_id),
            text=APPROVED_MESSAGE,
            read_timeout=3600.0,
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
        await bot.delete_message(chat_id=telegram_id, message_id=message_id)

    if act == DECLINE:
        update_user(int(telegram_id), 0, 0, 0)
        await bot.send_message(
            chat_id=int(telegram_id),
            text=DECLINE_MESSAGE,
            read_timeout=3600.0,
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )

    await message.edit_text(
        text="As your wish, Sir",
        read_timeout=3600.0,
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    await bot.close(write_timeout=3600.0, pool_timeout=3600.0)
    return
