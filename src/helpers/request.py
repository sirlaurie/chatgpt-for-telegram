#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


import html
import json
import os
from io import BytesIO
from typing import Dict, List, Union
import httpx
from fitz import fitz
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.constants import INIT_REPLY_MESSAGE, SUPPPORTED_FILE
from src.utils import usage_from_messages


header = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.getenv("openai_apikey") or ""}',
}


async def send_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    data: Dict[str, Union[str, int, List[Dict[str, str]]]],
) -> None:
    """
    Sends the request to the server and processes the response.

    Args:
        data (Dict[str, Union[str, List[Dict[str, str]]]]): Data to be sent with the request.

    Returns:
        None
    """
    assert update.message is not None
    assert context.chat_data is not None

    client = httpx.AsyncClient(timeout=None)
    message = await update.message.reply_text(
        text=INIT_REPLY_MESSAGE, pool_timeout=15.0
    )
    full_content = ""
    index = 0
    model = context.chat_data.get("model", "")
    data.update({"temperature": 0})
    async with client.stream(
        method="POST",
        url=os.getenv("api_endpoint") or os.getenv("default_api_endpoint", ""),
        headers=header,
        json=data,
    ) as response:
        if not response.is_success:
            resp = await response.aread()
            content = resp.decode()
            content = json.loads(content)
            await message.edit_text(
                text=escape_markdown(
                    text="ERROR: " + content.get("error", {}).get("message", {}),
                    version=2,
                ),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            await response.aclose()
            return
        async for chunk in response.aiter_lines():
            index += 1
            string = chunk.strip("data: ")
            if not string:
                continue
            if "[DONE]" in chunk:
                await response.aclose()
                continue
            chunk = json.loads(string)
            model = chunk.get("model", os.getenv("model"))
            is_stop = chunk.get("choices", [{}])[0].get("finish_reason", None)
            if is_stop:
                break

            chunk_message = (
                chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            )
            if not chunk_message:
                continue
            full_content += chunk_message

            if index and index % 13 == 0:
                await message.edit_text(
                    text=escape_markdown(text=full_content, version=2),
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
        num_token, price = usage_from_messages(full_content, model=model)
        to_sent_message = (
            f"{html.escape(full_content)}\n\n"
            f"----------------------------------------\n"
            f"<i>🎨 Generate by model: {model}.</i>\n"
            f"<i>💸 Usage: {num_token} tokens, cost: ${price}</i>"
        )
        await message.edit_text(
            text=to_sent_message,
            parse_mode=ParseMode.HTML,
        )
        await update_message(
            context, message={"role": "assistant", "content": full_content}
        )
    await client.aclose()


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
            text="未能获取到文件扩展名, 请上传一个具有确定扩展名的文件", pool_timeout=3600.0
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
