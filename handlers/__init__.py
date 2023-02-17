from typing import Any, Coroutine
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import httpx


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
translator = "我想让你充当英语翻译员、拼写纠正员和改进员. 我会用任何语言与你交谈,你会检测语言,翻译它并用我的文本的更正和改进版本回答. 我希望你用更优美优雅的词语和句子替换我的简单的词语和句子. 保持相同的意思,但使它们更文艺. 我要你只回复更正、改进,不要写任何解释."
rewrite = "I want you to act as an English translator, spelling corrector and improver. I will speak to you in any language and you will detect the language, translate it and answer in the corrected and improved version of my text. I want you to replace my simplified A0-level words and sentences with more beautiful and elegant, upper level English words and sentences. Keep the meaning same, but make them more literary. I want you to only reply the correction, the improvements and nothing else, do not write explanations. "
cyber_secrity = "我想让你充当网络安全专家. 我将询问一些提供一些关于如何存储和共享数据的具体信息,而你的工作就是想出保护这些数据免受恶意行为者攻击的策略. 这可能包括建议加密方法、创建防火墙或实施将某些活动标记为可疑的策略."
etymologists = "我希望你充当词源学家. 我给你一个词,你要研究那个词的来源,追根溯源. 如果适用,您还应该提供有关该词的含义如何随时间变化的信息."
genius = "我希望你充当 IT 专家. 我会向您提供有关我的技术问题所需的所有信息,而您的职责是解决我的问题. 你应该使用你的计算机科学、网络基础设施和 IT 安全知识来解决我的问题. 在您的回答中使用适合所有级别的人的智能、简单和易于理解的语言将很有帮助. 用要点逐步解释您的解决方案很有帮助. 尽量避免过多的技术细节,但在必要时使用它们. 我希望您回复解决方案,而不是写任何解释."
advanced_frontend = "我希望你担任高级前端开发人员. 我将描述您将使用以下工具编写项目代码的项目详细信息: NodeJs, react, nextjs, yarn, pnpm, nextauth, axios. 您应该将文件合并到单个 index.js 文件中,别无其他, 不要写解释."
reset = "从现在开始,退出你所充当的角色, 恢复初始状态"

def pick(act: str):
    match act:
        case "linux_terminal":
            return linux_terminal
        case "translator":
            return translator
        case "rewrite":
            return rewrite
        case "cyber_secrity":
            return cyber_secrity
        case "etymologists":
            return etymologists
        case "genius":
            return genius
        case "advanced_frontend":
            return advanced_frontend
        case "reset":
            return reset
        case _:
            return "hello"


def handler(act: str) -> Coroutine[Any, Any, None]:
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = ""
        initial = True
        if isinstance(context.chat_data, dict):
            initial = context.chat_data.get("initial", True)

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

        data = {
            "message": update.message.text if not initial else pick(act),
            "conversationId": conversation_id if update.message.text != "reset" else None,
            "parentMessageId": parent_message_id if update.message.text != "reset" else None
        }

        # 调用模型
        async with httpx.AsyncClient() as client:
            while not text:
                try:
                    await update.get_bot().send_chat_action(
                        update.message.chat.id, "typing", write_timeout=20000
                    )

                    response = await client.post(
                        "http://git.lloring.com:5000/conversation", json=data, timeout=60
                    )
                    resp = response.json()
                    if isinstance(context.chat_data, dict):
                        context.chat_data["conversation_id"] = resp["conversationId"]
                        context.chat_data["parent_message_id"] = resp["messageId"]
                    text = resp["response"]
                    if isinstance(context.chat_data, dict):
                        context.chat_data["initial"] = False
                    if text:
                        break
                except:
                    continue
            await update.message.reply_text(text=text)
    return handle # type: ignore
