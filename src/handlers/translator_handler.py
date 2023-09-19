#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
# from telegram._replykeyboardmarkup import ReplyKeyboardMarkup

# from telegram import MessageEntity

# from src.constants import TARGET_LANGUAGE_KEYBOARD

from src.helpers import check_permission, send_request
from src.constants import translator_prompt


TYPING_SRC_LANG, TYPING_TGT_LANG, TRANSLATE = range(3)


@check_permission
async def translator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        _ = context
        return

    await update.message.reply_text(
        text='欢迎使用翻译机功能, 你只需要告诉我你要翻译的文字是什么语言, 和想要翻译成什么语言, 剩下的只管发送就好\n\n首先, 请输入你要准备翻译的语言, 形式为"中文", "English", "英语", "Deutsch"等普通人都能理解的即可.',
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )

    return TYPING_SRC_LANG


async def typing_src_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    assert context.chat_data is not None

    src_lang = update.message.text
    context.chat_data.update({"source": src_lang})
    await update.message.reply_text(
        text=f"OK, 您要翻译的文字语言是{src_lang}. \n\n接下来请输入您要翻译成语言类型, 形式如上即可.",
        write_timeout=3600.0,
        pool_timeout=3600.0,
        )

    return TYPING_TGT_LANG


async def typing_tgt_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    assert context.chat_data is not None

    tgt_lang = update.message.text
    context.chat_data.update({"target": tgt_lang})
    await update.message.reply_text(
        text=f"OK, 您想要翻译成的文字语言是{tgt_lang}. \n\n请让我准备一下",
        write_timeout=3600.0,
        pool_timeout=3600.0,
        )

    init_content = translator_prompt.format(src_lang=context.chat_data.get('source'), tgt_lang=context.chat_data.get("target"))
    req = {
        "role": "user",
        "content": init_content
    }

    context.chat_data["messages"] = [req]

    data = {
        "model": context.chat_data.get("model", None)
        or os.getenv("model", "gpt-3.5-turbo-16k"),
        "messages": [req],
        "stream": True,
    }

    await send_request(update=update, context=context, data=data)

    return TRANSLATE


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    assert context.chat_data is not None

    text = update.message.text

    req = {
        "role": "user",
        "content": text
    }

    old_messages = context.chat_data.get("messages", [])
    if len(old_messages) > 2:
        messages = old_messages[:2]
    else:
        messages = old_messages

    messages.append(req)

    data = {
        "model": context.chat_data.get("model", None)
        or os.getenv("model", "gpt-3.5-turbo-16k"),
        "messages": messages,
        "stream": True,
    }

    await send_request(update=update, context=context, data=data)

    return TRANSLATE


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        _ = context
        return

    await update.message.reply_text(
        text="See you.",
        write_timeout=3600.0,
        pool_timeout=3600.0,
        )

    return ConversationHandler.END

