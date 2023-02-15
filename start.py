#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


import logging
from typing import List

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
import openai
import httpx
from allowed import user_list

from allowed import user_list

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

bot_token = "6187271186:AAGB4Am0DBGoAvm-WIiOvxE9kHJ6Ic0dmFQ"
openai.api_key = "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"
openai_model = "text-davinci-003"
max_tokens = 2048
temperature = 0.3

conversations: List[dict[str, str | int]] = [{"user_id": user_id} for user_id in user_list]


def allowed(user_id):
    return True if user_id in user_list else False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if allowed(update.message.from_user.id):
        # user = update.effective_user
        await update.message.reply_text(text="Hello, 你先说")
    else:
        await update.message.reply_text(text=f"你没有权限访问此bot.请将你的id {update.message.chat.id} 发送给管理员, 等待批准")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 调用模型
    text = ""
    current_user_id = update.message.from_user.id
    if not allowed(current_user_id):
        await update.message.reply_text(text=f"你没有权限访问此bot.请将你的id {update.message.chat.id} 发送给管理员, 等待批准")
        return

    user_conversation = {}
    for conversation in conversations:
        if current_user_id == conversation["user_id"]:
            user_conversation = conversation
    conversation_id = user_conversation.get("conversation_id", None)
    parent_message_id = user_conversation.get("parent_message_id", None)

    data = {"message": update.message.text, "conversationId": conversation_id, "parentMessageId": parent_message_id}

    await update.get_bot().send_chat_action(update.message.chat.id, "typing", read_timeout=10)
    async with httpx.AsyncClient() as client:
        while not text:
            try:
                response = await client.post("http://git.lloring.com:5000/conversation",
                    json=data,
                    timeout=60)
                resp = response.json()
                user_conversation["conversation_id"] = resp["conversationId"]
                user_conversation["parent_message_id"] = resp["messageId"]
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
