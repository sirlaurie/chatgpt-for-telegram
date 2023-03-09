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
from allowed import add, not_allowd, quota_exceeded


async def waring(update: Update, context: ContextTypes.DEFAULT_TYPE, msg) -> None:
    if msg == not_allowd:
        await update.message.reply_text(
            text=NOT_PERMITED.format(user_id=context._user_id),
            pool_timeout=3600.0
        )
        await apply_to_prove(update, context)
        return

    if msg == quota_exceeded:
        await update.message.reply_text(text=msg)
        return


async def apply_to_prove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    yes_or_no_keyboard = [YES_OR_NO_KEYBOARD]
    markup = ReplyKeyboardMarkup(
        yes_or_no_keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await bot.sendMessage(
        chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
        text=ASK_FOR_PERMITED.format(name=update.message.chat.first_name, user_id=context._user_id) ,
        reply_markup=markup,
        write_timeout=3600.0,
        pool_timeout=3600.0
    )

    updater = await bot.get_updates(
        timeout=3600.0,
        read_timeout=3600.0,
        pool_timeout=3600.0
    )

    if not isinstance(updater, Iterable):
        await update.message.reply_text(text=PROCESS_TIMEOUT)
        return

    if isinstance(updater, Iterable) and len(updater) > 0:
        reply_obj = updater[0]
        permit_message = reply_obj.message
        if permit_message.chat.id == int(os.getenv("DEVELOPER_CHAT_ID", 0)) and permit_message.text == "Approved":
            _ = add(context._user_id, update.message.chat.first_name)
            await update.message.reply_text(text=APPROVED_MESSAGE)
            return
        if permit_message.chat.id == int(os.getenv("DEVELOPER_CHAT_ID", 0)) and permit_message.text == "Decline":
            await update.message.reply_text(text=DECLINE_MESSAGE)
            return
