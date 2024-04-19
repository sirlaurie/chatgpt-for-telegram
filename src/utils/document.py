#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

import httpx
from fitz import fitz
from telegram import Update
from io import BytesIO

from ..constants.constant import SUPPPORTED_FILE


async def read_document(update: Update, file_path: str) -> str:
    assert update.message is not None

    try:
        file_type = file_path.split(".")[-1]
    except Exception as e:
        print(e)
        await update.message.reply_text(
            text="未能获取到文件扩展名, 请上传一个具有确定扩展名的文件",
            pool_timeout=3600.0,
        )
        return ""
    if file_type not in SUPPPORTED_FILE:
        await update.message.reply_text(
            text="目前支持的文件类型包括\n\n1.纯文本文件, 如txt, Markdown, source code文件.\n2.专有格式的文本文件, 如PDF, XPS, ePub, Mobi",
            pool_timeout=3600.0,
        )
        return ""
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.get(url=file_path)
        data = BytesIO(initial_bytes=response.content)
    file = fitz.open(stream=data, filetype=file_type)  # type: ignore
    text_of_file = ""
    for page in file:
        text_of_file += page.get_text()
    return text_of_file
