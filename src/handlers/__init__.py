#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


__all__ = (
    "handler",
    "reset_handler",
    "admin_handler",
    "query_list",
    "manage_user",
    "action",
    "back",
    "finish",
    "CHOOSING",
    "MANAGER",
    "image_start",
    "generate",
    "cancel_gen_image",
    "GENERATE",
    "switch_model_handler",
    "switch_model_callback",
    "translator_handler",
    "typing_src_lang",
    "typing_tgt_lang",
    "translate",
    "stop",
    "TYPING_SRC_LANG",
    "TYPING_TGT_LANG",
    "TRANSLATE",
    "document_start",
    "document_handler",
)

import os
import datetime
from typing import cast
from telegram import Update
from telegram.ext import ContextTypes

from src.helpers import check_permission, send_request
from src.utils import pick
from src.constants import instructions
from .reset_handler import reset_handler
from .switch_model_handler import switch_model_handler, switch_model_callback
from .translator_handler import translator_handler, typing_src_lang, typing_tgt_lang, translate, stop, TYPING_SRC_LANG, TYPING_TGT_LANG, TRANSLATE
from .admin_handler import (
    admin_handler,
    query_list,
    manage_user,
    action,
    back,
    finish,
    CHOOSING,
    MANAGER,
)
from .document_handler import document_start, document_handler
from .image_gen_handler import image_start, generate, cancel_gen_image, GENERATE


custom_instrucions = {
    "role": "system",
    "content": instructions
}


@check_permission
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    assert context.chat_data is not None

    context.bot_data.update({"initial": False})

    message_text = cast(str, update.message.text)

    if message_text in [
        "/linux_terminal",
        "/rewrite",
        "/cyber_secrity",
        "/etymologists",
        "/genius",
        "/expand",
        "/advanced_frontend",
    ]:
        context.bot_data.update({"initial": True})

    await update.get_bot().send_chat_action(
        update.message.chat.id, "typing", write_timeout=15.0, pool_timeout=10.0  # type: ignore
    )


    request = {
        "role": "user",
        "content": message_text
        if not context.bot_data.get("initial", True)
        else pick(message_text),
    }

    if context.bot_data.get("initial", True):
        messages = []
    else:
        last_message_date = context.chat_data.get("last_message_date", 0)
        last_message_datetime = datetime.datetime.fromtimestamp(last_message_date, tz=datetime.timezone.utc)
        time_difference = datetime.datetime.now(tz=datetime.timezone.utc)- last_message_datetime

        if time_difference > datetime.timedelta(hours=1.0):
            messages = []
        elif isinstance(context.chat_data, dict):
            messages = context.chat_data.get("messages", [])
        else:
            messages = []

    if len(messages) == 0:
        messages.append(custom_instrucions)
    messages.append(request)
    context.chat_data.update({"last_message_date": update.message.date.timestamp()})
    context.chat_data["messages"] = messages

    data = {
        "model": context.chat_data.get("model", None)
        or os.getenv("model", "gpt-3.5-turbo-16k"),
        "messages": messages,
        "stream": True,
    }

    first_name = getattr(update.message.from_user, "first_name", None)
    print(f"************ from {first_name}: ************\n{data}")

    await send_request(update=update, context=context, data=data)
