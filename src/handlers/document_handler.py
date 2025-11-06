#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

from openai.types.chat import ChatCompletionUserMessageParam
from telegram import Update
import telegram
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from ..utils.document import read_document
from .message_handler import send_request


async def document_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        _ = context  # no meaning. just for LSP
        return

    _ = await update.message.reply_text(
        text=escape_markdown(
            text="File analysis feature is in beta and may be unstable. Please report any issues to the administrator.\nSupports various text files such as `.md`, `.txt`, `.py`, or proprietary document formats like PDF, EPUB.\n\nPlease send the file you want to analyze",
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

    msg = await update.message.reply_text(text="Reading file...", pool_timeout=3600.0)

    try:
        file = await document.get_file()
        file_path = file.file_path
    except telegram.error.TelegramError as error:
        await msg.edit_text(
            text=f"Error: {error}. Telegram bot currently only supports text files under 50MB",
            pool_timeout=3600.0,
        )
        return

    try:
        text = await file.download_as_bytearray()
        content = text.decode()
    except UnicodeDecodeError:
        assert file_path is not None
        await msg.edit_text(
            text="Detected non-text file, attempting to read as proprietary format...",
            pool_timeout=3600.0,
        )
        content = await read_document(update, file_path=file_path)
    except Exception:
        await msg.edit_text(
            text="Sorry, unable to read file content. Please confirm the file is of a supported type.",
            pool_timeout=3600.0,
        )
        return
    finally:
        await msg.edit_text(
            text="File parsed successfully, analyzing content...", pool_timeout=3600.0
        )

    if not content.strip():
        await msg.edit_text(
            text="File was parsed successfully, but no text content was detected. Please contact administrator if you have questions.",
            pool_timeout=3600.0,
        )
        return

    req: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": f"I will provide you with a file path and its content. Please infer what type of file this is based on the path, then read the content. When finished, respond in the following format: ```This is a [file type], the file contains [content summary]```. Here is the path and content: ```Path: {file_path}, Content: {content}```",
    }

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = [req]

    context.chat_data.update({"last_message_date": update.message.date.timestamp()})

    await send_request(update=update, context=context, messages=[req])
    return
