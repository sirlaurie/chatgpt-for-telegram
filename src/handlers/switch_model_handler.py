#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.constants import (
    gpt_3p5_turbo,
    gpt_3p5_turbo_16k,
    gpt_3p5_turbo_0613,
    gpt_3p5_turbo_16k_0613,
    gpt_4_0314,
    gpt_4_0613,
    gpt_4_32k_0314,
    gpt_4_32k_0613,
)
from src.utils import is_allowed
from src.helpers import check_permission


async def switch_model_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    if not isinstance(context.chat_data, dict):
        return
    model = query.data
    if model not in [
        gpt_3p5_turbo,
        gpt_3p5_turbo_0613,
        gpt_3p5_turbo_16k,
        gpt_3p5_turbo_16k_0613,
        gpt_4_0314,
        gpt_4_0613,
        gpt_4_32k_0314,
        gpt_4_32k_0613,
    ]:
        return
    context.chat_data.update({"model": model})

    await query.edit_message_text(text=f"OK! 已为您切换到 {model} 模型")


@check_permission
async def switch_model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    _, premium, *_ = is_allowed(update.effective_user.id)

    if not update.message or not isinstance(context.chat_data, dict):
        return

    if premium:
        inline_keybord = [
            [
                InlineKeyboardButton("gpt-3.5-turbo", callback_data=str(gpt_3p5_turbo)),
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
                InlineKeyboardButton(
                    "gpt-4-32k-0314", callback_data=str(gpt_4_32k_0314)
                ),
            ],
            [
                InlineKeyboardButton("gpt-4-0613", callback_data=str(gpt_4_0613)),
                InlineKeyboardButton(
                    "gpt-4-32k-0613", callback_data=str(gpt_4_32k_0613)
                ),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keybord)

        await update.message.reply_text(
            f"当前使用的模型是: {context.chat_data.get('model', None) or os.getenv('model')}. 切换你要使用的模型:",
            reply_markup=reply_markup,
        )
        return

    await update.message.reply_text(
        "Sorry, 由于GPT-4等高级模型的费用较高(GPT-3.5的20倍), 默认用户当前只能使用GPT-3.5-turbo-16k模型"
    )
    return
