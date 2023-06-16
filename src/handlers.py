import os
import httpx

from telegram.constants import ParseMode
from telegram import Update
from telegram.ext import ContextTypes
from telegram._replykeyboardmarkup import ReplyKeyboardMarkup

from telegram.helpers import escape_markdown

# from telegram import MessageEntity

from constants.messages import (
    NOT_ALLOWD,
    NOT_PERMITED,
    YES_OR_NO_KEYBOARD,
    INIT_REPLY_MESSAGE,
    NEW_CONVERSATION_MESSAGE,
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
        case "/translator":
            return translator
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
    permitted, msg = allowed(context._user_id)
    if not permitted and msg == NOT_PERMITED:
        await waring(update, context, msg)
        return
    if not permitted and msg == NOT_ALLOWD:
        await update.message.reply_text(text=NOT_ALLOWD)
        return

    initial = False

    message_text = update.message.text

    if message_text in [
        "/linux_terminal",
        "/translator",
        "/rewrite",
        "/cyber_secrity",
        "/etymologists",
        "/genius",
        "/expand",
        "/advanced_frontend",
        "/reset",
    ]:
        initial = True

    if message_text in YES_OR_NO_KEYBOARD:
        return

    # if isinstance(context.chat_data, dict):
    #     initial = context.chat_data.get("initial", False)

    if message_text == "/reset":
        if isinstance(context.chat_data, dict):
            context.chat_data["messages"] = []
        await update.message.reply_text(text=NEW_CONVERSATION_MESSAGE)
        return

    if message_text == "/translator":
        target_language_keyboard = [TARGET_LANGUAGE_KEYBOARD]
        markup = ReplyKeyboardMarkup(
            target_language_keyboard, resize_keyboard=True, one_time_keyboard=True
        )
        await update.message.reply_text(
            text="首先,请选择你要翻译为哪种语言?",
            reply_markup=markup,
            write_timeout=3600.0,
            pool_timeout=3600.0,
        )
        # if isinstance(context.chat_data, dict):
        #     context.chat_data["initial"] = True
        return

    await update.get_bot().send_chat_action(
        update.message.chat.id, "typing", write_timeout=15.0, pool_timeout=10.0
    )

    async def send_request(data):
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
                    text=escape_markdown(text="openai开小差了, 请继续提问", version=2),
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
        initial = True
    else:
        request = {
            "role": "user",
            "content": message_text if not initial else pick(message_text),
        }

    messages = (
        []
        if initial
        else (
            context.chat_data.get("messages", [])
            if isinstance(context.chat_data, dict)
            else []
        )
    )

    messages.append(request)
    data = {
        "model": os.getenv("model", "gpt-3.5-turbo"),
        "messages": messages,
        "stream": False,
    }
    await send_request(data)

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = messages
        print("****************************************************************")
        print(context.chat_data["messages"])
        print("----------------------------------------------------------------")
