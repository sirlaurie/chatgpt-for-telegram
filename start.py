#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

# import re
import os
import logging

from telegram.constants import ParseMode

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackQueryHandler,
)

from src.helpers.permission import check_permission
from src.constants.messages import WELCOME_MESSAGE
from src.helpers.stripe_helper import PRICING
from src.helpers.subscription_check import format_price
from src.constants.commands import (
    reset_command,
    switch_model_command,
    admin_command,
    my_prompts_command,
    create_new_prompt_command,
    document_command,
    translator_command,
    gen_image_command,
)
from src.constants.constant import (
    APPROVE,
    DECLINE,
    UPGRADE,
    DOWNGRADE,
    WAITING,
    PERMITTED,
    PREMIUM,
)
from src.handlers import handler
from src.handlers.admin_handler import admin_handler
from src.handlers.reset_handler import reset_handler
from src.handlers.switch_model_handler import (
    switch_model_handler,
    switch_model_callback,
)
from src.handlers.my_prompts_handler import my_prompts_handler
from src.handlers.new_prompt_handler import create_new_prompt_handler
from src.handlers.document_handler import document_handler, document_start
from src.handlers.translator_handler import (
    TYPING_SRC_LANG,
    TYPING_TGT_LANG,
    TRANSLATE,
    typing_src_lang,
    typing_tgt_lang,
    translator_handler,
    translate,
    stop,
)
from src.handlers.image_gen_handler import (
    GENERATE,
    generate,
    image_start,
    cancel_gen_image,
)
from src.handlers.admin_handler import (
    CHOOSING,
    MANAGER,
    back,
    finish,
    query_list,
    manage_user,
    action,
)
from src.handlers.my_prompts_handler import (
    prompt_callback_handler,
    view_prompts,
)
from src.handlers.new_prompt_handler import (
    prompt_name_handler,
    prompt_content_handler,
    share_handler,
    prompt_name,
    prompt_content,
    share,
)
from src.handlers.subscription_handler import (
    subscribe_command,
    my_subscription_command,
    cancel_subscription_command,
    usage_command,
    handle_cancel_auto_renew,
    handle_reactivate_subscription,
    handle_confirm_cancel_subscription,
    handle_keep_subscription,
)
from src.helpers.subscription_check import (
    handle_subscribe_callback,
    handle_cancel_payment,
)

# Enable logging
logging.basicConfig(
    filename="error.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)


@check_permission
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        _ = context
        return

    monthly_price = format_price(PRICING["monthly"]["price"])
    yearly_price = format_price(PRICING["yearly"]["price"])
    yearly_monthly = format_price(PRICING["yearly"]["price"] / 12)

    welcome_text = f"""
🤖 *Welcome to AI Assistant Bot*

Your personal AI assistant powered by the latest AI models.

---
*📋 ABOUT OUR SERVICE*
---

We provide unlimited access to multiple cutting-edge AI models through Telegram:
• GPT-4o, GPT-4.1, GPT-4o Mini
• Gemini 2.5 Flash, Gemini 2.5 Pro
• DALL-E 3 for image generation

---
*💎 SUBSCRIPTION PLANS*
---

*Monthly:* {monthly_price}/month
*Yearly:* {yearly_price}/year (Save 17% - {yearly_monthly}/month)

---
*✨ FEATURES INCLUDED*
---

✓ Unlimited AI conversations
✓ Access to all AI models
✓ Document analysis (PDF, EPUB, etc.)
✓ DALL-E 3 image generation
✓ Multi-language translation
✓ Conversation history
✓ Custom prompts
✓ Priority support

---
*🔐 SECURE PAYMENT*
---

All payments are processed securely through Stripe, one of the world's most trusted payment platforms. We never store your payment information.

---
*📜 TERMS & POLICIES*
---

• Subscriptions auto-renew monthly/yearly
• Cancel anytime before next billing cycle
• 7-day refund policy
• No hidden fees
• Full service details: Use /terms

---
*📞 CONTACT & SUPPORT*
---

Support: Use /help command
Email: support@autheai.com

---

*Ready to start?* Use /subscribe to choose your plan!

Type /help to see all available commands.
"""

    keyboard = [
        [
            InlineKeyboardButton("💳 Subscribe Now", callback_data="subscription_info"),
            InlineKeyboardButton("📋 View Plans", callback_data="subscription_info"),
        ],
        [
            InlineKeyboardButton("📜 Terms & Policies", callback_data="show_terms"),
            InlineKeyboardButton("❓ Help", callback_data="show_help"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show terms and conditions"""
    if not update.message:
        return

    terms_text = """
📜 *TERMS OF SERVICE & POLICIES*

---
*🔰 SERVICE DESCRIPTION*
---

AI Assistant Bot provides access to multiple AI models (GPT-4, Gemini, etc.) through Telegram for text generation, document analysis, image creation, and translation services.

---
*💳 SUBSCRIPTION & BILLING*
---

• Monthly: $9.99/month
• Yearly: $99.99/year
• Subscriptions auto-renew unless cancelled
• Billing occurs on the same day each period
• All payments processed via Stripe
• We do not store payment information

---
*❌ CANCELLATION POLICY*
---

• Cancel anytime through /my_subscription
• Cancellation takes effect at end of billing period
• No partial refunds for unused time
• Access continues until subscription expires
• Use /cancel_subscription to cancel

---
*💰 REFUND POLICY*
---

• 7-day money-back guarantee for first purchase
• Contact support within 7 days for refund
• Email: support@autheai.com
• Refunds processed within 5-10 business days
• No refunds after 7 days

---
*🔒 PRIVACY & DATA*
---

• We don't sell your data
• Conversations stored for service functionality
• Payment info secured by Stripe (PCI compliant)
• We collect: Telegram ID, subscription status
• You can request data deletion anytime

---
*⚖️ ACCEPTABLE USE*
---

Prohibited activities:
• Illegal content generation
• Harassment or hate speech
• Automated/bot usage
• Sharing account access
• Violating third-party rights

Violations may result in immediate termination without refund.

---
*🛡️ SERVICE AVAILABILITY*
---

• Service provided "as is"
• 99% uptime target (no guarantee)
• Maintenance windows announced when possible
• No liability for service interruptions
• Rate limits may apply during high usage

---
*📧 CONTACT*
---

Support: support@autheai.com
Bot: Use /help for assistance

By subscribing, you agree to these terms.
Last updated: January 2025
"""

    await update.message.reply_text(
        text=terms_text,
        parse_mode="Markdown",
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed information about the service"""
    if not update.message:
        return

    monthly_price = format_price(PRICING["monthly"]["price"])
    yearly_price = format_price(PRICING["yearly"]["price"])

    about_text = f"""
ℹ️ *ABOUT AI ASSISTANT BOT*

---
*🎯 WHAT WE OFFER*
---

A comprehensive AI assistant service accessible directly through Telegram, providing unlimited access to the world's leading AI models.

---
*🤖 AVAILABLE AI MODELS*
---

*OpenAI Models:*
• GPT-4o - Latest flagship model
• GPT-4.1 - Enhanced reasoning
• GPT-4o Mini - Fast & efficient

*Google Models:*
• Gemini 2.5 Flash - Speed optimized
• Gemini 2.5 Pro - Most capable
• Gemini Flash Latest - Auto-updated

*Image Generation:*
• DALL-E 3 - High-quality images

---
*💎 PRICING*
---

*Monthly Plan:* {monthly_price}/month
• Unlimited messages
• All AI models
• All features

*Yearly Plan:* {yearly_price}/year
• Save 17% compared to monthly
• Equivalent to $8.33/month
• All features included

---
*✨ KEY FEATURES*
---

• Switch between AI models instantly
• Analyze documents (PDF, EPUB, TXT, etc.)
• Generate images from text descriptions
• Translate between languages
• Create and save custom prompts
• Persistent conversation history
• Priority customer support

---
*🔐 SECURITY & TRUST*
---

• Payments via Stripe (PCI DSS compliant)
• No payment data stored on our servers
• Industry-standard encryption
• Regular security audits
• Transparent pricing - no hidden fees

---
*📞 SUPPORT*
---

Email: support@autheai.com
Response time: Within 24 hours

---

Ready to get started?
Use /subscribe to choose your plan!
"""

    keyboard = [
        [
            InlineKeyboardButton("💳 Subscribe", callback_data="subscription_info"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=about_text,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help and available commands"""
    if not update.message:
        return

    help_text = """
❓ *HELP & COMMANDS*

---
*💬 BASIC COMMANDS*
---

/start - Show welcome & service info
/help - Show this help message
/subscribe - Choose a subscription plan
/my_subscription - View your subscription status
/usage - Check your usage statistics

---
*⚙️ FEATURE COMMANDS*
---

/reset - Start a new conversation
/switch_model - Change AI model
/my_prompts - View your custom prompts
/new_prompt - Create a custom prompt
/document - Analyze documents
/translate - Translate text
/gen_image - Generate images with DALL-E 3

---
*📋 INFORMATION COMMANDS*
---

/terms - View terms of service
/about - Learn more about the service

---
*🔧 SUBSCRIPTION MANAGEMENT*
---

/cancel_subscription - Cancel auto-renewal

---
*📞 NEED MORE HELP?*
---

Email: support@autheai.com
Response time: Within 24 hours

We're here to help! 🤖
"""

    await update.message.reply_text(
        text=help_text,
        parse_mode="Markdown",
    )


async def handle_info_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle information button callbacks"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data == "show_terms":
        terms_text = """
📜 *TERMS OF SERVICE*

*Subscription:* Auto-renews monthly/yearly
*Cancellation:* Anytime, effective at period end
*Refund:* 7-day money-back guarantee
*Privacy:* We don't sell your data
*Payment:* Secured by Stripe

Full terms: Use /terms command
Contact: support@autheai.com
"""
        await query.edit_message_text(
            text=terms_text,
            parse_mode="Markdown",
        )

    elif query.data == "show_help":
        help_text = """
❓ *QUICK HELP*

*Available Commands:*
/start - Show welcome & info
/subscribe - Choose a plan
/my_subscription - View subscription
/usage - Check usage status
/terms - Full terms & policies
/about - Detailed service info
/help - Show this help

*Need Support?*
Email: support@autheai.com
Response within 24 hours

Ready to subscribe? Use /subscribe
"""
        await query.edit_message_text(
            text=help_text,
            parse_mode="Markdown",
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # logger.warning(f"Update {update} caused error {context.error}")
    # update_str = update.to_dict() if isinstance(update, Update) else str(update)

    # message = (
    #     f"An exception was raised while handling an update\n"
    #     f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
    #     "</pre>\n\n"
    #     f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
    #     f"<pre>ERROR: {context.error}</pre>\n\n"
    # )

    # await context.bot.send_message(
    #     chat_id=os.getenv("DEVELOPER_CHAT_ID", 0),
    #     text=message,
    #     parse_mode=ParseMode.HTML,
    # )

    if hasattr(update, "effective_user") and update.effective_user:
        user_id = update.effective_user.id
        _ = await context.bot.send_message(
            chat_id=user_id,
            text=f"<pre>ERROR: {context.error}</pre>\n\n",
            parse_mode=ParseMode.HTML,
        )


def main() -> None:
    bot_token: str = os.environ.get("bot_token", "")
    # """Start the bot."""
    # # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .connect_timeout(connect_timeout=5 * 60.0)
        .token(bot_token)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(reset_command, reset_handler))
    application.add_handler(CommandHandler(switch_model_command, switch_model_handler))

    # Information commands
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("terms", terms_command))
    application.add_handler(CommandHandler("about", about_command))

    # Subscription commands
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("my_subscription", my_subscription_command))
    application.add_handler(CommandHandler("cancel_subscription", cancel_subscription_command))
    application.add_handler(CommandHandler("usage", usage_command))

    # Subscription callback handlers
    application.add_handler(
        CallbackQueryHandler(
            handle_subscribe_callback,
            pattern="^subscribe_|^subscription_info$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_cancel_payment,
            pattern="^cancel_payment$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_cancel_auto_renew,
            pattern="^cancel_auto_renew$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_reactivate_subscription,
            pattern="^reactivate_subscription$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_confirm_cancel_subscription,
            pattern="^confirm_cancel_subscription$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_keep_subscription,
            pattern="^keep_subscription$"
        )
    )

    # Information callback handlers
    application.add_handler(
        CallbackQueryHandler(
            handle_info_callbacks,
            pattern="^show_terms$|^show_help$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            switch_model_callback, pattern="^gpt|^gemini|^llama|^mixtral"
        )
    )
    application.add_handler(CommandHandler(my_prompts_command, my_prompts_handler))
    application.add_handler(
        CallbackQueryHandler(
            prompt_callback_handler, pattern=f"{view_prompts}|^prompt (17)\\d{8}$"
        )
    )
    # Approval callback removed - using public bot mode with auto-approval
    new_prompt_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(create_new_prompt_command, create_new_prompt_handler),
        ],
        states={
            prompt_name: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_name_handler),
            ],
            prompt_content: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_content_handler),
            ],
            share: [
                CallbackQueryHandler(share_handler, pattern="yes|no"),
            ],
        },
        fallbacks=[],
    )
    admin_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(admin_command, admin_handler),
        ],
        states={
            CHOOSING: [
                CallbackQueryHandler(
                    query_list, pattern=f"{WAITING}|{PERMITTED}|{PREMIUM}"
                ),
            ],
            MANAGER: [
                CallbackQueryHandler(manage_user, pattern=r"\d+"),
                CallbackQueryHandler(
                    action, pattern=f"{APPROVE}|{DECLINE}|{UPGRADE}|{DOWNGRADE} \\d+$"
                ),
                CallbackQueryHandler(back, pattern="^back$"),
                CallbackQueryHandler(finish, pattern="^finish$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(finish, pattern="^finish$"),
        ],
    )

    translator_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(translator_command, translator_handler),
        ],
        states={
            TYPING_SRC_LANG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, typing_src_lang),
                MessageHandler(filters.Regex("^/Done$"), stop),
            ],
            TYPING_TGT_LANG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, typing_tgt_lang),
                MessageHandler(filters.Regex("^/Done$"), stop),
            ],
            TRANSLATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translate),
                MessageHandler(filters.Regex("^/Done$"), stop),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^/Done$"), stop),
        ],
    )

    image_gen_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(gen_image_command, image_start),
        ],
        states={
            GENERATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate),
                CallbackQueryHandler(cancel_gen_image, pattern="^cancel_gen_image$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_gen_image, pattern="^cancel_gen_image$"),
        ],
    )
    application.add_handler(admin_conv_handler)
    application.add_handler(new_prompt_conv_handler)
    application.add_handler(translator_conv_handler)
    application.add_handler(image_gen_conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    application.add_handler(CommandHandler(document_command, document_start))
    # application.add_handler(MessageHandler(filters.PHOTO, vision_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    # error handler
    # application.add_error_handler(error_handler)  # type: ignore
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
