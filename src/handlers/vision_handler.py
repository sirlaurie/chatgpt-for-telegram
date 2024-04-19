#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import httpx
from telegram import Update
import telegram
from telegram.ext import ContextTypes

from ..helpers import headers


async def vision_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("processing with image")
    assert context.chat_data is not None
    if not update.message:
        _ = context  # no meaning. just for LSP
        return

    image = update.message.photo
    if not image:
        return

    try:
        img = image[-1]
        img_file = await img.get_file()
        img_file_path = img_file.file_path
    except telegram.error.TelegramError as error:
        await update.message.reply_text(
            text=f"Error: {error}.",
            pool_timeout=3600.0,
        )
        return

    data = {
        "model": context.chat_data.get("model", None),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这个图片里有什么?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": img_file_path},
                    },
                ],
            }
        ],
        "max_tokens": 2048,
    }

    print(f"data: {data}")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url="https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
        )
        if not response.is_success:
            print("error")
            return
        resp = response.json()
        print(resp)
        content = resp.get("choices", [{}])[0].get("message", {}).get("content")
        await update.message.reply_text(text=content, pool_timeout=60.0)
