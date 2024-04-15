#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.constants.models import (
    gpt_3p5_turbo,
    gpt_3p5_turbo_1106,
    gpt_4,
    gpt_4_turbo,
    gemini_pro,
    gemini_1p5_pro,
)
from src.utils import is_allowed
from src.helpers.permission import check_permission


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
        gpt_3p5_turbo_1106,
        gpt_4,
        gpt_4_turbo,
        gemini_pro,
        gemini_1p5_pro,
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

    inline_keybord = [
        [
            InlineKeyboardButton("gpt-3.5-turbo", callback_data=str(gpt_3p5_turbo)),
            InlineKeyboardButton(
                "gpt-3.5-turbo-1106", callback_data=str(gpt_3p5_turbo_1106)
            ),
        ],
        [
            InlineKeyboardButton("gemini pro", callback_data=str(gemini_pro)),
            InlineKeyboardButton("gemini 1.5 pro", callback_data=str(gemini_1p5_pro)),
        ],
    ]

    if premium:
        premium_inline_keybord = [
            [
                InlineKeyboardButton("gpt-4", callback_data=str(gpt_4)),
                InlineKeyboardButton("gpt-4-turbo", callback_data=str(gpt_4_turbo)),
            ],
        ]
        inline_keybord.extend(premium_inline_keybord)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keybord)

        await update.message.reply_text(
            f"当前使用的模型是: {context.chat_data.get('model', None) or os.getenv('model')}. 切换你要使用的模型:",
            reply_markup=reply_markup,
        )
        return

    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keybord)

    await update.message.reply_text(
        text="Sorry, 由于GPT-4系列模型的费用较高(约是GPT-3.5的20倍), 默认用户当前只能使用GPT-3.5系列模型. 如果你愿意资助, 可以开放GPT-4模型.",
        reply_markup=reply_markup
    )
    return
