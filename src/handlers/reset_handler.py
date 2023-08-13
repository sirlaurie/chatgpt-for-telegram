#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from telegram import Update
from telegram.ext import ContextTypes

from constants.messages import (
    NOT_ALLOWD,
    NOT_PERMITED,
    NEW_CONVERSATION_MESSAGE,
)

from allowed import allowed
from utils import waring


async def reset_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    permitted, _, msg = allowed(context._user_id)
    if not permitted and msg == NOT_PERMITED:
        await waring(update, context, msg)
        return
    if not permitted and msg == NOT_ALLOWD:
        await update.message.reply_text(text=NOT_ALLOWD)
        return

    context.bot_data.update({"initial": True})

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = []
    await update.message.reply_text(text=NEW_CONVERSATION_MESSAGE)
    return
