#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from constants.messages import (
    NOT_ALLOWD,
    NOT_PERMITED,
)
from constants.models import (
    gpt_3p5_turbo,
    gpt_3p5_turbo_16k,
    gpt_3p5_turbo_0613,
    gpt_3p5_turbo_16k_0613,
    gpt_4_0314,
    gpt_4_0613,
    gpt_4_32k_0314,
    gpt_4_32k_0613
)
from allowed import allowed
from utils import waring


async def switch_model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    context.bot_data.update({"model": query.data})

    await query.edit_message_text(text=f"OK! 已为您切换到 {query.data} 模型")


async def switch_model_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    permitted, premium, msg = allowed(context._user_id)
    if not permitted and msg == NOT_PERMITED:
        await waring(update, context, msg)
        return
    if not permitted and msg == NOT_ALLOWD and update.message:
        await update.message.reply_text(text=NOT_ALLOWD)
        return

    if not update.message:
        return
    if premium:
        inline_keybord = [
            [
                InlineKeyboardButton(
                    "gpt-3.5-turbo", callback_data=str(gpt_3p5_turbo)
                ),
                InlineKeyboardButton(
                    "gpt-3.5-turbo-0613", callback_data=str(gpt_3p5_turbo_0613)
                ),
            ],
            [
                InlineKeyboardButton(
                    "gpt-3.5-turbo-16k", callback_data=str(gpt_3p5_turbo_16k)
                ),
                InlineKeyboardButton(
                    "gpt-3.5-turbo-16k-0613",
                    callback_data=str(gpt_3p5_turbo_16k_0613),
                ),
            ],
            [
                InlineKeyboardButton("gpt-4-0314", callback_data=str(gpt_4_0314)),
                InlineKeyboardButton("gpt-4-32k-0314", callback_data=str(gpt_4_32k_0314)),
            ],
            [
                InlineKeyboardButton("gpt-4-0613", callback_data=str(gpt_4_0613)),
                InlineKeyboardButton("gpt-4-32k-0613", callback_data=str(gpt_4_32k_0613)),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keybord)

        await update.message.reply_text(
            f"当前使用的模型是: {context.bot_data.get('model', None) or os.getenv('model')}. 切换你要使用的模型:",
            reply_markup=reply_markup,
        )
        return

    await update.message.reply_text(
        "Sorry, 由于GPT-4等高级模型的费用较高(GPT-3.5的20倍), 默认用户当前只能使用GPT-3.5-turbo-16k模型"
    )
    return
