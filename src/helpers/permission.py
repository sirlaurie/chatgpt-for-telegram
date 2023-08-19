#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import CallbackContext

from src.constants import NOT_ALLOWD, NOT_PERMITED
from src.utils import is_allowed
from .unauthorize import warning


def check_permission(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(
        update: Update, context: CallbackContext, *args, **kwargs
    ) -> None:
        if not update.message:
            print("no message")
            return

        if not update.effective_user:
            print("no effective user")
            return

        permitted, _, msg = is_allowed(update.effective_user.id)
        if not permitted and msg == NOT_PERMITED:
            reply_from_admin = await warning(update, context)
            print(f"return {reply_from_admin}")
            return
        if not permitted and msg == NOT_ALLOWD:
            await update.message.reply_text(text=NOT_ALLOWD)
            print("not allowed")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper
