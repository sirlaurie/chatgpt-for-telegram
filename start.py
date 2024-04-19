#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

# import re
import os
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

from src.helpers.permission import check_permission
from src.helpers.unauthorize import approval_callback
from src.constants.messages import WELCOME_MESSAGE
from src.constants.commands import (
    reset_command,
    switch_model_command,
    admin_command,
    my_prompts_command,
    create_new_prompt_command,
    document_command,
    translator_command,
    gen_image_command,
)
from src.constants.constant import (
    APPROVE,
    DECLINE,
    UPGRADE,
    DOWNGRADE,
    WAITING,
    PERMITTED,
    PREMIUM,
)
from src.handlers import handler
from src.handlers.admin_handler import admin_handler
from src.handlers.reset_handler import reset_handler
from src.handlers.switch_model_handler import (
    switch_model_handler,
    switch_model_callback,
)
from src.handlers.my_prompts_handler import my_prompts_handler
from src.handlers.new_prompt_handler import create_new_prompt_handler
from src.handlers.document_handler import document_handler, document_start
from src.handlers.translator_handler import (
    TYPING_SRC_LANG,
    TYPING_TGT_LANG,
    TRANSLATE,
    typing_src_lang,
    typing_tgt_lang,
    translator_handler,
    translate,
    stop,
)
from src.handlers.image_gen_handler import (
    GENERATE,
    generate,
    image_start,
    cancel_gen_image,
)
from src.handlers.admin_handler import (
    CHOOSING,
    MANAGER,
    back,
    finish,
    query_list,
    manage_user,
    action,
)
from src.handlers.my_prompts_handler import (
    prompt_callback_handler,
    view_prompts,
)
from src.handlers.new_prompt_handler import (
    prompt_name_handler,
    prompt_content_handler,
    share_handler,
    prompt_name,
    prompt_content,
    share,
)

# Enable logging
logging.basicConfig(
    filename="error.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)


@check_permission
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        _ = context
        return
    await update.message.reply_text(text=WELCOME_MESSAGE)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # logger.warning(f"Update {update} caused error {context.error}")
    # update_str = update.to_dict() if isinstance(update, Update) else str(update)

    # message = (
    #     f"An exception was raised while handling an update\n"
    #     f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
    #     "</pre>\n\n"
    #     f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
    #     f"<pre>ERROR: {context.error}</pre>\n\n"
    # )

    # await context.bot.send_message(
    #     chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
    #     text=message,
    #     parse_mode=ParseMode.HTML,
    # )

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
    application.add_handler(CommandHandler(reset_command, reset_handler))
    application.add_handler(CommandHandler(switch_model_command, switch_model_handler))
    application.add_handler(
        CallbackQueryHandler(
            switch_model_callback, pattern="^gpt|^gemini|^llama|^mixtral"
        )
    )
    application.add_handler(CommandHandler(my_prompts_command, my_prompts_handler))
    application.add_handler(
        CallbackQueryHandler(
            prompt_callback_handler, pattern=f"{view_prompts}|^prompt (17)\\d{8}$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            approval_callback, pattern=f"^F ({APPROVE}|{DECLINE}) \\d+$"
        )
    )
    new_prompt_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(create_new_prompt_command, create_new_prompt_handler),
        ],
        states={
            prompt_name: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_name_handler),
            ],
            prompt_content: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_content_handler),
            ],
            share: [
                CallbackQueryHandler(share_handler, pattern="yes|no"),
            ],
        },
        fallbacks=[],
    )
    admin_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(admin_command, admin_handler),
        ],
        states={
            CHOOSING: [
                CallbackQueryHandler(
                    query_list, pattern=f"{WAITING}|{PERMITTED}|{PREMIUM}"
                ),
            ],
            MANAGER: [
                CallbackQueryHandler(manage_user, pattern=r"\d+"),
                CallbackQueryHandler(
                    action, pattern=f"{APPROVE}|{DECLINE}|{UPGRADE}|{DOWNGRADE} \\d+$"
                ),
                CallbackQueryHandler(back, pattern="^back$"),
                CallbackQueryHandler(finish, pattern="^finish$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(finish, pattern="^finish$"),
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
    application.add_handler(admin_conv_handler)
    application.add_handler(new_prompt_conv_handler)
    application.add_handler(translator_conv_handler)
    application.add_handler(image_gen_conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    application.add_handler(CommandHandler(document_command, document_start))
    # application.add_handler(MessageHandler(filters.PHOTO, vision_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    # error handler
    # application.add_error_handler(error_handler)  # type: ignore
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
