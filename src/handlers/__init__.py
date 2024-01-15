#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


__all__ = (
    "handler",
)


import datetime
from typing import cast

from telegram import Update
from telegram.ext import ContextTypes
from openai.types.chat import ChatCompletionUserMessageParam
from src.helpers.permission import check_permission
from .message_handler import send_request


@check_permission
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    assert context.chat_data is not None

    context.bot_data.update({"initial": False})

    message_text = cast(str, update.message.text)

    message: ChatCompletionUserMessageParam = {"role": "user", "content": message_text}

    if context.bot_data.get("initial", True):
        messages = []
    else:
        last_message_date = context.chat_data.get("last_message_date", 0)
        last_message_datetime = datetime.datetime.fromtimestamp(
            last_message_date, tz=datetime.timezone.utc
        )
        time_difference = (
            datetime.datetime.now(tz=datetime.timezone.utc) - last_message_datetime
        )

        if time_difference > datetime.timedelta(hours=1.0):
            messages = []
        elif isinstance(context.chat_data, dict):
            messages = context.chat_data.get("messages", [])
        else:
            messages = []

    messages.append(message)
    context.chat_data.update({"last_message_date": update.message.date.timestamp()})
    context.chat_data["messages"] = messages

    await send_request(update=update, context=context, messages=messages)

    # first_name = getattr(update.message.from_user, "first_name", None)
