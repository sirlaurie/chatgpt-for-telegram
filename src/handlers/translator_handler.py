#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from telegram import Update
from telegram.ext import ContextTypes
from telegram._replykeyboardmarkup import ReplyKeyboardMarkup

# from telegram import MessageEntity

from constants.messages import (
    NOT_ALLOWD,
    NOT_PERMITED,
    TARGET_LANGUAGE_KEYBOARD,
)

from allowed import allowed
from utils import waring


async def translator_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    permitted, _, msg = allowed(context._user_id)
    if not permitted and msg == NOT_PERMITED:
        await waring(update, context, msg)
        return
    if not permitted and msg == NOT_ALLOWD:
        await update.message.reply_text(text=NOT_ALLOWD)
        return

    target_language_keyboard = [TARGET_LANGUAGE_KEYBOARD]
    markup = ReplyKeyboardMarkup(
        target_language_keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        text="首先,请选择你要翻译为哪种语言?",
        reply_markup=markup,
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )
    return
