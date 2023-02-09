#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


from functools import wraps
import logging

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]


if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )


from telegram import ForceReply, Update

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import openai

from allowed import user_list

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and context.
openai.api_key = "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"
openai_model = "text-davinci-003"
max_tokens = 512
temperature = 0.6

bot_token = "2113990525:AAEQsbIVSHOylm1OFCUl0sHVBYw3IScP6kM"


def is_allowed(user_id):
    if user_id in user_list:
        return True
    else:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if is_allowed(update.message.from_user.id):
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}!",
            reply_markup=ForceReply(selective=True),
        )
    else:
        await update.message.reply_text(text=f"你没有权限访问此bot.请将你的id {update.message.chat.id} 发送给管理员, 等待批准")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 调用模型
    text = ""
    if is_allowed(update.message.from_user.id):
        await update.get_bot().send_chat_action(update.message.chat.id, "typing")

        while not text:
            try:
                response = openai.Completion.create(
                    prompt=update.message.text,
                    model=openai_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    )
                text = response.choices[0].text
                if text:
                    break
            except:
                continue
        await update.message.reply_text(text=text)
    else:
        await update.message.reply_text(text="你没有权限访问此bot.")


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
