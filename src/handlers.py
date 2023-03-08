import os
import sys
import httpx
from telegram import Update
# from telegram.constants import ParseMode
from telegram.ext import ContextTypes
# from telegram.helpers import escape_markdown
# from telegram import MessageEntity

sys.path.insert(0, "..")
from allowed import allowed
from utils import waring, apply_to_prove
# from helpers import escape_extend

reset_handler = "reset"
genius_handler = "genius"
expand_handler = "expand"
rewrite_handler = "rewrite"
translator_handler = "translator"
code_helper_handler = "code_helper"
etymologists_handler = "etymologists"
cyber_secrity_handler = "cyber_secrity"
linux_terminal_handler = "linux_terminal"
advanced_frontend_handler = "advanced_frontend"

expand = "我希望你充当一个文字工作者, 你在后面会收到我提供给你的一小段文字, 你的职责是根据这段文字扩充一下, 但保持相同的意思, 尽量多的使用中国政府机关常用的文书和表达方式, 尽量扩充到800字左右, 保持语句通顺, 逻辑通畅. 让别人不易察觉这段文字是由AI生成的."
genius = "我希望你充当IT专家. 我会向您提供有关我的技术问题所需的所有信息, 而您的职责是解决我的问题. 你应该使用你的计算机科学、网络基础设施和 IT 安全知识来解决我的问题. 在您的回答中使用适合所有级别的人的智能、简单和易于理解的语言将很有帮助. 用要点逐步解释您的解决方案很有帮助. 尽量避免过多的技术细节,但在必要时使用它们. 我希望您回复解决方案,而不是写任何解释."
rewrite = "I want you to act as an English translator, spelling corrector and improver. I will speak to you in any language and you will detect the language, translate it and answer in the corrected and improved version of my text. I want you to replace my simplified A0-level words and sentences with more beautiful and elegant, upper level English words and sentences. Keep the meaning same, but make them more literary. I want you to only reply the correction, the improvements and nothing else, do not write explanations. "
translator = "我想让你充当私人翻译, 我会用任何语言与你交谈, 你将自动检测语言, 并始终翻译为中文. 我希望你可以使用比较高级的词语, 使他们更文艺, 但保持相同的意思. 不要写任何解释."
etymologists = "我希望你充当词源学家. 我给你一个词, 你要研究那个词的来源, 追根溯源. 如果适用, 您还应该提供有关该词的含义如何随时间变化的信息."
cyber_secrity = "我想让你充当网络安全专家. 这可能包括解释网络现象, 对网络优化给出具体的可实施的建议."
linux_terminal = "I want you to act as a linux terminal. I will type commands and you will reply with what the terminal should show. I want you to only reply with the terminal output inside one unique code block, and nothing else. do not write explanations. do not type commands unless I instruct you to do so. When I need to tell you something in English, I will do so by putting text inside curly brackets {like this}. My first command is pwd"
advanced_frontend = "我希望你担任高级前端开发人员. 我将描述您需要实现的功能, 而你将使用以下工具编写项目代码的详细信息: NodeJs, react, nextjs, yarn, pnpm, nextauth, axios. 您应该将文件合并到单个index.js文件中, 别无其他."

header = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.getenv("openai_apikey") or ""}',
}


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
        case "/expand":
            return expand
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
        initial = context.chat_data.get("initial", False)

    if update.message.text in [
        "/linux_terminal",
        "/translator",
        "/rewrite",
        "/cyber_secrity",
        "/etymologists",
        "/genius",
        "/expand",
        "/advanced_frontend",
        "/reset",
    ]:
        initial = True

    if update.message.text == "/reset":
        if isinstance(context.chat_data, dict):
            context.chat_data["messages"] = []
        await update.message.reply_text(text="好的, 已为你开启新会话! 请继续输入你的问题.")
        return

    if update.message.text in ["Approved", "Decline"]:
        return

    message = await update.message.reply_text(text="please wait ...", pool_timeout=10.0)

    await update.get_bot().send_chat_action(
        update.message.chat.id, "typing", write_timeout=15.0, pool_timeout=10.0
    )

    async def send_request(data):
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                url=os.getenv("api_endpoint") or "", headers=header, json=data
            )
            resp = response.json()
            message_from_gpt = resp.get("choices", [{}])[0].get("message", {})
            content = message_from_gpt.get("content", "")
            await message.edit_text(
                text=content,
                # parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True
            )
            await update_message(message_from_gpt)

    async def update_message(message):
        old_messages = (
            context.chat_data.get("messages", [])
            if isinstance(context.chat_data, dict)
            else []
        )
        old_messages.append(message)
        if isinstance(context.chat_data, dict):
            context.chat_data["messages"] = old_messages

    request = {
        "role": "user",
        "content": update.message.text if not initial else pick(update.message.text),
    }

    messages = (
        (
            context.chat_data.get("messages", [])
            if isinstance(context.chat_data, dict)
            else []
        )
        if not initial
        else []
    )

    messages.append(request)
    data = {"model": "gpt-3.5-turbo-0301", "messages": messages[:5], "stream": False}
    await send_request(data)

    if isinstance(context.chat_data, dict):
        context.chat_data["messages"] = messages
