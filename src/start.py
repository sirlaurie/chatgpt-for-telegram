#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

# import re
import os
import json
import html
import logging
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

from constants.messages import WELCOME_MESSAGE
from constants.handlers import (
    linux_terminal_handler,
    translator_handler,
    rewrite_handler,
    cyber_secrity_handler,
    etymologists_handler,
    genius_handler,
    reset_handler,
    )
from utils import waring
from allowed import allowed
from handlers import handle

# Enable logging
logging.basicConfig(
    filename="error.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
)

logger = logging.getLogger(__name__)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    permitted, msg = allowed(context._user_id)
    if permitted:
        # user = update.effective_user
        await update.message.reply_text(text=WELCOME_MESSAGE)
    else:
        await waring(update, context, msg)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"Update {update} caused error {context.error}")
    update_str = update.to_dict() if isinstance(update, Update) else str(update)

    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
    )

    await context.bot.send_message(
        chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
        text=message,
        parse_mode=ParseMode.HTML,
    )


# pattern = re.compile(r'^data:\s*(?P<json>{.+})\s*$', re.MULTILINE)
# content_pattern = re.compile(r'"content":\s*"(.*)"')


# def clear(response):
#     match = pattern.match(response)
#     if match:
#         json_str = match.group('json')
#         data = json.loads(json_str)
#         choices = data.get('choices', [])
#         if choices:
#             delta = choices[0].get('delta', {})
#             content = delta.get('content', '')
#             clear_content = re.sub(r'\\n', '', content)
#             return clear_content
#     return ""


def main() -> None:
    bot_token: str = os.environ.get("bot_token", "")
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler(translator_handler, handle))  # type: ignore
    application.add_handler(CommandHandler(linux_terminal_handler, handle))  # type: ignore
    application.add_handler(CommandHandler(rewrite_handler, handle))  # type: ignore
    application.add_handler(CommandHandler(cyber_secrity_handler, handle))  # type: ignore
    application.add_handler(CommandHandler(etymologists_handler, handle))  # type: ignore
    application.add_handler(CommandHandler(genius_handler, handle))  # type: ignore
    application.add_handler(CommandHandler(reset_handler, handle))  # type: ignore
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    # error handler
    application.add_error_handler(error_handler)  # type: ignore
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
