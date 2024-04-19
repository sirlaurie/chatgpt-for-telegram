#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


from telegram import Update
from telegram.ext import ContextTypes

from ..constants.messages import NEW_CONVERSATION_MESSAGE

# from src.constants.commands import (
#     reset_command,
#     admin_command,
#     my_prompts_command,
#     my_assistants_command,
#     create_new_prompt_command,
#     create_new_assistant_command,
# )
from ..helpers.permission import check_permission


@check_permission
async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not update.effective_user:
        return

    context.bot_data.update({"initial": True})

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = []
        context.chat_data["history"] = []
    await update.message.reply_text(text=NEW_CONVERSATION_MESSAGE)
    return
