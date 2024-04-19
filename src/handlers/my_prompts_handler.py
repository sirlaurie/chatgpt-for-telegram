#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


import datetime
from openai.types.chat import ChatCompletionUserMessageParam
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .message_handler import send_request
from ..helpers.permission import check_permission
from ..utils.operations import query

view_prompts = "view_prompts"


@check_permission
async def my_prompts_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message:
        _ = context.bot
        return

    if not update.effective_user:
        return

    telegram_id = int(update.effective_user.id)

    maps = {"telegramId": telegram_id}

    user_prompts = query(table="Prompt", maps=maps)

    inline_keyboard = [
        [
            # InlineKeyboardButton("创建新的prompt", callback_data=new_prompt),
            InlineKeyboardButton("查看共享的prompt", callback_data=view_prompts),
        ],
    ]

    if not user_prompts:
        await update.message.reply_text(
            text="抱歉, 未查询到你创建过任何Prompt.\n\n你可以选择创建新的prompt或者查看其他人共享的prompt.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
        )
        return
    if len(user_prompts) > 1:
        inline_prompts_keyboard = [
            [
                InlineKeyboardButton(
                    user_prompts[i][1],
                    callback_data=f"prompt {str(user_prompts[i][3])}",
                ),
                InlineKeyboardButton(
                    user_prompts[i + 1][1],
                    callback_data=f"prompt {str(user_prompts[i + 1][3])}",
                ),
            ]
            for i in range(0, len(user_prompts) - 1, 2)
        ]
    else:
        inline_prompts_keyboard = []

    if len(user_prompts) % 2 == 1:
        user_prompt_index = len(user_prompts) - 1
        inline_prompts_keyboard.append(
            [
                InlineKeyboardButton(
                    f"{user_prompts[user_prompt_index][1]}",
                    callback_data=f"prompt {str(user_prompts[user_prompt_index][3])}",
                )
            ]
        )
    inline_prompts_keyboard.extend(inline_keyboard)
    await update.message.reply_text(
        text="请选择你的prompt",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_prompts_keyboard),
    )


async def prompt_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.effective_user:
        return
    callback_query = update.callback_query
    if not callback_query:
        return
    message = callback_query.message
    if not message:
        return

    await callback_query.answer()

    query_data = callback_query.data

    if query_data == view_prompts:
        maps = {"share": 1}
        shared_prompts = query(table="Prompt", maps=maps)
        if len(shared_prompts) > 1:
            inline_prompts_keyboard = [
                [
                    InlineKeyboardButton(
                        shared_prompts[i][1], callback_data=str(shared_prompts[i][3])
                    ),
                    InlineKeyboardButton(
                        shared_prompts[i + 1][1],
                        callback_data=str(shared_prompts[i + 1][3]),
                    ),
                ]
                for i in range(0, len(shared_prompts) - 1, 2)
            ]
        else:
            inline_prompts_keyboard = []

        if len(shared_prompts) % 2 == 1:
            user_prompt_index = len(shared_prompts) - 1
            inline_prompts_keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{shared_prompts[user_prompt_index][1]}",
                        callback_data=str(shared_prompts[user_prompt_index][3]),
                    )
                ]
            )
        await message.edit_text(
            text="以下是共享的prompt",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_prompts_keyboard),
        )
        return
    if query_data is not None and query_data.startswith("prompt"):
        prompt_id = query_data.split(" ")[1]
        prompt = query(table="Prompt", maps={"createAt": int(prompt_id)})

        prompt_content = prompt[0][2]
        msg: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": prompt_content,
        }
        await message.delete()
        assert context.chat_data is not None
        if context.bot_data.get("initial", True):
            messages = []
        else:
            last_message_date = context.chat_data.get("last_message_date", 0)
            last_message_datetime = datetime.datetime.fromtimestamp(
                last_message_date, tz=datetime.timezone.utc
            )
            time_difference = (
                datetime.datetime.now(tz=datetime.timezone.utc) - last_message_datetime
            )

            if time_difference > datetime.timedelta(hours=1.0):
                messages = []
            elif isinstance(context.chat_data, dict):
                messages = context.chat_data.get("messages", [])
            else:
                messages = []

        messages.append(msg)
        context.chat_data.update({"last_message_date": message.date.timestamp()})
        context.chat_data["messages"] = messages

        await send_request(update, context, messages=[msg])
        return
