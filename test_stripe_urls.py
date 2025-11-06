#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test script to check Stripe checkout URLs

import os
import sys

# Print current environment variables
print("=" * 60)
print("Current Environment Variables:")
print("=" * 60)
print(f"WEBHOOK_BASE_URL: {os.environ.get('WEBHOOK_BASE_URL', 'NOT SET (will use default)')}")
print(f"WEBHOOK_PORT: {os.environ.get('WEBHOOK_PORT', 'NOT SET')}")
print(f"WEBHOOK_HOST: {os.environ.get('WEBHOOK_HOST', 'NOT SET')}")
print(f"STRIPE_SECRET_KEY: {os.environ.get('STRIPE_SECRET_KEY', 'NOT SET')[:15] + '...' if os.environ.get('STRIPE_SECRET_KEY') else 'NOT SET'}")
print()

# Simulate what stripe_helper.py does
webhook_base = os.environ.get("WEBHOOK_BASE_URL", "https://yourdomain.com")
success_url = f"{webhook_base}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
cancel_url = f"{webhook_base}/payment/cancel"

print("=" * 60)
print("URLs that will be used in Stripe Checkout:")
print("=" * 60)
print(f"Success URL: {success_url}")
print(f"Cancel URL:  {cancel_url}")
print()

if webhook_base == "https://yourdomain.com":
    print("⚠️  WARNING: Using default URL!")
    print("   This will NOT work. Please set WEBHOOK_BASE_URL environment variable.")
    print()
    print("   To fix:")
    print("   1. Create .env file or set environment variable:")
    print("      export WEBHOOK_BASE_URL=https://stripe.autheai.com")
    print("   2. Restart webhook server after setting the variable")
else:
    print("✅ WEBHOOK_BASE_URL is configured correctly!")
