import os
from collections.abc import Iterable

from telegram import Update
from telegram.ext import ContextTypes
from telegram._replykeyboardmarkup import ReplyKeyboardMarkup

from constants.messages import (
    NOT_PERMITED,
    YES_OR_NO_KEYBOARD,
    ASK_FOR_PERMITED,
    PROCESS_TIMEOUT,
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
)
from allowed import add


async def waring(update: Update, context: ContextTypes.DEFAULT_TYPE, msg) -> None:
    if update.message is not None:
        await update.message.reply_text(
            text=NOT_PERMITED.format(user_id=context._user_id), pool_timeout=3600.0
        )
        await apply_to_prove(update, context)
        return


async def apply_to_prove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    yes_or_no_keyboard = [YES_OR_NO_KEYBOARD]
    markup = ReplyKeyboardMarkup(
        yes_or_no_keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    message = await bot.sendMessage(
        chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
        text=ASK_FOR_PERMITED.format(
            name=update.message.chat.first_name, user_id=context._user_id
        ),
        reply_markup=markup,
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )

    update_from_admin = await bot.get_updates(
        timeout=3600, read_timeout=3600.0, pool_timeout=3600.0
    )

    if isinstance(update_from_admin, Iterable) and len(update_from_admin) == 0:
        await update.message.reply_text(text=PROCESS_TIMEOUT)
        await message.delete(read_timeout=60.0)
        return

    if isinstance(update_from_admin, Iterable) and len(update_from_admin) > 0:
        reply_obj = update_from_admin[0]
        permit_message = reply_obj.message

        if (
            hasattr(permit_message, "chat")
            and permit_message.chat.id == int(os.getenv("DEVELOPER_CHAT_ID", 0))
            and permit_message.text == "Approved"
        ):
            _ = add(context._user_id, update.message.chat.first_name, 1, 0)
            await update.message.reply_text(text=APPROVED_MESSAGE)
            await message.edit_reply_markup(reply_markup=None)
            return
        if (
            hasattr(permit_message, "chat")
            and permit_message.chat.id == int(os.getenv("DEVELOPER_CHAT_ID", 0))
            and permit_message.text == "Decline"
        ):
            _ = add(context._user_id, update.message.chat.first_name, 0, 0)
            await update.message.reply_text(text=DECLINE_MESSAGE)
            await message.edit_reply_markup(reply_markup=None)
            return


async def model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    await query.answer()
    context.bot_data.update({"model": query.data})

    await query.edit_message_text(text=f"OK! 已为您切换到 {query.data} 模型")
