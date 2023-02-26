import sys
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
import httpx
import asyncio


sys.path.insert(0, "..")
from allowed import allowed
from utils import waring, apply_to_prove

linux_terminal_handler = "linux_terminal"
translator_handler = "translator"
rewrite_handler = "rewrite"
code_helper_handler = "code_helper"
cyber_secrity_handler = "cyber_secrity"
etymologists_handler = "etymologists"
genius_handler = "genius"
advanced_frontend_handler = "advanced_frontend"
reset_handler = "reset"

linux_terminal = "I want you to act as a linux terminal. I will type commands and you will reply with what the terminal should show. I want you to only reply with the terminal output inside one unique code block, and nothing else. do not write explanations. do not type commands unless I instruct you to do so. When I need to tell you something in English, I will do so by putting text inside curly brackets {like this}. My first command is pwd"
translator = "我想让你充当私人翻译, 我会用任何语言与你交谈, 你将自动检测语言, 并始终翻译为中文. 我希望你可以使用比较高级的词语, 使他们更文艺, 但保持相同的意思. 不要写任何解释."
rewrite = "I want you to act as an English translator, spelling corrector and improver. I will speak to you in any language and you will detect the language, translate it and answer in the corrected and improved version of my text. I want you to replace my simplified A0-level words and sentences with more beautiful and elegant, upper level English words and sentences. Keep the meaning same, but make them more literary. I want you to only reply the correction, the improvements and nothing else, do not write explanations. "
cyber_secrity = "我想让你充当网络安全专家. 这可能包括解释网络现象, 对网络优化给出具体的可实施的建议."
etymologists = "我希望你充当词源学家. 我给你一个词, 你要研究那个词的来源, 追根溯源. 如果适用, 您还应该提供有关该词的含义如何随时间变化的信息."
genius = "我希望你充当IT专家. 我会向您提供有关我的技术问题所需的所有信息, 而您的职责是解决我的问题. 你应该使用你的计算机科学、网络基础设施和 IT 安全知识来解决我的问题. 在您的回答中使用适合所有级别的人的智能、简单和易于理解的语言将很有帮助. 用要点逐步解释您的解决方案很有帮助. 尽量避免过多的技术细节,但在必要时使用它们. 我希望您回复解决方案,而不是写任何解释."
advanced_frontend = "我希望你担任高级前端开发人员. 我将描述您需要实现的功能, 而你将使用以下工具编写项目代码的详细信息: NodeJs, react, nextjs, yarn, pnpm, nextauth, axios. 您应该将文件合并到单个index.js文件中, 别无其他."


def pick(act: str):
    match act:
        case "/linux_terminal":
            return linux_terminal
        case "/translator":
            return translator
        case "/rewrite":
            return rewrite
        case "/cyber_secrity":
            return cyber_secrity
        case "/etymologists":
            return etymologists
        case "/genius":
            return genius
        case "/advanced_frontend":
            return advanced_frontend
        case "/reset":
            return "hello"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    permitted, msg = allowed(context._user_id)
    if not permitted:
        await waring(update, context, msg)
        await apply_to_prove(update, context)
        return

    initial = False
    if isinstance(context.chat_data, dict):
        initial = context.chat_data.get("initial", True)

    if update.message.text in [
        "/linux_terminal",
        "/translator",
        "/rewrite",
        "/cyber_secrity",
        "/etymologists",
        "/genius",
        "/advanced_frontend",
        "/reset",
    ]:
        initial = True

    if update.message.text == "/reset":
        context.chat_data["conversation_id"] = None  # type: ignore
        context.chat_data["parent_message_id"] = None  # type: ignore
        await update.message.reply_text(text="好的, 已为你开启新会话! 请继续输入你的问题.")
        return

    conversation_id = (
        context.chat_data.get("conversation_id", None)
        if isinstance(context.chat_data, dict)
        else None
    )
    parent_message_id = (
        context.chat_data.get("parent_message_id", None)
        if isinstance(context.chat_data, dict)
        else None
    )

    message = message = await update.message.reply_text(text="please wait...")

    await update.get_bot().send_chat_action(
        update.message.chat.id, "typing", write_timeout=15.0
    )

    async def send_request(data):
        async with httpx.AsyncClient(timeout=None) as client:
            responses = await client.post(
                url=os.getenv("api_endpoint") or "",
                json=data,
                timeout=None,
            )
            asyncio.create_task(update_message(responses))

    async def update_message(responses):
        data = responses.json()
        if isinstance(context.chat_data, dict):
            context.chat_data["conversation_id"] = data["conversationId"]
            context.chat_data["parent_message_id"] = data["messageId"]

        await message.edit_text(
            text=data["text"],
            parse_mode=ParseMode.MARKDOWN_V2,
            write_timeout=None,
        )

    data = {
        "prompt": update.message.text if not initial else pick(update.message.text),
        "conversationId": conversation_id if not initial else None,
        "parentMessageId": parent_message_id if not initial else None,
    }

    print(f"{context._user_id}:")
    print(data)

    await send_request(data)
    # 调用模型
    # async with httpx.AsyncClient() as client:
    #     while not text:
    #         try:
    #             await update.get_bot().send_chat_action(
    #                 update.message.chat.id, "typing", write_timeout=15.0
    #             )

    #             response = await client.post(
    #                 "http://git.lloring.com:5000/conversation",
    #                 json=data,
    #                 timeout=60,
    #             )
    #             if response.status_code == 503:
    #                 await update.message.reply_text(
    #                     text="You exceeded your current quota, please check your plan and billing details."
    #                 )
    #                 return
    #             if response.status_code != 200:
    #                 await update.message.reply_text(
    #                     text="Rate limit reached for default-text-davinci-003 in organization org-mogd9SPFFICvnfu2W1DUPk1e on requests per min."
    #                 )
    #                 return
    #             resp = response.json()
    #             if isinstance(context.chat_data, dict):
    #                 context.chat_data["conversation_id"] = resp["conversationId"]
    #                 context.chat_data["parent_message_id"] = resp["messageId"]
    #             text = resp["response"]
    #             if isinstance(context.chat_data, dict):
    #                 context.chat_data["initial"] = False
    #             if text:
    #                 break
    #         except:
    #             continue
    #     await update.message.reply_text(text=text)
