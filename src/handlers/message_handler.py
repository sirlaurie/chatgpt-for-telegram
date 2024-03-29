#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


import html
import os
from io import BytesIO
from typing import Dict, List
import httpx

from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from fitz import fitz
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.constants.messages import INIT_REPLY_MESSAGE
from src.constants.constant import SUPPPORTED_FILE


async_client = AsyncOpenAI()


async def send_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    messages: List[ChatCompletionMessageParam],
) -> None:
    """
    Sends the request to the server and processes the response.

    Args:
        messages: Data to be sent with the request.

    Returns:
        None
    """
    # print(f"update message: {update.message}")
    assert context.chat_data is not None
    # if update.message is None and update.callback_query is None:
    #     return
    if update.message is not None:
        message = update.message
    elif (
        update.callback_query is not None and update.callback_query.message is not None
    ):
        message = update.callback_query.message
    else:
        return
    msg = await message.reply_text(text=INIT_REPLY_MESSAGE, pool_timeout=15.0)
    full_content = ""
    index = 0
    model = context.chat_data.get("model", os.getenv("model"))

    stream = await async_client.chat.completions.create(
        messages=messages, model=model, stream=True
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            full_content += chunk.choices[0].delta.content
        if index and index % 9 == 0:
            await msg.edit_text(
                text=escape_markdown(text=full_content, version=2),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        index += 1

    to_sent_message = (
        f"{html.escape(full_content)}\n\n"
        f"----------------------------------------\n"
        f"<i>🎨 Generate by model: {model}.</i>\n"
    )
    await msg.edit_text(
        text=to_sent_message,
        parse_mode=ParseMode.HTML,
    )
    await update_message(
        context, message={"role": "assistant", "content": full_content}
    )


async def update_message(
    context: ContextTypes.DEFAULT_TYPE, message: Dict[str, str]
) -> None:
    """
    Updates the conversation context with the new message.

    Args:
        message (Dict[str, str]): The message to be appended.

    Returns:
        None
    """
    old_messages = (
        context.chat_data.get("messages", [])
        if isinstance(context.chat_data, dict)
        else []
    )
    old_messages.append(message)

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = old_messages


async def read_document(update: Update, file_path: str) -> str:
    assert update.message is not None

    try:
        file_type = file_path.split(".")[-1]
    except Exception as e:
        print(e)
        await update.message.reply_text(
            text="未能获取到文件扩展名, 请上传一个具有确定扩展名的文件",
            pool_timeout=3600.0,
        )
        return ""
    if file_type not in SUPPPORTED_FILE:
        await update.message.reply_text(
            text="目前支持的文件类型包括\n\n1.纯文本文件, 如txt, Markdown, source code文件.\n2.专有格式的文本文件, 如PDF, XPS, ePub, Mobi",
            pool_timeout=3600.0,
        )
        return ""
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.get(url=file_path)
        data = BytesIO(initial_bytes=response.content)
    file = fitz.open(stream=data, filetype=file_type)  # type: ignore
    text_of_file = ""
    for page in file:
        text_of_file += page.get_text()
    return text_of_file
