#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Subscription management handlers

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from ..utils.subscription_operations import (
    check_subscription_status,
    get_user_subscription,
    cancel_subscription as cancel_user_subscription,
    FREE_MESSAGE_LIMIT,
)
from ..helpers.stripe_helper import (
    cancel_stripe_subscription,
    reactivate_subscription as reactivate_stripe_subscription,
    PRICING,
)
from ..helpers.subscription_check import format_price
import logging

logger = logging.getLogger(__name__)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command - show subscription plans"""
    user = update.effective_user
    telegram_id = user.id

    # Check current status
    status = check_subscription_status(telegram_id)

    if status["is_admin"]:
        await update.message.reply_text("👨‍💼 您是管理员，无需订阅即可使用所有功能。")
        return

    if status["is_subscribed"]:
        await update.message.reply_text(
            "✅ 您已经是订阅用户了！使用 /my_subscription 查看订阅详情。"
        )
        return

    # Show subscription plans
    monthly_price = format_price(PRICING["monthly"]["price"])
    yearly_price = format_price(PRICING["yearly"]["price"])
    yearly_monthly = format_price(PRICING["yearly"]["price"] / 12)

    remaining = status["free_messages_remaining"]

    message = f"""
💎 *订阅 AI 助手*

您当前还有 {remaining}/{FREE_MESSAGE_LIMIT} 次免费对话机会。

📅 *月度订阅*
• 价格：{monthly_price}/月
• 无限对话次数
• 所有功能完整访问

🎁 *年度订阅* ⭐ 推荐
• 价格：{yearly_price}/年（{yearly_monthly}/月）
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

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def my_subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_subscription command - show current subscription details"""
    user = update.effective_user
    telegram_id = user.id

    status = check_subscription_status(telegram_id)

    if status["is_admin"]:
        message = """
👨‍💼 *管理员账户*

您拥有完整的管理员权限。
✅ 无限对话次数
✅ 所有功能访问
"""
        await update.message.reply_text(message, parse_mode="Markdown")
        return

    if not status["is_subscribed"]:
        remaining = status["free_messages_remaining"]
        used = status["free_messages_used"]

        message = f"""
📊 *您的使用情况*

状态: 🆓 免费用户
已使用: {used}/{FREE_MESSAGE_LIMIT} 次对话
剩余: {remaining} 次对话

订阅后可享受无限对话！
使用 /subscribe 查看订阅计划。
"""

        keyboard = [[InlineKeyboardButton("💳 立即订阅", callback_data="subscription_info")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
        return

    # Get subscription details
    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await update.message.reply_text("❌ 无法获取订阅信息，请联系管理员。")
        return

    # Parse subscription data
    # Subscription table: id, telegramId, stripe_subscription_id, stripe_customer_id,
    #                     status, plan_type, current_period_start, current_period_end,
    #                     cancel_at_period_end, created_at, updated_at
    (sub_id, tid, stripe_sub_id, stripe_cust_id, sub_status, plan_type,
     period_start, period_end, cancel_at_end, created_at, updated_at) = subscription

    # Format dates
    end_date = datetime.fromtimestamp(period_end).strftime("%Y-%m-%d")
    start_date = datetime.fromtimestamp(period_start).strftime("%Y-%m-%d")

    # Calculate days remaining
    days_remaining = max(0, (period_end - int(datetime.now().timestamp())) // 86400)

    plan_name = "月度订阅" if plan_type == "monthly" else "年度订阅"
    auto_renew = "❌ 已关闭" if cancel_at_end else "✅ 已开启"

    message = f"""
📊 *您的订阅信息*

状态: ✅ 活跃
套餐: {plan_name}
开始时间: {start_date}
到期时间: {end_date}
剩余天数: {days_remaining} 天
自动续费: {auto_renew}

✨ 享受无限对话和所有高级功能！
"""

    keyboard = []

    if not cancel_at_end:
        keyboard.append([InlineKeyboardButton("❌ 取消自动续费", callback_data="cancel_auto_renew")])
    else:
        keyboard.append([InlineKeyboardButton("✅ 恢复自动续费", callback_data="reactivate_subscription")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def cancel_subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel_subscription command - cancel auto-renewal"""
    user = update.effective_user
    telegram_id = user.id

    status = check_subscription_status(telegram_id)

    if not status["is_subscribed"]:
        await update.message.reply_text("❌ 您当前没有活跃的订阅。")
        return

    # Get subscription
    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await update.message.reply_text("❌ 无法获取订阅信息，请联系管理员。")
        return

    stripe_sub_id = subscription[2]
    cancel_at_end = subscription[8]

    if cancel_at_end:
        await update.message.reply_text("ℹ️ 您的订阅已设置为在当前周期结束时取消。")
        return

    # Show confirmation
    message = """
⚠️ *确认取消订阅？*

取消后：
• 您的订阅将在当前周期结束时终止
• 在到期前仍可正常使用所有功能
• 到期后将恢复为免费用户（5次对话限制）

确定要取消吗？
"""

    keyboard = [
        [
            InlineKeyboardButton("✅ 确认取消", callback_data="confirm_cancel_subscription"),
            InlineKeyboardButton("❌ 保持订阅", callback_data="keep_subscription"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /usage command - show usage statistics"""
    user = update.effective_user
    telegram_id = user.id

    status = check_subscription_status(telegram_id)

    if status["is_admin"]:
        message = "👨‍💼 管理员账户 - 无限制访问"
    elif status["is_subscribed"]:
        subscription = get_user_subscription(telegram_id)
        if subscription:
            period_end = subscription[7]
            end_date = datetime.fromtimestamp(period_end).strftime("%Y-%m-%d")
            message = f"✅ 订阅用户 - 无限对话\n到期时间: {end_date}"
        else:
            message = "✅ 订阅用户 - 无限对话"
    else:
        used = status["free_messages_used"]
        remaining = status["free_messages_remaining"]
        message = f"""
📊 *使用统计*

免费额度: {used}/{FREE_MESSAGE_LIMIT} 次
剩余次数: {remaining} 次

想要无限对话？使用 /subscribe 订阅！
"""

    await update.message.reply_text(message, parse_mode="Markdown")


# Callback query handlers


async def handle_cancel_auto_renew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel auto-renew callback"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    telegram_id = user.id

    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await query.edit_message_text("❌ 无法获取订阅信息，请联系管理员。")
        return

    stripe_sub_id = subscription[2]
    period_end = subscription[7]
    end_date = datetime.fromtimestamp(period_end).strftime("%Y-%m-%d")

    # Cancel subscription in Stripe (at period end)
    success = cancel_stripe_subscription(stripe_sub_id, at_period_end=True)

    if success:
        # Update local database
        cancel_user_subscription(telegram_id, immediate=False)

        message = f"""
✅ *已取消自动续费*

您的订阅将在 {end_date} 到期。
在此之前，您仍可正常使用所有功能。

如需恢复订阅，请使用 /my_subscription 命令。
"""
        await query.edit_message_text(message, parse_mode="Markdown")
        logger.info(f"Cancelled auto-renew for telegram_id: {telegram_id}")
    else:
        await query.edit_message_text("❌ 取消订阅失败，请稍后重试或联系管理员。")


async def handle_reactivate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reactivate subscription callback"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    telegram_id = user.id

    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await query.edit_message_text("❌ 无法获取订阅信息，请联系管理员。")
        return

    stripe_sub_id = subscription[2]

    # Reactivate subscription in Stripe
    success = reactivate_stripe_subscription(stripe_sub_id)

    if success:
        # Update local database - remove cancel flag
        from ..utils.subscription_operations import update_subscription
        update_subscription(stripe_sub_id, cancel_at_period_end=0)

        message = """
✅ *已恢复自动续费*

您的订阅将自动续费，无需担心到期问题。

使用 /my_subscription 查看订阅详情。
"""
        await query.edit_message_text(message, parse_mode="Markdown")
        logger.info(f"Reactivated subscription for telegram_id: {telegram_id}")
    else:
        await query.edit_message_text("❌ 恢复订阅失败，请稍后重试或联系管理员。")


async def handle_confirm_cancel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmed subscription cancellation"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    telegram_id = user.id

    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await query.edit_message_text("❌ 无法获取订阅信息，请联系管理员。")
        return

    stripe_sub_id = subscription[2]
    period_end = subscription[7]
    end_date = datetime.fromtimestamp(period_end).strftime("%Y-%m-%d")

    # Cancel subscription
    success = cancel_stripe_subscription(stripe_sub_id, at_period_end=True)

    if success:
        cancel_user_subscription(telegram_id, immediate=False)

        message = f"""
✅ *订阅已取消*

您的订阅将在 {end_date} 到期。
感谢您的使用！

如需重新订阅，请随时使用 /subscribe 命令。
"""
        await query.edit_message_text(message, parse_mode="Markdown")
        logger.info(f"Confirmed cancel subscription for telegram_id: {telegram_id}")
    else:
        await query.edit_message_text("❌ 取消订阅失败，请稍后重试或联系管理员。")


async def handle_keep_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle keep subscription callback"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("✅ 太好了！您的订阅将继续保持活跃。")
