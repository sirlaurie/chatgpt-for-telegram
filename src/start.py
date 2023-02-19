#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import logging
import os

from telegram import __version__ as TG_VER

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

import httpx

from utils import waring, apply_to_prove
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
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

bot_token: str = os.environ.get("bot_token", "")
openai_apikey: str = os.environ.get("openai_apikey", "")
openai_model: str = os.environ.get("openai_model", "")
max_tokens: int = int(os.environ.get("max_tokens", "2048"))
temperature: float = float(os.environ.get("temperature", "0.6"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    permitted, msg = allowed(context._user_id)
    if permitted:
        # user = update.effective_user
        await update.message.reply_text(text="Hello, 你先说")
    else:
        await waring(update, context, msg)
        await apply_to_prove(update, context)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    permitted, msg = allowed(context._user_id)
    if not permitted:
        await waring(update, context, msg)
        return

    if (update.message.text in ["Approved", "Decline"]):
        return

    text = ""
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
        "message": update.message.text,
        "conversationId": conversation_id,
        "parentMessageId": parent_message_id,
    }

    # 调用模型
    async with httpx.AsyncClient() as client:
        while not text:
            try:
                await update.get_bot().send_chat_action(
                    update.message.chat.id, "typing", write_timeout=15.0
                )

                response = await client.post(
                    "http://git.lloring.com:5000/conversation", json=data, timeout=60
                )
                if (response.status_code == 503):
                    await update.message.reply_text(text="You exceeded your current quota, please check your plan and billing details.")
                    return
                if (response.status_code != 200):
                    await update.message.reply_text(text="Rate limit reached for default-text-davinci-003 in organization org-mogd9SPFFICvnfu2W1DUPk1e on requests per min.")
                    return
                resp = response.json()
                if isinstance(context.chat_data, dict):
                    context.chat_data["conversation_id"] = resp["conversationId"]
                    context.chat_data["parent_message_id"] = resp["messageId"]
                text = resp["response"]
                if text:
                    break
            except:
                continue
        await update.message.reply_text(text=text)


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
    # application.add_handler(CommandHandler(reset_handler, handle_reset)) # type: ignore
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
