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
        await update.message.reply_text("👨‍💼 You are an administrator with access to all features without subscription.")
        return

    if status["is_subscribed"]:
        await update.message.reply_text(
            "✅ You are already subscribed! Use /my_subscription to view subscription details."
        )
        return

    # Show subscription plans
    monthly_price = format_price(PRICING["monthly"]["price"])
    yearly_price = format_price(PRICING["yearly"]["price"])
    yearly_monthly = format_price(PRICING["yearly"]["price"] / 12)

    remaining = status["free_messages_remaining"]

    message = f"""
💎 *Subscribe to AI Assistant*

You have {remaining}/{FREE_MESSAGE_LIMIT} free messages remaining.

📅 *Monthly Subscription*
• Price: {monthly_price}/month
• Unlimited messages
• Full access to all features

🎁 *Yearly Subscription* ⭐ Recommended
• Price: {yearly_price}/year ({yearly_monthly}/month)
• Save 17%
• Unlimited messages
• Full access to all features

✨ *Included Features:*
• 🤖 GPT-3.5, GPT-4, Gemini models
• 📄 Document analysis (PDF, EPUB, etc.)
• 🎨 DALL-E 3 image generation
• 🌍 Multi-language translation
• 💾 Conversation history
• 🎯 Custom prompts

Choose your plan:
"""

    keyboard = [
        [
            InlineKeyboardButton(f"💳 Monthly {monthly_price}", callback_data="subscribe_monthly"),
            InlineKeyboardButton(f"💎 Yearly {yearly_price}", callback_data="subscribe_yearly"),
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
👨‍💼 *Administrator Account*

You have full administrator privileges.
✅ Unlimited messages
✅ Access to all features
"""
        await update.message.reply_text(message, parse_mode="Markdown")
        return

    if not status["is_subscribed"]:
        remaining = status["free_messages_remaining"]
        used = status["free_messages_used"]

        message = f"""
📊 *Your Usage Status*

Status: 🆓 Free User
Used: {used}/{FREE_MESSAGE_LIMIT} messages
Remaining: {remaining} messages

Subscribe for unlimited messages!
Use /subscribe to view subscription plans.
"""

        keyboard = [[InlineKeyboardButton("💳 Subscribe Now", callback_data="subscription_info")]]
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
        await update.message.reply_text("❌ Unable to retrieve subscription information. Please contact administrator.")
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

    plan_name = "Monthly Subscription" if plan_type == "monthly" else "Yearly Subscription"
    auto_renew = "❌ Disabled" if cancel_at_end else "✅ Enabled"

    message = f"""
📊 *Your Subscription*

Status: ✅ Active
Plan: {plan_name}
Start Date: {start_date}
Expiration Date: {end_date}
Days Remaining: {days_remaining} days
Auto-Renewal: {auto_renew}

✨ Enjoy unlimited messages and all premium features!
"""

    keyboard = []

    if not cancel_at_end:
        keyboard.append([InlineKeyboardButton("❌ Cancel Auto-Renewal", callback_data="cancel_auto_renew")])
    else:
        keyboard.append([InlineKeyboardButton("✅ Resume Auto-Renewal", callback_data="reactivate_subscription")])

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
        await update.message.reply_text("❌ You do not have an active subscription.")
        return

    # Get subscription
    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await update.message.reply_text("❌ Unable to retrieve subscription information. Please contact administrator.")
        return

    stripe_sub_id = subscription[2]
    cancel_at_end = subscription[8]

    if cancel_at_end:
        await update.message.reply_text("ℹ️ Your subscription is already set to cancel at the end of the current period.")
        return

    # Show confirmation
    message = """
⚠️ *Confirm Cancellation?*

After cancellation:
• Your subscription will end at the end of the current period
• You can still use all features until expiration
• After expiration, you will return to free tier (5 message limit)

Are you sure you want to cancel?
"""

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm Cancellation", callback_data="confirm_cancel_subscription"),
            InlineKeyboardButton("❌ Keep Subscription", callback_data="keep_subscription"),
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
        message = "👨‍💼 Administrator Account - Unlimited Access"
    elif status["is_subscribed"]:
        subscription = get_user_subscription(telegram_id)
        if subscription:
            period_end = subscription[7]
            end_date = datetime.fromtimestamp(period_end).strftime("%Y-%m-%d")
            message = f"✅ Subscribed User - Unlimited Messages\nExpires: {end_date}"
        else:
            message = "✅ Subscribed User - Unlimited Messages"
    else:
        used = status["free_messages_used"]
        remaining = status["free_messages_remaining"]
        message = f"""
📊 *Usage Statistics*

Free Messages: {used}/{FREE_MESSAGE_LIMIT} used
Remaining: {remaining} messages

Want unlimited messages? Use /subscribe!
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
        await query.edit_message_text("❌ Unable to retrieve subscription information. Please contact administrator.")
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
✅ *Auto-Renewal Cancelled*

Your subscription will expire on {end_date}.
You can continue using all features until then.

To reactivate, use /my_subscription command.
"""
        await query.edit_message_text(message, parse_mode="Markdown")
        logger.info(f"Cancelled auto-renew for telegram_id: {telegram_id}")
    else:
        await query.edit_message_text("❌ Failed to cancel subscription. Please try again later or contact administrator.")


async def handle_reactivate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reactivate subscription callback"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    telegram_id = user.id

    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await query.edit_message_text("❌ Unable to retrieve subscription information. Please contact administrator.")
        return

    stripe_sub_id = subscription[2]

    # Reactivate subscription in Stripe
    success = reactivate_stripe_subscription(stripe_sub_id)

    if success:
        # Update local database - remove cancel flag
        from ..utils.subscription_operations import update_subscription
        update_subscription(stripe_sub_id, cancel_at_period_end=0)

        message = """
✅ *Auto-Renewal Reactivated*

Your subscription will renew automatically. No need to worry about expiration.

Use /my_subscription to view subscription details.
"""
        await query.edit_message_text(message, parse_mode="Markdown")
        logger.info(f"Reactivated subscription for telegram_id: {telegram_id}")
    else:
        await query.edit_message_text("❌ Failed to reactivate subscription. Please try again later or contact administrator.")


async def handle_confirm_cancel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmed subscription cancellation"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    telegram_id = user.id

    subscription = get_user_subscription(telegram_id)

    if not subscription:
        await query.edit_message_text("❌ Unable to retrieve subscription information. Please contact administrator.")
        return

    stripe_sub_id = subscription[2]
    period_end = subscription[7]
    end_date = datetime.fromtimestamp(period_end).strftime("%Y-%m-%d")

    # Cancel subscription
    success = cancel_stripe_subscription(stripe_sub_id, at_period_end=True)

    if success:
        cancel_user_subscription(telegram_id, immediate=False)

        message = f"""
✅ *Subscription Cancelled*

Your subscription will expire on {end_date}.
Thank you for using our service!

To resubscribe anytime, use /subscribe command.
"""
        await query.edit_message_text(message, parse_mode="Markdown")
        logger.info(f"Confirmed cancel subscription for telegram_id: {telegram_id}")
    else:
        await query.edit_message_text("❌ Failed to cancel subscription. Please try again later or contact administrator.")


async def handle_keep_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle keep subscription callback"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("✅ Great! Your subscription will remain active.")
