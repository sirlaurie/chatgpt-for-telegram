#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stripe Webhook Server

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
import os
import logging
import asyncio
import time
from telegram import Bot
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Import project modules
from src.helpers.stripe_helper import verify_webhook_signature
from src.utils.subscription_operations import (
    create_subscription,
    update_subscription,
    record_payment,
    get_subscription_by_stripe_id,
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_CANCELED,
    SUBSCRIPTION_STATUS_EXPIRED,
)
from src.utils._db import DBClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("webhook_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Bot Webhook Server")

# Initialize Telegram Bot
bot_token = os.environ.get("bot_token")
bot = Bot(token=bot_token) if bot_token else None

db_client = DBClient()


async def send_telegram_notification(telegram_id: int, message: str):
    """Send a notification message to a Telegram user"""
    if not bot:
        logger.error("Bot not initialized, cannot send notification")
        return

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="Markdown",
        )
        logger.info(f"Sent notification to telegram_id: {telegram_id}")
    except Exception as e:
        logger.error(f"Error sending notification to {telegram_id}: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "telegram-bot-webhook"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/test-simple", response_class=HTMLResponse)
async def test_simple():
    """Ultra simple test page for mobile debugging"""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Test</title>
</head>
<body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; text-align: center;">
    <h1>✅ Test Page</h1>
    <p>If you can see this, the basic HTML works!</p>
    <p style="color: green; font-size: 18px;">Success!</p>
</body>
</html>"""


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events

    Supported events:
    - checkout.session.completed: Payment successful, create subscription
    - invoice.payment_succeeded: Recurring payment successful
    - invoice.payment_failed: Payment failed
    - customer.subscription.updated: Subscription updated
    - customer.subscription.deleted: Subscription cancelled
    """

    # Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    # Verify webhook signature
    event = verify_webhook_signature(payload, signature)

    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    event_data = event["data"]["object"]

    logger.info(f"Received webhook event: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(event_data)

        elif event_type == "invoice.payment_succeeded":
            await handle_payment_succeeded(event_data)

        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(event_data)

        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event_data)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event_data)

        else:
            logger.info(f"Unhandled event type: {event_type}")

        return JSONResponse({"status": "success"})

    except Exception as e:
        logger.error(f"Error handling webhook event {event_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_checkout_completed(session_data):
    """Handle successful checkout session"""
    logger.info("Processing checkout.session.completed")

    # Extract data
    telegram_id = int(session_data["metadata"]["telegram_id"])
    plan_type = session_data["metadata"]["plan_type"]
    customer_id = session_data["customer"]
    subscription_id = session_data.get("subscription")

    if not subscription_id:
        logger.error("No subscription ID in checkout session")
        return

    # Get subscription details from Stripe
    import stripe
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    subscription = stripe.Subscription.retrieve(subscription_id)

    # Extract subscription period safely
    # Note: Subscription object may not have current_period_start/end directly
    # We need to calculate from billing_cycle_anchor or use created + 1 month/year
    try:
        # Try to get current_period_start and current_period_end directly
        current_period_start = getattr(subscription, 'current_period_start', None)
        current_period_end = getattr(subscription, 'current_period_end', None)

        # If not available, use alternative fields
        if not current_period_start:
            # Use start_date or created as fallback
            current_period_start = subscription.get('start_date') or subscription.get('created')
            logger.info(f"Using start_date/created as current_period_start: {current_period_start}")

        if not current_period_end:
            # Calculate end date based on plan interval
            start_dt = datetime.fromtimestamp(current_period_start)

            if plan_type == "yearly":
                end_dt = start_dt + relativedelta(years=1)
            else:  # monthly
                end_dt = start_dt + relativedelta(months=1)

            current_period_end = int(end_dt.timestamp())
            logger.info(f"Calculated current_period_end: {current_period_end}")

    except Exception as e:
        logger.error(f"Error accessing subscription fields: {e}")
        logger.error(f"Subscription object type: {type(subscription)}")
        logger.error(f"Subscription keys: {list(subscription.keys()) if hasattr(subscription, 'keys') else 'N/A'}")
        logger.error("Failed to extract subscription period, aborting")
        return

    # Create subscription in database
    create_subscription(
        telegram_id=telegram_id,
        stripe_subscription_id=subscription_id,
        stripe_customer_id=customer_id,
        plan_type=plan_type,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
    )

    # Record payment
    amount = session_data.get("amount_total", 0) / 100  # Convert from cents
    currency = session_data.get("currency", "usd").upper()

    record_payment(
        telegram_id=telegram_id,
        stripe_payment_id=session_data["payment_intent"],
        stripe_subscription_id=subscription_id,
        amount=amount,
        currency=currency,
        status="succeeded",
        payment_type=plan_type,
    )

    # Send notification to user
    plan_name = "Monthly" if plan_type == "monthly" else "Yearly"
    end_date = datetime.fromtimestamp(current_period_end).strftime("%Y-%m-%d")

    message = f"""
🎉 *Subscription Successful!*

Thank you for subscribing!

Plan: {plan_name} Subscription
Expires: {end_date}

✅ You now have unlimited access to all features!

• 🤖 All AI Models
• 📄 Document Analysis
• 🎨 Image Generation
• 🌍 Translation Services

Start chatting!
"""

    await send_telegram_notification(telegram_id, message)

    logger.info(f"Subscription created for telegram_id: {telegram_id}, plan: {plan_type}")


async def handle_payment_succeeded(invoice_data):
    """Handle successful recurring payment"""
    logger.info("Processing invoice.payment_succeeded")

    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        # This might be a one-time payment, skip
        return

    # Get subscription from database
    subscription = get_subscription_by_stripe_id(subscription_id)

    if not subscription:
        logger.warning(f"Subscription not found in database: {subscription_id}")
        return

    telegram_id = subscription[1]
    created_at = subscription[9]  # created_at timestamp
    now = int(time.time())

    # Skip if this is the first payment (subscription created within last 60 seconds)
    # checkout.session.completed already handled the initial setup with correct periods
    if now - created_at < 60:
        logger.info(f"Skipping period update for newly created subscription: {subscription_id}")
        return

    # Update subscription period (only for recurring payments, not first payment)
    update_subscription(
        stripe_subscription_id=subscription_id,
        current_period_start=invoice_data["period_start"],
        current_period_end=invoice_data["period_end"],
        status=SUBSCRIPTION_STATUS_ACTIVE,
    )

    # Record payment
    amount = invoice_data.get("amount_paid", 0) / 100
    currency = invoice_data.get("currency", "usd").upper()

    record_payment(
        telegram_id=telegram_id,
        stripe_payment_id=invoice_data.get("payment_intent"),
        stripe_subscription_id=subscription_id,
        amount=amount,
        currency=currency,
        status="succeeded",
        payment_type=subscription[5],  # plan_type
    )

    # Send notification
    end_date = datetime.fromtimestamp(invoice_data["period_end"]).strftime("%Y-%m-%d")

    message = f"""
✅ *Subscription Renewed*

Your subscription has been successfully renewed!

Expires: {end_date}
Amount Paid: ${amount:.2f} {currency}

Thank you for your continued support!
"""

    await send_telegram_notification(telegram_id, message)

    logger.info(f"Payment succeeded for telegram_id: {telegram_id}")


async def handle_payment_failed(invoice_data):
    """Handle failed payment"""
    logger.info("Processing invoice.payment_failed")

    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        return

    subscription = get_subscription_by_stripe_id(subscription_id)

    if not subscription:
        return

    telegram_id = subscription[1]

    # Send notification
    message = """
⚠️ *Payment Failed*

Your subscription renewal failed.

Please check your payment method and update your payment information.
If the problem persists, please contact support.

Use /my_subscription to view your subscription status.
"""

    await send_telegram_notification(telegram_id, message)

    logger.warning(f"Payment failed for telegram_id: {telegram_id}")


async def handle_subscription_updated(subscription_data):
    """Handle subscription update"""
    logger.info("Processing customer.subscription.updated")

    subscription_id = subscription_data["id"]

    subscription = get_subscription_by_stripe_id(subscription_id)

    if not subscription:
        logger.warning(f"Subscription not found: {subscription_id}")
        return

    # Update subscription
    update_subscription(
        stripe_subscription_id=subscription_id,
        status=subscription_data["status"],
        current_period_start=subscription_data["current_period_start"],
        current_period_end=subscription_data["current_period_end"],
        cancel_at_period_end=1 if subscription_data.get("cancel_at_period_end") else 0,
    )

    logger.info(f"Subscription updated: {subscription_id}, status: {subscription_data['status']}")


async def handle_subscription_deleted(subscription_data):
    """Handle subscription cancellation"""
    logger.info("Processing customer.subscription.deleted")

    subscription_id = subscription_data["id"]

    subscription = get_subscription_by_stripe_id(subscription_id)

    if not subscription:
        logger.warning(f"Subscription not found: {subscription_id}")
        return

    telegram_id = subscription[1]

    # Update subscription to canceled
    update_subscription(
        stripe_subscription_id=subscription_id,
        status=SUBSCRIPTION_STATUS_CANCELED,
    )

    # Update user status
    db_client.update_record(
        "User",
        telegram_id,
        {"subscription_status": SUBSCRIPTION_STATUS_CANCELED},
    )

    # Send notification
    message = """
ℹ️ *Subscription Cancelled*

Your subscription has expired and been cancelled.

You are now a free user with 5 free messages.

To continue using all features, use /subscribe to resubscribe.

Thank you for using our service!
"""

    await send_telegram_notification(telegram_id, message)

    logger.info(f"Subscription deleted for telegram_id: {telegram_id}")


# Payment success/cancel pages


@app.get("/payment/success", response_class=HTMLResponse)
async def payment_success(session_id: str = None):
    """Payment success page"""
    # Simplified HTML without complex gradients and animations for better mobile compatibility
    session_display = f'<p style="font-size: 12px; color: #999; margin-top: 20px;">Session: {session_id}</p>' if session_id else ''

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Successful</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            background-color: #6366f1;
            color: #1f2937;
            text-align: center;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            padding: 40px 20px;
            max-width: 400px;
            margin: 40px auto;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #1f2937;
            font-size: 24px;
            margin: 0 0 15px 0;
        }}
        p {{
            color: #4b5563;
            font-size: 16px;
            line-height: 1.5;
            margin: 10px 0;
        }}
        .info {{
            background: #f3f4f6;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            background: #6366f1;
            color: white;
            padding: 12px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🎉</div>
        <h1>Payment Successful!</h1>
        <p>Thank you for subscribing!<br>Your payment has been successfully processed.</p>
        <div class="info">
            ✅ Subscription Activated<br>
            📱 Please return to Telegram to view your subscription status
        </div>
        <a href="tg://" class="button">Return to Telegram</a>
        {session_display}
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.get("/payment/cancel", response_class=HTMLResponse)
async def payment_cancel():
    """Payment cancel page"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Cancelled</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            background-color: #ef4444;
            color: #1f2937;
            text-align: center;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 40px 20px;
            max-width: 400px;
            margin: 40px auto;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #1f2937;
            font-size: 24px;
            margin: 0 0 15px 0;
        }
        p {
            color: #4b5563;
            font-size: 16px;
            line-height: 1.5;
            margin: 10px 0;
        }
        .info {
            background: #f3f4f6;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            font-size: 14px;
        }
        .button {
            display: inline-block;
            background: #ef4444;
            color: white;
            padding: 12px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">😔</div>
        <h1>Payment Cancelled</h1>
        <p>Your payment has been cancelled. No charges were made.</p>
        <div class="info">
            💡 Use /subscribe command<br>to start the subscription process again
        </div>
        <a href="tg://" class="button">Return to Telegram</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.environ.get("WEBHOOK_PORT", 8000))
    host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")

    logger.info(f"Starting webhook server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
