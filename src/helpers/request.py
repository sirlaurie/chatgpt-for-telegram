#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


import html
import json
import os
from typing import Dict, List, Union
import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.constants import INIT_REPLY_MESSAGE
from src.utils import usage_from_messages


header = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.getenv("openai_apikey") or ""}',
}


async def send_request(update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Union[str, List[Dict[str, str]]]]) -> None:
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
            full_content += chunk_message

            if index and index % 7 == 0:
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
        await update_message(context, message={"role": "assistant", "content": full_content})


async def update_message(context: ContextTypes.DEFAULT_TYPE, message: Dict[str, str]) -> None:
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
