#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import html
import json
import httpx

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from telegram.helpers import escape_markdown

from src.constants import INIT_REPLY_MESSAGE
from src.helpers import check_permission, headers


TYPING_SRC_LANG, TYPING_TGT_LANG, TRANSLATE = range(3)


@check_permission
async def translator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        _ = context
        return

    await update.message.reply_text(
        text='欢迎使用翻译机功能, 你只需要告诉我你要在哪两种语言之间翻译, 剩下的只管发送就好\n\n首先, 请输入第一个语言类型, 形式为"中文", "English", "英语", "Deutsch"等普通人都能理解的即可.',
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
        text=f"Good!\n\n接下来请输入第二种语言类型, 形式如上即可.",
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
        text=f"""OK, 我会在{context.chat_data.get("source")}和{context.chat_data.get("target")}之间进行翻译. \n\n下面请发送你要翻译的内容""",
        write_timeout=3600.0,
        pool_timeout=3600.0,
    )

    return TRANSLATE


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    assert context.chat_data is not None

    text = str(update.message.text) + "."
    source_lang = context.chat_data.get("source", "英文")
    target_lang = context.chat_data.get("target", "中文")
    prompt = f"""
    翻译任务:
    如果我发送给你的文字是{source_lang}, 请将它翻译为{target_lang}; 如果我发送给你的文字是{target_lang}, 请将它翻译为{source_lang}.

    待翻译内容:
    {text}

    翻译要求:
    先将待翻译内容直译, 再按照目标语言的使用习惯优化语句保证内容自然流畅.

    注意事项:
    只需将翻译后的内容回复给我
    以纯文本格式回复
    请不要修改翻译任务部分的文本
    请注意源语言和目标语言，确保翻译方向正确
"""

    data = {
        "temperature": 0.3,
        "model": "gpt-3.5-turbo-instruct",
        "max_tokens": 3072,
        "prompt": prompt,
        "stream": True,
    }

    print(prompt)
    message = await update.message.reply_text(
        text=INIT_REPLY_MESSAGE, pool_timeout=15.0
    )

    full_content = ""
    index = 0
    client = httpx.AsyncClient(timeout=None)
    async with client.stream(
        method="POST",
        url="https://api.openai.com/v1/completions",
        headers=headers,
        json=data,
    ) as response:
        if not response.is_success:
            resp = await response.aread()
            content = resp.decode()
            content = json.loads(content)
            await message.edit_text(
                text=escape_markdown(
                    text="ERROR: " + content.get("error", {}).get("message", {}),
                    version=2,
                ),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            await response.aclose()
            return
        async for chunk in response.aiter_lines():
            index += 1
            string = chunk.strip("data: ")
            if not string:
                continue
            if "[DONE]" in chunk:
                await response.aclose()
                continue
            chunk = json.loads(string)
            is_stop = chunk.get("choices", [{}])[0].get("finish_reason", None)
            if is_stop:
                break

            chunk_message = chunk.get("choices", [{}])[0].get("text", "")
            if not chunk_message:
                continue
            full_content += chunk_message

            if index and index % 7 == 0:
                await message.edit_text(
                    text=escape_markdown(text=full_content, version=2),
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
        to_sent_message = f"{html.escape(full_content) + 'ㅤ'}ㅤ\n\n"
        await message.edit_text(
            text=to_sent_message,
            parse_mode=ParseMode.HTML,
        )

    await client.aclose()
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
