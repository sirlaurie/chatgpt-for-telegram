#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Subscription management operations

from typing import Optional, Tuple, Dict, Union
import time
from ._db import DBClient

client = DBClient()

# Subscription status constants
SUBSCRIPTION_STATUS_FREE = "free"
SUBSCRIPTION_STATUS_ACTIVE = "active"
SUBSCRIPTION_STATUS_EXPIRED = "expired"
SUBSCRIPTION_STATUS_CANCELED = "canceled"

# Plan types
PLAN_TYPE_MONTHLY = "monthly"
PLAN_TYPE_YEARLY = "yearly"

# Free message limit
FREE_MESSAGE_LIMIT = 5


def check_subscription_status(telegram_id: int) -> Dict[str, Union[str, int, bool]]:
    """
    Check user's subscription status and usage

    Returns:
        dict with keys:
        - is_subscribed: bool
        - subscription_status: str (free/active/expired/canceled)
        - free_messages_used: int
        - free_messages_remaining: int
        - can_send_message: bool
        - subscription_end_date: int or None
        - is_admin: bool
    """
    user = client.select_record(table="User", telegram_id=telegram_id)

    if not user:
        return {
            "is_subscribed": False,
            "subscription_status": SUBSCRIPTION_STATUS_FREE,
            "free_messages_used": 0,
            "free_messages_remaining": FREE_MESSAGE_LIMIT,
            "can_send_message": True,
            "subscription_end_date": None,
            "is_admin": False,
        }

    # Parse user data - adjusted for new columns
    # User table: role, nickname, telegramId, allow, premium, waiting,
    #             free_messages_used, subscription_status, subscription_type,
    #             subscription_start_date, subscription_end_date, stripe_customer_id, last_message_date
    (role, nickname, tid, allow, premium, waiting,
     free_messages_used, subscription_status, subscription_type,
     subscription_start_date, subscription_end_date, stripe_customer_id, last_message_date) = user

    # Check if admin (admins have free unlimited access)
    is_admin = role == "admin" or telegram_id == int(os.environ.get("DEVELOPER_CHAT_ID", 0))

    if is_admin:
        return {
            "is_subscribed": True,
            "subscription_status": "admin",
            "free_messages_used": 0,
            "free_messages_remaining": 999999,
            "can_send_message": True,
            "subscription_end_date": None,
            "is_admin": True,
        }

    # Default values if None
    free_messages_used = free_messages_used or 0
    subscription_status = subscription_status or SUBSCRIPTION_STATUS_FREE

    # Check if subscription is active and not expired
    is_subscribed = False
    if subscription_status == SUBSCRIPTION_STATUS_ACTIVE and subscription_end_date:
        if subscription_end_date > int(time.time()):
            is_subscribed = True
        else:
            # Subscription expired, update status
            subscription_status = SUBSCRIPTION_STATUS_EXPIRED
            client.update_column("User", telegram_id, "subscription_status", SUBSCRIPTION_STATUS_EXPIRED)

    # Determine if user can send message
    can_send_message = is_subscribed or (free_messages_used < FREE_MESSAGE_LIMIT)

    free_messages_remaining = max(0, FREE_MESSAGE_LIMIT - free_messages_used)

    return {
        "is_subscribed": is_subscribed,
        "subscription_status": subscription_status,
        "free_messages_used": free_messages_used,
        "free_messages_remaining": free_messages_remaining,
        "can_send_message": can_send_message,
        "subscription_end_date": subscription_end_date,
        "is_admin": is_admin,
    }


def increment_free_usage(telegram_id: int) -> int:
    """
    Increment the free message usage counter

    Returns:
        Current free_messages_used count
    """
    current_count = client.get_column_value("User", telegram_id, "free_messages_used") or 0
    new_count = current_count + 1

    client.update_column("User", telegram_id, "free_messages_used", new_count)
    client.update_column("User", telegram_id, "last_message_date", int(time.time()))

    return new_count


def create_subscription(
    telegram_id: int,
    stripe_subscription_id: str,
    stripe_customer_id: str,
    plan_type: str,
    current_period_start: int,
    current_period_end: int,
) -> None:
    """Create a new subscription record"""
    now = int(time.time())

    # Insert into Subscription table
    client.insert_record(
        table="Subscription",
        data={
            "telegramId": telegram_id,
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_customer_id": stripe_customer_id,
            "status": SUBSCRIPTION_STATUS_ACTIVE,
            "plan_type": plan_type,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "cancel_at_period_end": 0,
            "created_at": now,
            "updated_at": now,
        },
    )

    # Update User table
    client.update_record(
        table="User",
        telegram_id=telegram_id,
        data={
            "subscription_status": SUBSCRIPTION_STATUS_ACTIVE,
            "subscription_type": plan_type,
            "subscription_start_date": current_period_start,
            "subscription_end_date": current_period_end,
            "stripe_customer_id": stripe_customer_id,
        },
    )


def update_subscription(
    stripe_subscription_id: str,
    status: Optional[str] = None,
    current_period_start: Optional[int] = None,
    current_period_end: Optional[int] = None,
    cancel_at_period_end: Optional[int] = None,
) -> None:
    """Update an existing subscription"""
    # Get the subscription
    subscriptions = client.query("Subscription", "stripe_subscription_id", stripe_subscription_id)

    if not subscriptions:
        return

    subscription = subscriptions[0]
    telegram_id = subscription[1]  # telegramId is the second column

    # Prepare update data
    update_data = {"updated_at": int(time.time())}

    if status is not None:
        update_data["status"] = status
    if current_period_start is not None:
        update_data["current_period_start"] = current_period_start
    if current_period_end is not None:
        update_data["current_period_end"] = current_period_end
    if cancel_at_period_end is not None:
        update_data["cancel_at_period_end"] = cancel_at_period_end

    # Update Subscription table
    sql = f"UPDATE Subscription SET {', '.join([f'{k} = ?' for k in update_data.keys()])} WHERE stripe_subscription_id = ?"
    params = tuple(update_data.values()) + (stripe_subscription_id,)
    client.execute_query(sql, params)

    # Update User table
    user_update_data = {}
    if status is not None:
        user_update_data["subscription_status"] = status
    if current_period_end is not None:
        user_update_data["subscription_end_date"] = current_period_end

    if user_update_data:
        client.update_record("User", telegram_id, user_update_data)


def cancel_subscription(telegram_id: int, immediate: bool = False) -> bool:
    """
    Cancel a user's subscription

    Args:
        telegram_id: User's telegram ID
        immediate: If True, cancel immediately. If False, cancel at period end.

    Returns:
        True if successful, False if no active subscription found
    """
    # Get user's subscription
    subscriptions = client.query("Subscription", "telegramId", telegram_id)

    active_subscriptions = [s for s in subscriptions if s[4] == SUBSCRIPTION_STATUS_ACTIVE]  # status is 5th column

    if not active_subscriptions:
        return False

    subscription = active_subscriptions[0]
    stripe_subscription_id = subscription[2]  # stripe_subscription_id is 3rd column

    if immediate:
        # Cancel immediately
        update_subscription(
            stripe_subscription_id=stripe_subscription_id,
            status=SUBSCRIPTION_STATUS_CANCELED,
            cancel_at_period_end=1,
        )
        # Update user status
        client.update_record(
            "User",
            telegram_id,
            {"subscription_status": SUBSCRIPTION_STATUS_CANCELED},
        )
    else:
        # Cancel at period end
        update_subscription(
            stripe_subscription_id=stripe_subscription_id,
            cancel_at_period_end=1,
        )

    return True


def record_payment(
    telegram_id: int,
    stripe_payment_id: str,
    stripe_subscription_id: Optional[str],
    amount: float,
    currency: str,
    status: str,
    payment_type: str,
) -> None:
    """Record a payment transaction"""
    now = int(time.time())

    client.insert_record(
        table="Payment",
        data={
            "telegramId": telegram_id,
            "stripe_payment_id": stripe_payment_id,
            "stripe_subscription_id": stripe_subscription_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "payment_type": payment_type,
            "created_at": now,
            "updated_at": now,
        },
    )


def get_user_subscription(telegram_id: int) -> Optional[Tuple]:
    """Get user's active subscription details"""
    subscriptions = client.query("Subscription", "telegramId", telegram_id)

    active_subscriptions = [s for s in subscriptions if s[4] == SUBSCRIPTION_STATUS_ACTIVE]

    return active_subscriptions[0] if active_subscriptions else None


def get_subscription_by_stripe_id(stripe_subscription_id: str) -> Optional[Tuple]:
    """Get subscription by Stripe subscription ID"""
    subscriptions = client.query("Subscription", "stripe_subscription_id", stripe_subscription_id)
    return subscriptions[0] if subscriptions else None


def get_user_payments(telegram_id: int) -> list:
    """Get all payments for a user"""
    return client.query("Payment", "telegramId", telegram_id)


def get_expiring_subscriptions(days: int = 3) -> list:
    """Get subscriptions expiring within N days"""
    now = int(time.time())
    expiry_threshold = now + (days * 24 * 60 * 60)

    sql = """
        SELECT * FROM Subscription
        WHERE status = ?
        AND current_period_end > ?
        AND current_period_end <= ?
        AND cancel_at_period_end = 0
    """
    return client.execute_query(sql, (SUBSCRIPTION_STATUS_ACTIVE, now, expiry_threshold))


def get_expired_subscriptions() -> list:
    """Get all expired subscriptions that are still marked as active"""
    now = int(time.time())

    sql = """
        SELECT * FROM Subscription
        WHERE status = ?
        AND current_period_end < ?
    """
    return client.execute_query(sql, (SUBSCRIPTION_STATUS_ACTIVE, now))


def update_expired_subscriptions() -> int:
    """Update all expired subscriptions to expired status. Returns count of updated subscriptions."""
    expired = get_expired_subscriptions()
    count = 0

    for subscription in expired:
        stripe_subscription_id = subscription[2]
        telegram_id = subscription[1]

        update_subscription(stripe_subscription_id=stripe_subscription_id, status=SUBSCRIPTION_STATUS_EXPIRED)
        client.update_record("User", telegram_id, {"subscription_status": SUBSCRIPTION_STATUS_EXPIRED})
        count += 1

    return count


# Import os for admin check
import os
