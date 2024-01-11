#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from openai.types.chat import ChatCompletionUserMessageParam
from telegram import Update
import telegram
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.utils.document import read_document
from src.handlers.message_handler import send_request


async def document_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        _ = context  # no meaning. just for LSP
        return

    await update.message.reply_text(
        text=escape_markdown(
            text="文件功能尚在测试中, 可能不稳定, 如有问题请反馈给我的主人.\n支持各种纯文本文件, 如`.md`, `.txt`, `.py`, 或者专有格式文档, 如PDF, EPUB.\n\n请发送你要分析的文件",
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

    msg = await update.message.reply_text(text="疯狂读取文件中...", pool_timeout=3600.0)

    try:
        file = await document.get_file()
        file_path = file.file_path
    except telegram.error.TelegramError as error:
        await msg.edit_text(
            text=f"Error: {error}. telegram bot目前仅支持50M以下的文本文件",
            pool_timeout=3600.0,
        )
        return

    try:
        text = await file.download_as_bytearray()
        content = text.decode()
    except UnicodeDecodeError:
        assert file_path is not None
        await msg.edit_text(
            text="检测到此文件不是文本文件, 尝试切换为专有格式读取模式....",
            pool_timeout=3600.0,
        )
        content = await read_document(update, file_path=file_path)
    except Exception:
        await msg.edit_text(
            text="抱歉, 未能读取文件内容, 请确认文件是否属于支持的类型.",
            pool_timeout=3600.0,
        )
        return
    finally:
        await msg.edit_text(
            text="已成功解析文件, 正在理解你的文件中...", pool_timeout=3600.0
        )

    if not content.strip():
        await msg.edit_text(
            text="虽然文件解析成功了, 但是没有识别到任何文字内容. 如有疑问请联系管理员查看.",
            pool_timeout=3600.0,
        )
        return

    req: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": f"我会给你一个文件路径和文件的内容, 请你根据文件路径推测这个文件是什么类型文件, 然后阅读内容, 当你执行完成时, 按照下面的格式进行回答:```这是一个[文件类型], 这个文件是[内容概述]```. 以下是路径和内容 ```路径: {file_path}, 内容: {content}```",
    }

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = [req]

    context.chat_data.update({"last_message_date": update.message.date.timestamp()})

    await send_request(update=update, context=context, messages=[req])
    return
