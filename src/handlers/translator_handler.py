#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from telegram import Update
from telegram.ext import ContextTypes
from telegram._replykeyboardmarkup import ReplyKeyboardMarkup

# from telegram import MessageEntity

from src.constants import TARGET_LANGUAGE_KEYBOARD

from src.helpers import check_permission


@check_permission
async def translator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
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
