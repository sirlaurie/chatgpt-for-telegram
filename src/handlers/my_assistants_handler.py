#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


from telegram import Update
from telegram.ext import ContextTypes

from ..constants.commands import my_assistants_command
from ..helpers.permission import check_permission


@check_permission
async def my_assistants_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
