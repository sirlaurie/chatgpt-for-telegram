#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Subscription check decorator

from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..utils.subscription_operations import (
    check_subscription_status,
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
    Decorator to check if user has an active subscription before allowing them to use the bot.

    If user has no subscription, sends payment prompt.
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

        # User has no subscription - send payment prompt
        await send_payment_prompt(update, context, telegram_id)
        return

    return wrapper


async def send_payment_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int):
    """Send payment prompt to non-subscribed users"""

    monthly_price = format_price(PRICING["monthly"]["price"])
    yearly_price = format_price(PRICING["yearly"]["price"])

    message = f"""
🔒 *Subscription Required*

Please subscribe to use this bot.

Subscribe to enjoy:
✨ Unlimited messages
🤖 All AI model access
📄 Document analysis
🎨 Image generation
🌍 Translation services

Choose a subscription plan:
"""

    keyboard = [
        [
            InlineKeyboardButton(
                f"💳 Monthly {monthly_price}",
                callback_data="subscribe_monthly"
            ),
            InlineKeyboardButton(
                f"💎 Yearly {yearly_price} (Save 17%)",
                callback_data="subscribe_yearly"
            ),
        ],
        [InlineKeyboardButton("❓ View Details", callback_data="subscription_info")],
    ]

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
💎 *Subscription Plans*

📅 *Monthly Subscription*
• Price: {monthly_price}/month
• Unlimited messages
• Full access to all features

🎁 *Yearly Subscription* ⭐ Recommended
• Price: {yearly_price}/year
• Equivalent to {yearly_monthly}/month
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

        plan_name = "Monthly" if plan_type == "monthly" else "Yearly"
        price = format_price(PRICING[plan_type]["price"])

        message = f"""
✅ *Ready to Subscribe!*

Plan: {plan_name} Subscription
Price: {price}

Click below to proceed to secure payment:
"""

        keyboard = [
            [InlineKeyboardButton("💳 Proceed to Payment", url=session["url"])],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")],
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
            "❌ Sorry, an error occurred while creating payment session. Please try again later or contact administrator."
        )


async def handle_cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment cancellation"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("❌ Payment cancelled. To subscribe, use /subscribe command anytime.")
