#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stripe integration helper

import os
import stripe
from typing import Optional, Dict, Any
import logging

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Pricing configuration
PRICING = {
    "monthly": {
        "price": 9.99,
        "currency": "usd",
        "interval": "month",
        "description": "Monthly unlimited conversations",
        "description_zh": "每月无限对话",
    },
    "yearly": {
        "price": 99.99,
        "currency": "usd",
        "interval": "year",
        "description": "Yearly unlimited conversations (Save 17%)",
        "description_zh": "每年无限对话（节省17%）",
    },
}

logger = logging.getLogger(__name__)


def create_or_get_customer(telegram_id: int, email: Optional[str] = None, name: Optional[str] = None) -> str:
    """
    Create a new Stripe customer or retrieve existing one

    Args:
        telegram_id: Telegram user ID
        email: User's email (optional)
        name: User's name (optional)

    Returns:
        Stripe customer ID
    """
    try:
        # Check if customer already exists by metadata
        customers = stripe.Customer.list(limit=1, email=email) if email else None

        if customers and len(customers.data) > 0:
            customer = customers.data[0]
            logger.info(f"Found existing Stripe customer: {customer.id} for telegram_id: {telegram_id}")
            return customer.id

        # Create new customer
        customer_data = {
            "metadata": {"telegram_id": str(telegram_id)},
        }

        if email:
            customer_data["email"] = email
        if name:
            customer_data["name"] = name

        customer = stripe.Customer.create(**customer_data)
        logger.info(f"Created new Stripe customer: {customer.id} for telegram_id: {telegram_id}")

        return customer.id

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating customer: {str(e)}")
        raise


def create_checkout_session(
    telegram_id: int,
    plan_type: str,
    customer_id: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Stripe Checkout session for subscription

    Args:
        telegram_id: Telegram user ID
        plan_type: 'monthly' or 'yearly'
        customer_id: Existing Stripe customer ID (optional)
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect after cancelled payment

    Returns:
        Dictionary with checkout session details (id, url)
    """
    if plan_type not in PRICING:
        raise ValueError(f"Invalid plan type: {plan_type}")

    try:
        # Create or get customer
        if not customer_id:
            customer_id = create_or_get_customer(telegram_id)

        pricing = PRICING[plan_type]

        # Set default URLs if not provided
        webhook_base = os.environ.get("WEBHOOK_BASE_URL", "https://yourdomain.com")
        if not success_url:
            success_url = f"{webhook_base}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        if not cancel_url:
            cancel_url = f"{webhook_base}/payment/cancel"

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": pricing["currency"],
                        "product_data": {
                            "name": f"{plan_type.capitalize()} Subscription",
                            "description": pricing["description"],
                        },
                        "unit_amount": int(pricing["price"] * 100),  # Amount in cents
                        "recurring": {
                            "interval": pricing["interval"],
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "telegram_id": str(telegram_id),
                "plan_type": plan_type,
            },
            subscription_data={
                "metadata": {
                    "telegram_id": str(telegram_id),
                    "plan_type": plan_type,
                }
            },
        )

        logger.info(f"Created checkout session: {session.id} for telegram_id: {telegram_id}, plan: {plan_type}")

        return {
            "id": session.id,
            "url": session.url,
            "customer_id": customer_id,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise


def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a subscription from Stripe

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        Subscription data dictionary or None
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "customer_id": subscription.customer,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error retrieving subscription: {str(e)}")
        return None


def cancel_stripe_subscription(subscription_id: str, at_period_end: bool = True) -> bool:
    """
    Cancel a Stripe subscription

    Args:
        subscription_id: Stripe subscription ID
        at_period_end: If True, cancel at end of billing period. If False, cancel immediately.

    Returns:
        True if successful, False otherwise
    """
    try:
        if at_period_end:
            # Cancel at period end
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
            )
        else:
            # Cancel immediately
            subscription = stripe.Subscription.delete(subscription_id)

        logger.info(f"Cancelled subscription: {subscription_id}, at_period_end: {at_period_end}")
        return True

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error cancelling subscription: {str(e)}")
        return False


def reactivate_subscription(subscription_id: str) -> bool:
    """
    Reactivate a subscription that was set to cancel at period end

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        True if successful, False otherwise
    """
    try:
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False,
        )
        logger.info(f"Reactivated subscription: {subscription_id}")
        return True

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error reactivating subscription: {str(e)}")
        return False


def create_refund(payment_intent_id: str, amount: Optional[int] = None) -> bool:
    """
    Create a refund for a payment

    Args:
        payment_intent_id: Stripe payment intent ID
        amount: Amount to refund in cents (optional, defaults to full refund)

    Returns:
        True if successful, False otherwise
    """
    try:
        refund_data = {"payment_intent": payment_intent_id}
        if amount:
            refund_data["amount"] = amount

        refund = stripe.Refund.create(**refund_data)
        logger.info(f"Created refund: {refund.id} for payment: {payment_intent_id}")
        return True

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating refund: {str(e)}")
        return False


def verify_webhook_signature(payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
    """
    Verify Stripe webhook signature

    Args:
        payload: Raw request body
        signature: Stripe signature header

    Returns:
        Event dictionary if valid, None otherwise
    """
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        return None

    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        return event
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return None
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        return None


def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get customer details from Stripe"""
    try:
        customer = stripe.Customer.retrieve(customer_id)
        return {
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "metadata": customer.metadata,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error retrieving customer: {str(e)}")
        return None


def list_customer_subscriptions(customer_id: str) -> list:
    """List all subscriptions for a customer"""
    try:
        subscriptions = stripe.Subscription.list(customer=customer_id, limit=10)
        return subscriptions.data
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error listing subscriptions: {str(e)}")
        return []
