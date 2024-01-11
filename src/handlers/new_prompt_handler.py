#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from src.helpers.permission import check_permission
from src.utils.operations import add_prompt


prompt_name, prompt_content, share = range(3)

prompt = {}


@check_permission
async def create_new_prompt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    await update.message.reply_text(
        text="创建一个自定义的prompt, 请输入你的prompt名称, 例如: 翻译助手",
        pool_timeout=3600.0,
    )
    return prompt_name


async def prompt_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    text = update.message.text
    if not text:
        return prompt_name
    prompt.update({"name": text})
    await update.message.reply_text(
        text="接下来请输入你的prompt具体内容", pool_timeout=3600.0
    )
    return prompt_content


async def prompt_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    text = update.message.text
    if not text:
        return prompt_content
    prompt.update({"prompt": text})
    inline_keyboard = [
        InlineKeyboardButton("Yes", callback_data="yes"),
        InlineKeyboardButton("No", callback_data="no"),
    ]
    await update.message.reply_text(
        text="你是否愿意将你的prompt共享?",
        reply_markup=InlineKeyboardMarkup([inline_keyboard]),
        pool_timeout=3600.0,
    )
    return share


async def share_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    callback_query = update.callback_query
    if not callback_query:
        return share
    await callback_query.answer()
    query_data = callback_query.data
    if not query_data:
        return share
    prompt.update({"share": 1 if query_data == "yes" else 0})
    add_prompt(user_id=update.effective_user.id, prompt=prompt)
    await callback_query.edit_message_text(
        text="恭喜!你成功的创建了一个自定义prompt!",
        reply_markup=None,
        pool_timeout=3600.0,
    )
    return ConversationHandler.END
