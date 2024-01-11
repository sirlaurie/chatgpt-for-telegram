#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


from telegram import Update
from telegram.ext import ContextTypes

from src.constants.commands import create_new_assistant_command
from src.helpers.permission import check_permission


@check_permission
async def create_new_assistant_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    pass
