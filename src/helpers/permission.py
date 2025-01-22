#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import os
from collections.abc import Coroutine
from functools import wraps
from typing import Any, Callable

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from ..constants.messages import NOT_ALLOWD, NOT_PERMITED
from ..utils import is_allowed
from .unauthorize import warning


def check_permission(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any] | None]:
    @wraps(func)
    async def wrapper(
        update: Update,
        context: CallbackContext[Any, Any, Any, Any],
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any]
    ) -> Coroutine[Any, Any, Any] | None:
        if not update.message:
            return

        if not update.effective_user:
            return

        message = update.message.text
        permitted, *_, msg = is_allowed(update.effective_user.id)
        if not permitted and msg == NOT_PERMITED:
            await warning(update, context)
            return

        if not permitted and msg == NOT_ALLOWD:
            await context.bot.send_message(
                chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
                text=f"from {update.effective_user.first_name}: {message}",
                parse_mode=ParseMode.HTML,
            )
            _ = await update.message.reply_text(text=NOT_ALLOWD)
            return

        return await func(update, context, *args, **kwargs)

    return wrapper
