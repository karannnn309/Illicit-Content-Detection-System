# Stripe Payment Configuration Guide

## Overview
Your payment system supports both **Test Mode** (for development) and **Production Mode** (for real payments).

---

## Current Status: Test Mode Active ✅

The system is currently running in **Test Mode**, which means:
- ✅ No real payments are processed
- ✅ No credit card information is required
- ✅ Perfect for testing the payment flow
- ✅ All payment features work as expected (just simulated)

---

## Configuration Settings

### Location: `illicit_detection/settings.py`

```python
# Test Mode Configuration (Current)
STRIPE_TEST_MODE = True  # Set to False for production

# Test API Keys (For Development)
STRIPE_TEST_PUBLIC_KEY = 'pk_test_your_test_publishable_key_here'
STRIPE_TEST_SECRET_KEY = 'sk_test_your_test_secret_key_here'

# Live API Keys (For Production)
STRIPE_LIVE_PUBLIC_KEY = 'pk_live_your_live_publishable_key_here'
STRIPE_LIVE_SECRET_KEY = 'sk_live_your_live_secret_key_here'
```

---

## How to Get Stripe API Keys

### Step 1: Create Stripe Account
1. Go to [https://stripe.com](https://stripe.com)
2. Click "Sign up" and create a free account
3. Complete email verification

### Step 2: Get Test Keys (For Development)
1. Log in to [Stripe Dashboard](https://dashboard.stripe.com)
2. Make sure you're in **Test mode** (toggle in top-right)
3. Go to **Developers** → **API keys**
4. You'll see:
   - **Publishable key**: `pk_test_...` (safe to expose in frontend)
   - **Secret key**: `sk_test_...` (keep this private!)
5. Copy both keys to `settings.py`:
   ```python
   STRIPE_TEST_PUBLIC_KEY = 'pk_test_51A...'
   STRIPE_TEST_SECRET_KEY = 'sk_test_51A...'
   ```

### Step 3: Get Live Keys (For Production - Later)
1. Complete Stripe account verification (business details, banking info)
2. Switch to **Live mode** in Stripe Dashboard
3. Go to **Developers** → **API keys**
4. Copy your live keys:
   ```python
   STRIPE_LIVE_PUBLIC_KEY = 'pk_live_51A...'
   STRIPE_LIVE_SECRET_KEY = 'sk_live_51A...'
   ```

---

## Switching Between Test and Production

### Currently Running: Test Mode

**To keep using Test Mode (Recommended for now):**
```python
STRIPE_TEST_MODE = True  # Keep this setting
```

**To switch to Production Mode:**
```python
STRIPE_TEST_MODE = False  # Change to False

# Make sure you have valid live keys set:
STRIPE_LIVE_PUBLIC_KEY = 'pk_live_...'  # Real live key
STRIPE_LIVE_SECRET_KEY = 'sk_live_...'  # Real live key
```

⚠️ **Important**: Only switch to production when:
- You have completed Stripe account verification
- You have tested thoroughly in test mode
- You have valid live API keys
- Your business is ready to accept real payments

---

## Testing the Payment System

### Test Mode (Current Setup)

1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Login and navigate to:**
   - Go to "My API Keys" page
   - Click "Upgrade" on a free tier API key

3. **Select a tier:**
   - Choose Basic ($9.99/month) or Premium ($49.99/month)

4. **Process payment:**
   - You'll see: "⚠️ Test Mode Active: This is a demo payment"
   - Select "Test Payment (Demo)"
   - Click "Complete Payment"
   - Payment will be simulated instantly

5. **Verify upgrade:**
   - Check success page shows new tier
   - API key page shows upgraded tier
   - Daily limit increased to tier limit

### Production Mode Testing (When Ready)

With valid Stripe keys and `STRIPE_TEST_MODE = False`:

1. Use real test credit cards from Stripe:
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits

2. Payment will process through Stripe
3. Real payment intent created
4. You'll see charges in Stripe Dashboard

---

## Payment Features

### Supported Features:
✅ **Tier-based subscriptions** (Free, Basic, Premium)  
✅ **Automatic daily limit updates**  
✅ **30-day subscription periods**  
✅ **Subscription cancellation** (downgrade to free)  
✅ **Payment history tracking**  
✅ **User notifications** on payment success  
✅ **Admin billing dashboard**  

### Payment Tiers:

| Tier | Price | Daily Limit | Features |
|------|-------|-------------|----------|
| Free | $0/month | 50 requests | Basic API access |
| Basic | $9.99/month | 1,000 requests | Priority support |
| Premium | $49.99/month | 10,000 requests | Advanced features + Priority support |

---

## Security Best Practices

### ⚠️ Never commit real API keys to Git!

**Option 1: Use environment variables**
```python
import os

STRIPE_LIVE_SECRET_KEY = os.environ.get('STRIPE_LIVE_SECRET_KEY', '')
STRIPE_LIVE_PUBLIC_KEY = os.environ.get('STRIPE_LIVE_PUBLIC_KEY', '')
```

**Option 2: Use .env file**
```bash
# Create .env file
STRIPE_LIVE_SECRET_KEY=sk_live_...
STRIPE_LIVE_PUBLIC_KEY=pk_live_...
```

**Add to .gitignore:**
```
.env
settings_local.py
```

---

## Troubleshooting

### Issue: "Payment processing error"
**Solution**: 
- Check if `STRIPE_SECRET_KEY` is set correctly
- Verify you're using the right key (test vs live)
- Check Stripe Dashboard for error details

### Issue: "This payment has already been completed"
**Solution**: 
- Each payment can only be processed once
- Create a new payment by clicking "Upgrade" again

### Issue: Can't see Stripe option
**Solution**: 
- Make sure `STRIPE_TEST_MODE = False` in settings
- Verify Stripe keys are configured
- Check that Stripe package is installed: `pip list | grep stripe`

---

## Quick Reference

### Current Configuration:
```
Mode: Test Mode ✅
Charges: Simulated (No real money)
Keys Required: None (optional for enhanced testing)
Ready for: Development & Testing
```

### To Go Live:
1. ✅ Complete Stripe account verification
2. ✅ Get live API keys
3. ✅ Set `STRIPE_TEST_MODE = False`
4. ✅ Test with test credit cards
5. ✅ Deploy to production

---

## Support Resources

- **Stripe Documentation**: [https://stripe.com/docs](https://stripe.com/docs)
- **Stripe Dashboard**: [https://dashboard.stripe.com](https://dashboard.stripe.com)
- **Test Cards**: [https://stripe.com/docs/testing](https://stripe.com/docs/testing)
- **API Reference**: [https://stripe.com/docs/api](https://stripe.com/docs/api)

---

## Summary

✅ **Test Mode is currently active** - Perfect for development  
✅ **No setup required** - Works out of the box  
✅ **Add Stripe keys later** - When ready for production  
✅ **Easy to switch** - Just change `STRIPE_TEST_MODE` setting  

You can start testing the payment flow immediately without any Stripe configuration!
