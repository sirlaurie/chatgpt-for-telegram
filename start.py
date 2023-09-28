#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

# import re
import os
import json
import html
import logging

from telegram.constants import ParseMode

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackQueryHandler,
)

from src.constants import WELCOME_MESSAGE
from src.constants import (
    model_switch_command,
    linux_terminal_command,
    translator_command,
    rewrite_command,
    cyber_secrity_command,
    etymologists_command,
    genius_command,
    reset_command,
    admin_command,
    document_command,
    gen_image_command,
    APPROVE,
    DECLINE,
    UPGRADE,
    DOWNGRADE,
)
from src.helpers import check_permission
from src.handlers import (
    handler,
    reset_handler,
    admin_handler,
    query_list,
    manage_user,
    action,
    back,
    finish,
    CHOOSING,
    MANAGER,
    image_start,
    generate,
    cancel_gen_image,
    GENERATE,
    switch_model_handler,
    switch_model_callback,
    translator_handler,
    typing_src_lang,
    typing_tgt_lang,
    translate,
    stop,
    TYPING_SRC_LANG,
    TYPING_TGT_LANG,
    TRANSLATE,
    document_start,
    document_handler,
)
from src.helpers import approval_callback


# Enable logging
logging.basicConfig(
    filename="error.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
)

logger = logging.getLogger(__name__)


@check_permission
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        _ = context
        return
    await update.message.reply_text(text=WELCOME_MESSAGE)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"Update {update} caused error {context.error}")
    update_str = update.to_dict() if isinstance(update, Update) else str(update)

    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>ERROR: {context.error}</pre>\n\n"
    )

    await context.bot.send_message(
        chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
        text=message,
        parse_mode=ParseMode.HTML,
    )

    if hasattr(update, "effective_user") and update.effective_user:
        user_id = update.effective_user.id
        await context.bot.send_message(
            chat_id=user_id,
            text=f"<pre>ERROR: {context.error}</pre>\n\n",
            parse_mode=ParseMode.HTML,
        )


def main() -> None:
    bot_token: str = os.environ.get("bot_token", "")
    # """Start the bot."""
    # # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .connect_timeout(connect_timeout=5 * 60.0)
        .token(bot_token)
        .build()
    )
    application.add_handler(CommandHandler("start", start))

    admin_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(admin_command, admin_handler),
        ],
        states={
            CHOOSING: [
                CallbackQueryHandler(query_list, pattern="^(允许|等待|高级)名单$"),
            ],
            MANAGER: [
                CallbackQueryHandler(manage_user, pattern=r"\d+"),
                CallbackQueryHandler(
                    action, pattern=f"{APPROVE}|{DECLINE}|{UPGRADE}|{DOWNGRADE}"
                ),
                CallbackQueryHandler(back, pattern="^back$"),
                CallbackQueryHandler(finish, pattern="^finish$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(finish, pattern="^finish$"),
        ],
    )

    image_gen_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(gen_image_command, image_start),
        ],
        states={
            GENERATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate),
                CallbackQueryHandler(cancel_gen_image, pattern="^cancel_gen_image$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_gen_image, pattern="^cancel_gen_image$"),
        ],
    )

    translator_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(translator_command, translator_handler),
        ],
        states={
            TYPING_SRC_LANG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, typing_src_lang),
                MessageHandler(filters.Regex("^/Done$"), stop),
            ],
            TYPING_TGT_LANG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, typing_tgt_lang),
                MessageHandler(filters.Regex("^/Done$"), stop),
            ],
            TRANSLATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translate),
                MessageHandler(filters.Regex("^/Done$"), stop),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^/Done$"), stop),
        ],
    )
    application.add_handler(admin_conv_handler)
    application.add_handler(image_gen_conv_handler)
    application.add_handler(translator_conv_handler)
    application.add_handler(CommandHandler(reset_command, reset_handler))
    application.add_handler(CommandHandler(model_switch_command, switch_model_handler))
    application.add_handler(CommandHandler(document_command, document_start))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    application.add_handler(CallbackQueryHandler(switch_model_callback, pattern="^gpt"))
    application.add_handler(CallbackQueryHandler(approval_callback, pattern="^允许|拒绝$"))
    application.add_handler(CommandHandler(linux_terminal_command, handler))
    application.add_handler(CommandHandler(rewrite_command, handler))
    application.add_handler(CommandHandler(cyber_secrity_command, handler))
    application.add_handler(CommandHandler(etymologists_command, handler))
    application.add_handler(CommandHandler(genius_command, handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    # error handler
    application.add_error_handler(error_handler)  # type: ignore
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
