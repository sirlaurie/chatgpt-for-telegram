import html
import json
import os
from typing import Dict, List, Union, cast
import httpx

from telegram.constants import ParseMode
from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from constants.messages import (
    NOT_ALLOWD,
    NOT_PERMITED,
    YES_OR_NO_KEYBOARD,
    INIT_REPLY_MESSAGE,
    TARGET_LANGUAGE_KEYBOARD,
)
from constants.prompts import (
    expand,
    genius,
    rewrite,
    translator,
    etymologists,
    cyber_secrity,
    linux_terminal,
)
from allowed import allowed
from utils import waring
from helpers import usage_from_messages


header = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.getenv("openai_apikey") or ""}',
}


def pick(act: str) -> str:
    """
    Function that matches the passed-in string to a known set of strings and returns the associated function.

    Args:
        act (str): The action string to match.

    Returns:
        str: default string.
    """
    match act:
        case "/linux_terminal":
            return linux_terminal
        case "/rewrite":
            return rewrite
        case "/cyber_secrity":
            return cyber_secrity
        case "/etymologists":
            return etymologists
        case "/genius":
            return genius
        case "/expand":
            return expand
        case _:
            return "who are you?"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    permitted, _, msg = allowed(context._user_id)
    if not permitted and msg == NOT_PERMITED:
        await waring(update, context, msg)
        return
    if not permitted and msg == NOT_ALLOWD:
        await update.message.reply_text(text=NOT_ALLOWD)
        return

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
        model = context.bot_data.get("model", "")
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
            "content": translator.format(target_lang=message_text),
        }
        # context.bot_data.update({"initial": True})
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
        "model": context.bot_data.get("model", None)
        or os.getenv("model", "gpt-3.5-turbo-16k"),
        "messages": messages,
        "stream": True,
    }

    first_name = getattr(update.message.from_user, 'first_name', None)
    print(f"************ from {first_name}: ************\n{data}")

    await send_request(data)
