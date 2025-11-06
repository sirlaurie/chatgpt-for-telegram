#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..constants.models import (
    # OpenAI models
    gpt_4o,
    gpt_4o_mini,
    gpt_4_turbo,
    # Gemini models
    gemini_2p5_flash,
    gemini_2p5_flash_thinking,
    gemini_exp_1206,
)
from ..helpers.permission import check_permission


async def switch_model_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    if not query:
        return

    _ = await query.answer()
    if not isinstance(context.chat_data, dict):
        return
    model = query.data
    if model not in [
        # OpenAI models
        gpt_4o,
        gpt_4o_mini,
        gpt_4_turbo,
        # Gemini models
        gemini_2p5_flash,
        gemini_2p5_flash_thinking,
        gemini_exp_1206,
    ]:
        return
    context.chat_data.update({"model": model})

    _ = await query.edit_message_text(text=f"OK! 已为您切换到 {model} 模型")


@check_permission
async def switch_model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    if not update.message or not isinstance(context.chat_data, dict):
        return

    # All models available to subscribed users
    inline_keyboard = [
        [
            InlineKeyboardButton("GPT-4o 🚀", callback_data=str(gpt_4o)),
            InlineKeyboardButton("GPT-4o Mini", callback_data=str(gpt_4o_mini)),
        ],
        [
            InlineKeyboardButton("GPT-4 Turbo", callback_data=str(gpt_4_turbo)),
        ],
        [
            InlineKeyboardButton("Gemini 2.5 Flash ⚡", callback_data=str(gemini_2p5_flash)),
            InlineKeyboardButton("Gemini 2.5 Thinking 🤔", callback_data=str(gemini_2p5_flash_thinking)),
        ],
        [
            InlineKeyboardButton("Gemini Exp 1206 🧪", callback_data=str(gemini_exp_1206)),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    _ = await update.message.reply_text(
        f"当前使用的模型是: {context.chat_data.get('model', None) or os.getenv('model')}. 切换你要使用的模型:",
        reply_markup=reply_markup,
    )
    return
