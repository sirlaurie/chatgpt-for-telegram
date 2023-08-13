import os
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


header = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.getenv("openai_apikey") or ""}',
}


def pick(act: str):
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


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    permitted, _, msg = allowed(context._user_id)
    if not permitted and msg == NOT_PERMITED:
        await waring(update, context, msg)
        return
    if not permitted and msg == NOT_ALLOWD:
        await update.message.reply_text(text=NOT_ALLOWD)
        return

    context.bot_data.update({"initial": False})

    message_text = update.message.text

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
        update.message.chat.id, "typing", write_timeout=15.0, pool_timeout=10.0
    )

    async def send_request(data: dict):
        async with httpx.AsyncClient(timeout=None) as client:
            message = await update.message.reply_text(
                text=INIT_REPLY_MESSAGE, pool_timeout=15.0
            )
            response = await client.post(
                url=os.getenv("api_endpoint") or os.getenv("default_api_endpoint", ""),
                headers=header,
                json=data,
            )
            resp = response.json()
            message_from_gpt = resp.get("choices", [{}])[0].get("message", {})
            content = message_from_gpt.get("content", "")
            if content:
                await message.edit_text(
                    text=escape_markdown(text=content, version=2),
                    parse_mode=ParseMode.MARKDOWN_V2,
                )

                await update_message(message_from_gpt)
            else:
                await message.edit_text(
                    text=escape_markdown(
                        text="ERROR: " + resp.get("error", {}).get("message", {}),
                        version=2,
                    ),
                    parse_mode=ParseMode.MARKDOWN_V2,
                )

    async def update_message(message):
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
        context.bot_data.update({"initial": True})
    else:
        request = {
            "role": "user",
            "content": message_text if not context.bot_data.get("initial") else pick(message_text),
        }

    messages = (
        []
        if context.bot_data.get("initial")
        else (
            context.chat_data.get("messages", [])
            if isinstance(context.chat_data, dict)
            else []
        )
    )

    messages.append(request)

    data = {
        "model": context.bot_data.get("model", None)
        or os.getenv("model", "gpt-3.5-turbo-16k"),
        "messages": messages,
        "stream": False,
    }
    await send_request(data)
