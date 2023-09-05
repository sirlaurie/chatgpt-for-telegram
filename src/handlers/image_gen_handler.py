#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


import httpx
from src.helpers import header

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler


GENERATE, EXIT = range(2)


async def image_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    _ = context
    assert update.message is not None
    global callback_query
    callback_query = await update.message.reply_text(
        text="欢迎使用图像生成功能, 此功能使用DALL.E作为功能接口, \n请发送你要生成图像的提示词, 或者点击下方Exit退出此功能.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton("Exit", callback_data="cancel_gen_image")]],
        ),
    )

    return GENERATE


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    _ = context
    assert update.message is not None

    prompt = update.message.text
    msg = await update.message.reply_text(
        text="正在生成图片, 请稍后..."
    )

    image = await gen_image(prompt)
    if not image.startswith("http"):
        await msg.edit_text(text=image)
        return -1

    await msg.edit_text(text="图片已生成, 正在获取图片...")
    await update.message.reply_photo(photo=image)
    await msg.delete()
    global callback_query
    callback_query = await update.message.reply_text(
        text="你可以继续发送新的提示词, 或者点击下方Exit退出此功能.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton("Exit", callback_data="cancel_gen_image")]],
        ),
    )
    return GENERATE


async def cancel_gen_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    _ = update, context

    await callback_query.edit_text(
        text="Bye!"
    )
    return ConversationHandler.END


async def gen_image(prompt) -> str:
    payload = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post("https://api.openai.com/v1/images/generations", headers=header, json=payload)
        if not response.is_success:
            return f"Error: a error happened when requesting, status code: {response.status_code}"
        data = response.json()
        return data.get("data", [{}])[0].get("url", "")
