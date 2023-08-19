#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


__all__ = (
  "handler",
  "reset_handler",
  "switch_model_handler",
  "switch_model_callback",
  "translator_handler"
  )

import html
import json
import os
from typing import Dict, List, Union, cast
import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.constants import YES_OR_NO_KEYBOARD, INIT_REPLY_MESSAGE, TARGET_LANGUAGE_KEYBOARD, translator_prompt
from src.helpers import check_permission
from src.utils import pick, usage_from_messages

from .reset_handler import reset_handler
from .switch_model_handler import switch_model_handler, switch_model_callback
from .translator_handler import translator_handler


header = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.getenv("openai_apikey") or ""}',
}

@check_permission
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    context.bot_data.update({"initial": False})

    message_text = cast(str, update.message.text)
    print(f"got a message: {message_text}")

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
        print(message_text)
        return

    await update.get_bot().send_chat_action(
        update.message.chat.id, "typing", write_timeout=15.0, pool_timeout=10.0  # type: ignore
    )

    async def send_request(data: Dict[str, Union[str, List[Dict[str, str]]]]) -> None:
        """
        Sends the request to the server and processes the response.

        Args:
            data (Dict[str, Union[str, List[Dict[str, str]]]]): Data to be sent with the request.

        Returns:
            None
        """
        client = httpx.AsyncClient(timeout=None)
        assert update.message is not None
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
                f'<i>🎨 Generate by model: {model}.</i>\n'
                f'<i>💸 Usage: {num_token} tokens, cost: ${price}</i>'
                )
            await message.edit_text(
                text=to_sent_message,
                parse_mode=ParseMode.HTML,
            )
            await update_message({"role": "assistant", "content": full_content})

    async def update_message(message: Dict[str, str]) -> None:
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

    first_name = getattr(update.message.from_user, 'first_name', None)
    print(f"************ from {first_name}: ************\n{data}")

    await send_request(data)
