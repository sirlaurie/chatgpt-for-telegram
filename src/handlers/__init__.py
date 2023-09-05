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
    "document_start",
    "document_handler",
)

import os
from typing import cast
from telegram import Update
from telegram.ext import ContextTypes

from src.constants import (
    YES_OR_NO_KEYBOARD,
    TARGET_LANGUAGE_KEYBOARD,
    translator_prompt,
)
from src.helpers import check_permission, send_request
from src.utils import pick

from .reset_handler import reset_handler
from .switch_model_handler import switch_model_handler, switch_model_callback
from .translator_handler import translator_handler
from .admin_handler import admin_handler, query_list, manage_user, action, back, finish, CHOOSING, MANAGER
from .document_handler import document_start, document_handler
from .image_gen_handler import image_start, generate, cancel_gen_image, GENERATE


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

    if message_text in YES_OR_NO_KEYBOARD:
        return

    await update.get_bot().send_chat_action(
        update.message.chat.id, "typing", write_timeout=15.0, pool_timeout=10.0  # type: ignore
    )

    if message_text in TARGET_LANGUAGE_KEYBOARD:
        request = {
            "role": "user",
            "content": translator_prompt.format(target_lang=message_text),
        }
        context.bot_data.update({"initial": True})
    else:
        request = {
            "role": "user",
            "content": message_text
            if not context.bot_data.get("initial", True)
            else pick(message_text),
        }

    messages = (
        []
        if context.bot_data.get("initial", True)
        else (
            context.chat_data.get("messages", [])
            if isinstance(context.chat_data, dict)
            else []
        )
    )

    messages.append(request)

    if isinstance(context.chat_data, dict):
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
