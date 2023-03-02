import os
from collections.abc import Iterable
from allowed import add, not_allowd, quota_exceeded

from telegram import Update
from telegram.ext import ContextTypes
from telegram._replykeyboardmarkup import ReplyKeyboardMarkup


async def waring(update: Update, context: ContextTypes.DEFAULT_TYPE, msg) -> None:
    if msg == not_allowd:
        await update.message.reply_text(
            text=f"你没有权限访问此bot.请将你的id {context._user_id} 发送给管理员, 等待批准. 最长耗时约1小时🤔"
        )
        await apply_to_prove(update, context)
        return

    if msg == quota_exceeded:
        await update.message.reply_text(text=msg)
        return


async def apply_to_prove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    yes_or_no_keyboard = [["Approved", "Decline"]]
    markup = ReplyKeyboardMarkup(
        yes_or_no_keyboard, resize_keyboard=True, one_time_keyboard=False
    )
    await bot.sendMessage(
        chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
        text=f"User {update.message.chat.first_name}, id: {context._user_id} want to chat with me, would you like to allow it?",
        reply_markup=markup,
        write_timeout=30.0,
    )

    updater = await bot.get_updates(
        timeout=3600.0, pool_timeout=3600.0
    )

    if not isinstance(updater, Iterable):
        await update.message.reply_text(text=f"到目前为止, 管理员尚未处理你的请求.🤯")
        return

    if isinstance(updater, Iterable) and len(updater) > 0:
        reply_obj = updater[0]
        permit_message = reply_obj.message
        if permit_message.chat.id == int(os.getenv("DEVELOPER_CHAT_ID", 0)) and permit_message.text == "Approved":
            _ = add(context._user_id, update.message.chat.first_name)
            await update.message.reply_text(text=f"管理员已经批准了你的请求, 现在你可以和我聊天啦.🥳")
            return
        if permit_message.chat.id == int(os.getenv("DEVELOPER_CHAT_ID", 0)) and permit_message.text == "Decline":
            await update.message.reply_text(text=f"抱歉, 管理员拒绝了你的请求. 可能他并不认识你🫢")
            return
