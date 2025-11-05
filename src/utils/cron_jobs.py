#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Scheduled cron jobs for subscription management

import logging
import asyncio
import os
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .subscription_operations import (
    update_expired_subscriptions,
    get_expiring_subscriptions,
    get_expired_subscriptions,
)
from ..helpers.stripe_helper import get_subscription as get_stripe_subscription

logger = logging.getLogger(__name__)


class SubscriptionCronJobs:
    """Manages scheduled tasks for subscription management"""

    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """Start all scheduled jobs"""
        # Daily job at midnight - check and update expired subscriptions
        self.scheduler.add_job(
            self.check_expired_subscriptions,
            CronTrigger(hour=0, minute=0),
            id="check_expired_subscriptions",
            name="Check expired subscriptions daily",
            replace_existing=True,
        )

        # Daily job at 10 AM - send expiration reminders
        self.scheduler.add_job(
            self.send_expiration_reminders,
            CronTrigger(hour=10, minute=0),
            id="send_expiration_reminders",
            name="Send subscription expiration reminders",
            replace_existing=True,
        )

        # Hourly job - sync with Stripe
        self.scheduler.add_job(
            self.sync_stripe_subscriptions,
            CronTrigger(minute=0),  # Every hour at minute 0
            id="sync_stripe_subscriptions",
            name="Sync Stripe subscription status",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Subscription cron jobs started")

    def stop(self):
        """Stop all scheduled jobs"""
        self.scheduler.shutdown()
        logger.info("Subscription cron jobs stopped")

    async def check_expired_subscriptions(self):
        """Check and update expired subscriptions"""
        logger.info("Running check_expired_subscriptions job")

        try:
            # Get expired subscriptions
            expired = get_expired_subscriptions()

            if not expired:
                logger.info("No expired subscriptions found")
                return

            logger.info(f"Found {len(expired)} expired subscriptions")

            # Update status in database
            updated_count = update_expired_subscriptions()

            # Send notifications to users
            for subscription in expired:
                telegram_id = subscription[1]  # telegramId
                await self.send_expiration_notification(telegram_id)

            logger.info(f"Updated {updated_count} expired subscriptions")

        except Exception as e:
            logger.error(f"Error in check_expired_subscriptions: {str(e)}")

    async def send_expiration_reminders(self):
        """Send reminders for subscriptions expiring soon (within 3 days)"""
        logger.info("Running send_expiration_reminders job")

        try:
            # Get subscriptions expiring in 3 days
            expiring = get_expiring_subscriptions(days=3)

            if not expiring:
                logger.info("No expiring subscriptions found")
                return

            logger.info(f"Found {len(expiring)} expiring subscriptions")

            for subscription in expiring:
                telegram_id = subscription[1]  # telegramId
                period_end = subscription[7]  # current_period_end
                end_date = datetime.fromtimestamp(period_end).strftime("%Y-%m-%d")
                days_remaining = (period_end - int(datetime.now().timestamp())) // 86400

                await self.send_reminder_notification(telegram_id, end_date, days_remaining)

            logger.info(f"Sent {len(expiring)} expiration reminders")

        except Exception as e:
            logger.error(f"Error in send_expiration_reminders: {str(e)}")

    async def sync_stripe_subscriptions(self):
        """Sync subscription status with Stripe"""
        logger.info("Running sync_stripe_subscriptions job")

        try:
            from .subscription_operations import client, SUBSCRIPTION_STATUS_ACTIVE

            # Get all active subscriptions
            subscriptions = client.query("Subscription", "status", SUBSCRIPTION_STATUS_ACTIVE)

            if not subscriptions:
                logger.info("No active subscriptions to sync")
                return

            logger.info(f"Syncing {len(subscriptions)} active subscriptions with Stripe")

            synced_count = 0
            for subscription in subscriptions:
                stripe_sub_id = subscription[2]  # stripe_subscription_id

                # Get latest status from Stripe
                stripe_data = get_stripe_subscription(stripe_sub_id)

                if not stripe_data:
                    logger.warning(f"Could not fetch Stripe subscription: {stripe_sub_id}")
                    continue

                # Check if status changed
                local_status = subscription[4]  # status
                stripe_status = stripe_data["status"]

                if local_status != stripe_status:
                    logger.info(f"Subscription {stripe_sub_id} status changed: {local_status} -> {stripe_status}")

                    # Update local database
                    from .subscription_operations import update_subscription
                    update_subscription(
                        stripe_subscription_id=stripe_sub_id,
                        status=stripe_status,
                        current_period_start=stripe_data["current_period_start"],
                        current_period_end=stripe_data["current_period_end"],
                        cancel_at_period_end=1 if stripe_data["cancel_at_period_end"] else 0,
                    )
                    synced_count += 1

            logger.info(f"Synced {synced_count} subscription status changes")

        except Exception as e:
            logger.error(f"Error in sync_stripe_subscriptions: {str(e)}")

    async def send_expiration_notification(self, telegram_id: int):
        """Send notification when subscription expires"""
        message = """
ℹ️ *订阅已到期*

您的订阅已到期。

您现在恢复为免费用户，每天有 5 次对话机会。

如需继续使用所有功能，请使用 /subscribe 重新订阅。

感谢您的使用！
"""

        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown",
            )
            logger.info(f"Sent expiration notification to {telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send expiration notification to {telegram_id}: {str(e)}")

    async def send_reminder_notification(self, telegram_id: int, end_date: str, days_remaining: int):
        """Send reminder notification for expiring subscription"""
        message = f"""
⏰ *订阅即将到期提醒*

您的订阅将在 {days_remaining} 天后到期。

到期时间: {end_date}

如果您已开启自动续费，无需任何操作。
如果您已取消自动续费，可以使用 /my_subscription 重新开启。

感谢您的支持！
"""

        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown",
            )
            logger.info(f"Sent reminder notification to {telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder notification to {telegram_id}: {str(e)}")


# Standalone function to run cron jobs
def start_cron_jobs():
    """Start subscription cron jobs"""
    bot_token = os.environ.get("bot_token")

    if not bot_token:
        logger.error("bot_token not found in environment variables")
        return None

    jobs = SubscriptionCronJobs(bot_token)
    jobs.start()

    return jobs


if __name__ == "__main__":
    # For testing purposes
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    jobs = start_cron_jobs()

    if jobs:
        print("Cron jobs started. Press Ctrl+C to stop.")
        try:
            # Keep the script running
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print("\nStopping cron jobs...")
            jobs.stop()
