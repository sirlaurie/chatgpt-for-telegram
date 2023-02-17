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

from allowed import user_list
from handlers import (
    handler,
    linux_terminal_handler,
    translator_handler,
    rewrite_handler,
    code_helper_handler,
    cyber_secrity_handler,
    etymologists_handler,
    genius_handler,
    advanced_frontend_handler,
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


def allowed(user_id):
    return True if user_id in user_list else False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if allowed(update.message.from_user.id):
        # user = update.effective_user
        await update.message.reply_text(text="Hello, 你先说")
    else:
        await update.message.reply_text(
            text=f"你没有权限访问此bot.请将你的id {context._user_id} 发送给管理员, 等待批准"
        )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    update.message.chat.id, "typing", write_timeout=20000
                )

                response = await client.post(
                    "http://git.lloring.com:5000/conversation", json=data, timeout=60
                )
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
    application.add_handler(CommandHandler(translator_handler, handler(translator_handler))) # type: ignore
    application.add_handler(CommandHandler(linux_terminal_handler, handler(linux_terminal_handler))) # type: ignore
    application.add_handler(CommandHandler(rewrite_handler, handler(rewrite_handler))) # type: ignore
    application.add_handler(CommandHandler(code_helper_handler, handler(code_helper_handler))) # type: ignore
    application.add_handler(CommandHandler(cyber_secrity_handler, handler(cyber_secrity_handler))) # type: ignore
    application.add_handler(CommandHandler(etymologists_handler, handler(etymologists_handler))) # type: ignore
    application.add_handler(CommandHandler(genius_handler, handler(genius_handler))) # type: ignore
    application.add_handler(CommandHandler(advanced_frontend_handler, handler(advanced_frontend_handler))) # type: ignore
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
