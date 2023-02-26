#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import logging
import os

from telegram import __version__ as TG_VER
from telegram.constants import ParseMode

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the {TG_VER} version of this example, visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown

import asyncio
import httpx

from utils import waring
from allowed import allowed
from handlers import (
    handle,
    linux_terminal_handler,
    translator_handler,
    rewrite_handler,
    code_helper_handler,
    cyber_secrity_handler,
    etymologists_handler,
    genius_handler,
    reset_handler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

bot_token: str = os.environ.get("bot_token", "")
# openai_apikey: str = os.environ.get("openai_apikey", "")
# openai_model: str = os.environ.get("openai_model", "")
# max_tokens: int = int(os.environ.get("max_tokens", "2048"))
# temperature: float = float(os.environ.get("temperature", "0.6"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    permitted, msg = allowed(context._user_id)
    if permitted:
        # user = update.effective_user
        await update.message.reply_text(text="Hello, 你先说")
    else:
        await waring(update, context, msg)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    permitted, msg = allowed(context._user_id)
    if not permitted:
        await waring(update, context, msg)
        return

    if update.message.text in ["Approved", "Decline"]:
        return

    message = await update.message.reply_text(text="please wait...")
    await update.get_bot().send_chat_action(
        update.message.chat.id, "typing", write_timeout=15.0
    )

    async def send_request(data):
        async with httpx.AsyncClient(timeout=None) as client:
            responses = await client.post(
                url=os.getenv("api_endpoint") or "",
                json=data,
                timeout=None,
            )
            asyncio.create_task(update_message(responses))

    async def update_message(responses):
        if responses.status_code == 200:
            data = responses.json()
            if isinstance(context.chat_data, dict):
                context.chat_data["conversation_id"] = data["conversationId"]
                context.chat_data["parent_message_id"] = data["parentMessageId"]

            await message.edit_text(
                text=escape_markdown(data["text"]),
                parse_mode=ParseMode.MARKDOWN,
                write_timeout=None,
            )
        else:
            await message.edit_text(text="sorry, 服务器开小差了.", parse_mode=ParseMode.HTML)

    conversation_id = (
        context.chat_data.get("conversation_id", None)
        if isinstance(context.chat_data, dict)
        else None
    )

    parent_message_id = (
        context.chat_data.get("parent_message_id", None)
        if isinstance(context.chat_data, dict)
        else None
    )

    data = {
        "prompt": update.message.text,
        "conversationId": conversation_id,
        "parentMessageId": parent_message_id,
    }

    print(data)

    await send_request(data)


def main() -> None:
    """Start the bot."""

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler(translator_handler, handle))  # type: ignore
    # handle_linux_terminal = handler(linux_terminal_handler)
    application.add_handler(CommandHandler(linux_terminal_handler, handle))  # type: ignore
    # handle_rewrite = handler(rewrite_handler)
    application.add_handler(CommandHandler(rewrite_handler, handle))  # type: ignore
    # handle_code_helper = handler(code_helper_handler)
    application.add_handler(CommandHandler(code_helper_handler, handle))  # type: ignore
    # handle_cyber_secrity = handler(cyber_secrity_handler)
    application.add_handler(CommandHandler(cyber_secrity_handler, handle))  # type: ignore
    # handle_etymologists = handler(etymologists_handler)
    application.add_handler(CommandHandler(etymologists_handler, handle))  # type: ignore
    # handle_genius = handler(genius_handler)
    application.add_handler(CommandHandler(genius_handler, handle))  # type: ignore
    # handle_advanced_frontend = handler(advanced_frontend_handler)
    # application.add_handler(CommandHandler(advanced_frontend_handler, handle_advanced_frontend)) # type: ignore
    # handle_reset = handler(reset_handler)
    application.add_handler(CommandHandler(reset_handler, handle))  # type: ignore
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
