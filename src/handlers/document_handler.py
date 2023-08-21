#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
from telegram import Update
from telegram import Update
import telegram
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.helpers import send_request


async def document_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        text=escape_markdown(
            text="文件功能尚在测试中, 可能不稳定, 如有问题请反馈给我的主人.\n支持各种纯文本文件, 如`.md`, `.txt`, `.py`.\nPDF文件的功能尚在开发中, 敬请期待. \n请开始发送文件",
            version=2,
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
        pool_timeout=3600.0,
    )
    return


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    assert context.chat_data is not None
    if not update.message:
        return

    document = update.message.document
    if not document:
        return

    try:
        file = await document.get_file()
        file_path = file.file_path
    except telegram.error.TelegramError as error:
        await update.message.reply_text(
            text=f"Error: {error}. telegram bot目前仅支持50M以下的文本文件", pool_timeout=3600.0
        )
        return

    text = await file.download_as_bytearray()
    try:
        content = text.decode()
    except UnicodeDecodeError as error:
        await update.message.reply_text(
            text="此文件不是文本文件, 请确认要传输的文件类型.", pool_timeout=3600.0
        )
        return

    req = {
            "role": "user",
            "content": f"我会给你一个文件路径和文件的内容, 请你根据文件路径推测这个文件是什么类型文件, 然后阅读内容, 当你执行完成时, 按照下面的格式进行回答:```这个文件类型是[文件类型], 这个文件是[内容概述]```. 以下是路径和内容 ```路径: {file_path}, 内容: {content}```"
        }

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = [req]

    data = {
        "model": context.chat_data.get("model", None)
        or os.getenv("model", "gpt-3.5-turbo-16k"),
        "messages": [req],
        "stream": True,
    }

    first_name = getattr(update.message.from_user, "first_name", None)
    print(f"************ from {first_name}: ************\n{data}")

    await send_request(update=update, context=context, data=data)
    return
