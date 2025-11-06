#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

headers = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.environ.get("OPENAI_API_KEY") or ""}',
}


GENERATE, EXIT = range(2)


async def image_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    _ = context
    assert update.message is not None
    global callback_query
    callback_query = await update.message.reply_text(
        text="Welcome to the image generation feature. This uses DALL-E 3 as the backend.\nPlease send your image prompt, or click Exit below to exit this feature.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("Exit", callback_data="cancel_gen_image")]
            ],
        ),
    )

    return GENERATE


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    _ = context
    assert update.message is not None

    prompt = update.message.text
    msg = await update.message.reply_text(text="Generating image, please wait...")

    image = await gen_image(prompt)
    if not image.startswith("http"):
        await msg.edit_text(text=image)
        return -1

    await msg.edit_text(text="Image generated, retrieving...")
    await msg.delete()
    await update.message.reply_photo(photo=image)
    global callback_query
    callback_query = await update.message.reply_text(
        text="You can continue sending new prompts, or click Exit below to exit this feature.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("Exit", callback_data="cancel_gen_image")]
            ],
        ),
    )
    return GENERATE


async def cancel_gen_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    _ = update, context

    await callback_query.edit_text(text="Bye!")
    return ConversationHandler.END


async def gen_image(prompt) -> str:
    payload = {"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url="https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload,
        )
        if not response.is_success:
            try:
                error_reason = response.json().get("error", {}).get("message")
            except Exception:
                error_reason = None
            return f"Error: a error happened when requesting, status code: {error_reason if error_reason else response.status_code }"
        data = response.json()
        return data.get("data", [{}])[0].get("url", "")
