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


def check_permission(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any] | None]:
    """
    Check if user is allowed to use the bot.

    For public bot mode:
    - New users are automatically allowed
    - Only banned users (allow=0) are blocked
    - Subscription limits are checked separately in @check_subscription
    """
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

        user = update.effective_user
        nickname = user.first_name or "Unknown"

        # Check if user is allowed (auto-create new users with allow=1)
        permitted, is_premium, is_waiting, error_msg = is_allowed(user.id, nickname)

        # Only block if user is explicitly banned (allow=0)
        if not permitted:
            # User is banned by admin
            await update.message.reply_text(
                text="❌ 你已被管理员封禁，无法使用此 bot。\n\nYou have been banned by the administrator."
            )
            # Notify admin about banned user's attempt
            await context.bot.send_message(
                chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
                text=f"🚫 Banned user {nickname} (ID: {user.id}) tried to send: {update.message.text}",
                parse_mode=ParseMode.HTML,
            )
            return

        # User is allowed, proceed to next check (subscription)
        return await func(update, context, *args, **kwargs)

    return wrapper
