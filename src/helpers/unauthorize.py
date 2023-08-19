#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
from typing import Tuple
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.constants import (
    YES_OR_NO_KEYBOARD,
    NOT_PERMITED,
    ASK_FOR_PERMITED,
    PROCESS_TIMEOUT,
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
)
from src.utils import add


async def warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text(
            text=NOT_PERMITED.format(user_id=context._user_id), pool_timeout=3600.0
        )
        return await apply_to_approve(update, context)


async def apply_to_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return

    if not update.message:
        return
    bot = context.bot
    admin_id = int(os.getenv("DEVELOPER_CHAT_ID", 0))
    yes_or_no_keyboard = [YES_OR_NO_KEYBOARD]
    markup = ReplyKeyboardMarkup(
        yes_or_no_keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    message = await bot.sendMessage(
        chat_id=admin_id,
        text=ASK_FOR_PERMITED.format(
            name=update.message.chat.first_name, user_id=context._user_id
        ),
        reply_markup=markup,
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )

    update_from_admin = await bot.get_updates(
        timeout=3600, read_timeout=3600.0, pool_timeout=3600.0
    )

    if isinstance(update_from_admin, Tuple) and len(update_from_admin) == 0:
        await update.message.reply_text(text=PROCESS_TIMEOUT)
        return

    if isinstance(update_from_admin, Tuple) and len(update_from_admin) > 0:
        reply_obj = update_from_admin[0]
        permit_message = reply_obj.message
        if not permit_message:
          return

        if (
            hasattr(permit_message, "chat")
            and permit_message.chat.id == admin_id
            and permit_message.text == "Approved"
        ):
            _ = add(update.effective_user.id, update.effective_user.first_name, 1, 0)
            await update.message.reply_text(text=APPROVED_MESSAGE)
            # await message.edit_reply_markup(reply_markup=None)
            return
        if (
            hasattr(permit_message, "chat")
            and permit_message.chat.id == admin_id
            and permit_message.text == "Decline"
        ):
            _ = add(update.effective_user.id, update.effective_user.first_name, 0, 0)
            await update.message.reply_text(text=DECLINE_MESSAGE)
            # await message.edit_reply_markup(reply_markup=None)
            return
