#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from telegram import Update
from telegram.ext import ContextTypes

from src.constants import NEW_CONVERSATION_MESSAGE

from src.helpers import check_permission


@check_permission
async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not update.effective_user:
        return

    context.bot_data.update({"initial": True})

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = []
    await update.message.reply_text(text=NEW_CONVERSATION_MESSAGE)
    return
