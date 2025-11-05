#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Subscription check decorator

from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..utils.subscription_operations import (
    check_subscription_status,
    increment_free_usage,
    FREE_MESSAGE_LIMIT,
)
from .stripe_helper import create_checkout_session, PRICING
import logging
import os

logger = logging.getLogger(__name__)


def format_price(price: float, currency: str = "USD") -> str:
    """Format price with currency symbol"""
    symbols = {
        "usd": "$",
        "eur": "€",
        "gbp": "£",
        "cny": "¥",
    }
    symbol = symbols.get(currency.lower(), "$")
    return f"{symbol}{price:.2f}"


def check_subscription(handler):
    """
    Decorator to check if user has an active subscription or free messages remaining
    before allowing them to use the bot.

    If user has exceeded free limit and has no subscription, sends payment prompt.
    """

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = user.id

        # Check subscription status
        status = check_subscription_status(telegram_id)

        # Admin or subscribed users can proceed
        if status["is_admin"] or status["is_subscribed"]:
            return await handler(update, context)

        # Check if user can send message (has free messages remaining)
        if not status["can_send_message"]:
            # User has exceeded free limit - send payment prompt
            await send_payment_prompt(update, context, telegram_id)
            return

        # User has free messages remaining - proceed and increment counter
        result = await handler(update, context)

        # After processing, increment free usage counter
        new_count = increment_free_usage(telegram_id)

        # Send reminder if approaching limit
        remaining = FREE_MESSAGE_LIMIT - new_count
        if remaining == 2:
            await send_usage_reminder(update, context, remaining)
        elif remaining == 0:
            await send_limit_reached(update, context)

        return result

    return wrapper


async def send_payment_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int):
    """Send payment prompt when user exceeds free limit"""

    monthly_price = format_price(PRICING["monthly"]["price"])
    yearly_price = format_price(PRICING["yearly"]["price"])

    message = f"""
🚫 *免费额度已用完*

您已使用完 {FREE_MESSAGE_LIMIT} 次免费对话。

订阅后可享受：
✨ 无限对话次数
🤖 所有 AI 模型访问
📄 文档分析
🎨 图像生成
🌍 翻译服务

选择订阅计划：
"""

    keyboard = [
        [
            InlineKeyboardButton(
                f"💳 月付 {monthly_price}/月",
                callback_data="subscribe_monthly"
            ),
            InlineKeyboardButton(
                f"💎 年付 {yearly_price}/年 (省17%)",
                callback_data="subscribe_yearly"
            ),
        ],
        [InlineKeyboardButton("❓ 查看订阅详情", callback_data="subscription_info")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def send_usage_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, remaining: int):
    """Send reminder when user is approaching free limit"""

    message = f"""
💬 *使用提醒*

您还剩 {remaining} 次免费对话机会。

订阅后即可享受无限对话！
"""

    keyboard = [[InlineKeyboardButton("💳 查看订阅计划", callback_data="subscription_info")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def send_limit_reached(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send notification when user reaches free limit"""

    message = """
✅ *这是您的最后一次免费对话*

下次对话将需要订阅。

点击下方按钮查看订阅计划：
"""

    keyboard = [[InlineKeyboardButton("💳 立即订阅", callback_data="subscription_info")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def handle_subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription button callbacks"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    telegram_id = user.id
    callback_data = query.data

    if callback_data == "subscription_info":
        # Show subscription plans
        await show_subscription_plans(query, context, telegram_id)
    elif callback_data.startswith("subscribe_"):
        # Handle subscription selection
        plan_type = callback_data.replace("subscribe_", "")
        await initiate_subscription(query, context, telegram_id, plan_type)


async def show_subscription_plans(query, context: ContextTypes.DEFAULT_TYPE, telegram_id: int):
    """Show detailed subscription plans"""

    monthly_price = format_price(PRICING["monthly"]["price"])
    yearly_price = format_price(PRICING["yearly"]["price"])
    yearly_monthly = format_price(PRICING["yearly"]["price"] / 12)

    message = f"""
💎 *订阅计划*

📅 *月度订阅*
• 价格：{monthly_price}/月
• 无限对话次数
• 所有功能完整访问

🎁 *年度订阅* ⭐ 推荐
• 价格：{yearly_price}/年
• 相当于 {yearly_monthly}/月
• 节省 17%
• 无限对话次数
• 所有功能完整访问

✨ *包含功能：*
• 🤖 GPT-3.5, GPT-4, Gemini 模型
• 📄 文档分析（PDF, EPUB等）
• 🎨 DALL-E 3 图像生成
• 🌍 多语言翻译
• 💾 对话历史保存
• 🎯 自定义提示词

选择您的计划：
"""

    keyboard = [
        [
            InlineKeyboardButton(f"💳 月付 {monthly_price}", callback_data="subscribe_monthly"),
            InlineKeyboardButton(f"💎 年付 {yearly_price}", callback_data="subscribe_yearly"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def initiate_subscription(query, context: ContextTypes.DEFAULT_TYPE, telegram_id: int, plan_type: str):
    """Initiate the subscription process via Stripe"""

    try:
        # Create Stripe checkout session
        session = create_checkout_session(
            telegram_id=telegram_id,
            plan_type=plan_type,
        )

        plan_name = "月度" if plan_type == "monthly" else "年度"
        price = format_price(PRICING[plan_type]["price"])

        message = f"""
✅ *准备好订阅了！*

计划：{plan_name}订阅
价格：{price}

点击下方按钮前往安全支付页面：
"""

        keyboard = [
            [InlineKeyboardButton("💳 前往支付", url=session["url"])],
            [InlineKeyboardButton("❌ 取消", callback_data="cancel_payment")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

        logger.info(f"Created checkout session for telegram_id: {telegram_id}, plan: {plan_type}")

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        await query.edit_message_text(
            "❌ 抱歉，创建支付会话时出错。请稍后重试或联系管理员。"
        )


async def handle_cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment cancellation"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("❌ 已取消支付。如需订阅，请随时使用 /subscribe 命令。")
