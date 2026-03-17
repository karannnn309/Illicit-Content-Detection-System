# Razorpay Payment Gateway Setup Guide (India)

## Overview
Razorpay is India's leading payment gateway that supports UPI, Credit/Debit Cards, NetBanking, and Digital Wallets. This guide will help you integrate Razorpay for accepting payments from Indian users.

---

## Why Razorpay for India?

### ✅ **India-Specific Features**
- **UPI Payments**: Direct bank transfers via UPI apps (GPay, PhonePe, Paytm)
- **Local Cards**: Accepts Indian Rupee transactions
- **NetBanking**: Support for 50+ Indian banks
- **Wallets**: Paytm, PhonePe, Freecharge, etc.
- **EMI Options**: Card EMI and Cardless EMI
- **Compliant**: RBI-compliant payment gateway

### ❌ **Why Not Stripe for India?**
- Limited support for Indian payment methods
- No UPI integration
- Higher fees for INR transactions
- Complex setup for Indian businesses

---

## Current Status: Test Mode Active ✅

The system is currently running in **Test Mode**, which means:
- ✅ No real payments are processed
- ✅ Use Razorpay test credentials
- ✅ Perfect for testing the payment flow
- ✅ All payment features work as expected (simulated)

---

## Configuration Settings

### Location: `illicit_detection/settings.py`

```python
# Payment Gateway Configuration
PAYMENT_TEST_MODE = True  # Set to False for production

# Razorpay Test Keys (For Development)
RAZORPAY_TEST_KEY_ID = 'rzp_test_your_test_key_id_here'
RAZORPAY_TEST_KEY_SECRET = 'your_test_key_secret_here'

# Razorpay Live Keys (For Production)
RAZORPAY_LIVE_KEY_ID = 'rzp_live_your_live_key_id_here'
RAZORPAY_LIVE_KEY_SECRET = 'your_live_key_secret_here'

# Payment gateway preference
PAYMENT_GATEWAY_PREFERENCE = 'auto'  # Shows all available options
```

---

## How to Get Razorpay API Keys

### Step 1: Create Razorpay Account
1. Go to [https://razorpay.com](https://razorpay.com)
2. Click "Sign Up" and create a free account
3. Complete email and phone verification
4. **Note**: You need an Indian business or can use individual account for testing

### Step 2: Get Test Keys (For Development)
1. Log in to [Razorpay Dashboard](https://dashboard.razorpay.com)
2. Make sure you're in **Test mode** (toggle in top-left)
3. Go to **Settings** → **API Keys**
4. Click **Generate Test Keys**
5. You'll see:
   - **Key ID**: `rzp_test_...` (safe to expose in frontend)
   - **Key Secret**: `...` (keep this private!)
6. Copy both keys to `settings.py`:
   ```python
   RAZORPAY_TEST_KEY_ID = 'rzp_test_ABC123...'
   RAZORPAY_TEST_KEY_SECRET = 'YourSecretKey123...'
   ```

### Step 3: Get Live Keys (For Production - Later)
1. Complete KYC verification (business/individual details)
2. Submit required documents (PAN, GST, Bank Account)
3. Wait for approval (usually 24-48 hours)
4. Switch to **Live mode** in Razorpay Dashboard
5. Go to **Settings** → **API Keys**
6. Generate and copy your live keys:
   ```python
   RAZORPAY_LIVE_KEY_ID = 'rzp_live_ABC123...'
   RAZORPAY_LIVE_KEY_SECRET = 'YourLiveSecretKey123...'
   ```

---

## Switching Between Test and Production

### Currently Running: Test Mode

**To keep using Test Mode (Recommended for now):**
```python
PAYMENT_TEST_MODE = True  # Keep this setting
```

**To switch to Production Mode:**
```python
PAYMENT_TEST_MODE = False  # Change to False

# Make sure you have valid live keys set:
RAZORPAY_LIVE_KEY_ID = 'rzp_live_...'  # Real live key
RAZORPAY_LIVE_KEY_SECRET = '...'  # Real live secret
```

⚠️ **Important**: Only switch to production when:
- You have completed Razorpay KYC verification
- You have tested thoroughly in test mode
- You have valid live API keys
- Your business is ready to accept real payments

---

## Testing the Payment System

### Test Mode (Current Setup)

1. **Install the razorpay package:**
   ```bash
   cd illicit_detection
   pip install razorpay
   ```

2. **Start the server:**
   ```bash
   python manage.py runserver
   ```

3. **Login and navigate to:**
   - Go to "My API Keys" page
   - Click "Upgrade" on a free tier API key

4. **Select a tier:**
   - Choose Basic (₹749/month) or Premium (₹3,749/month)
   - Note: Prices shown in $ are converted to ₹ in production

5. **Process payment:**
   - Select "Razorpay (India)" as payment method
   - Click "Pay with Razorpay"
   - Razorpay checkout modal will open

6. **Test Payment Methods:**

   **For Test Mode, use these credentials:**
   
   - **Test Cards:**
     - Card Number: `4111 1111 1111 1111`
     - Expiry: Any future date (e.g., 12/25)
     - CVV: Any 3 digits (e.g., 123)
     - Name: Any name
   
   - **Test UPI:**
     - UPI ID: `success@razorpay`
     - This will simulate a successful payment
   
   - **Test NetBanking:**
     - Select any bank
     - Login with any credentials in test mode
     - All test transactions will succeed

7. **Verify upgrade:**
   - Check success page shows new tier
   - API key page shows upgraded tier
   - Daily limit increased to tier limit

---

## Production Mode Testing (When Ready)

With valid Razorpay keys and `PAYMENT_TEST_MODE = False`:

1. Real payment methods:
   - **UPI**: Use your actual UPI ID (GPay, PhonePe, etc.)
   - **Cards**: Use real credit/debit cards
   - **NetBanking**: Login with actual bank credentials
   - **Wallets**: Use Paytm, PhonePe wallet, etc.

2. Payment will process through Razorpay
3. Money will be deducted from customer's account
4. Funds will be credited to your Razorpay account
5. You'll see charges in Razorpay Dashboard

---

## Payment Features

### Supported Payment Methods:
✅ **UPI** (Google Pay, PhonePe, Paytm, BHIM, etc.)  
✅ **Credit Cards** (Visa, Mastercard, RuPay, Amex)  
✅ **Debit Cards** (All Indian bank debit cards)  
✅ **NetBanking** (50+ Indian banks)  
✅ **Wallets** (Paytm, PhonePe, Freecharge, Mobikwik)  
✅ **EMI** (Card EMI for select banks)  

### Payment Tiers:

| Tier | Price (INR) | Price (USD) | Daily Limit | Features |
|------|-------------|-------------|-------------|----------|
| Free | ₹0/month | $0/month | 50 requests | Basic API access |
| Basic | ₹749/month | $9.99/month | 1,000 requests | Priority support |
| Premium | ₹3,749/month | $49.99/month | 10,000 requests | Advanced features |

**Note**: Dollar prices are shown in USD equivalent. Razorpay processes in INR.

---

## Database Migration

After updating the Payment model, run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

This will add the new fields:
- `payment_gateway` (test/stripe/razorpay)
- `razorpay_order_id`
- `razorpay_payment_id`
- `razorpay_signature`

---

## Security Best Practices

### 1. **Keep API Secrets Secure**
```python
# ❌ DON'T commit secrets to Git
RAZORPAY_TEST_KEY_SECRET = 'actual_secret_key'

# ✅ DO use environment variables
import os
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'default_test_key')
```

### 2. **Verify Payment Signatures**
The system automatically verifies Razorpay signatures to prevent tampering:
```python
# This is handled in razorpay_payment_callback view
client.utility.verify_payment_signature(params_dict)
```

### 3. **Use HTTPS in Production**
Always use HTTPS for production deployments to protect payment data.

### 4. **Enable Webhooks (Optional)**
Set up webhooks in Razorpay Dashboard for:
- Payment success notifications
- Payment failure alerts
- Subscription renewals
- Refund notifications

---

## Troubleshooting

### Issue: "Payment processing error"
**Solution**: 
- Check if `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are set correctly
- Verify you're using the right key (test vs live)
- Check Razorpay Dashboard for error details

### Issue: "razorpay module not found"
**Solution**: 
```bash
pip install razorpay
```

### Issue: Payment succeeds but order not updated
**Solution**: 
- Check that callback URL is accessible
- Verify CSRF token is being sent
- Check server logs for errors

### Issue: "Invalid signature" error
**Solution**: 
- Make sure you're using matching key pairs (test with test, live with live)
- Verify that the signature verification is not being skipped
- Check that the order_id matches

### Issue: Currency mismatch
**Solution**: 
- Razorpay uses INR (Indian Rupees) as the currency
- The system automatically converts amounts to paise (100 paise = 1 INR)
- For international cards, Razorpay handles currency conversion

---

## Comparison: Razorpay vs Stripe

| Feature | Razorpay (India) | Stripe (International) |
|---------|------------------|------------------------|
| **UPI Support** | ✅ Yes | ❌ No |
| **Indian Cards** | ✅ Optimized | ⚠️ Limited |
| **NetBanking** | ✅ 50+ Banks | ❌ No |
| **Wallets** | ✅ All Major | ❌ No |
| **Setup for India** | ✅ Easy | ❌ Complex |
| **Fees (India)** | 2% + GST | 2.9% + GST |
| **Settlement** | T+3 days | T+7 days |
| **KYC Required** | ✅ Yes | ✅ Yes |
| **Best For** | 🇮🇳 Indian Users | 🌍 International |

---

## Multi-Gateway Setup

The system now supports both Razorpay and Stripe:

### Gateway Selection Options:

```python
# In settings.py
PAYMENT_GATEWAY_PREFERENCE = 'auto'  # Show all available options
# or
PAYMENT_GATEWAY_PREFERENCE = 'razorpay'  # Default to Razorpay
# or
PAYMENT_GATEWAY_PREFERENCE = 'stripe'  # Default to Stripe
```

### User Selection:
When `PAYMENT_GATEWAY_PREFERENCE = 'auto'`, users can choose:
- **Test Payment** (Demo mode - no charges)
- **Razorpay** (India - UPI, Cards, NetBanking, Wallets)
- **Stripe** (International - Credit/Debit Cards)

---

## Quick Reference

### Current Configuration:
```
Mode: Test Mode ✅
Gateway: Razorpay + Stripe (Multi-gateway)
Charges: Simulated (No real money)
Keys Required: Test keys (optional for enhanced testing)
Ready for: Development & Testing
Currency: INR (Indian Rupees) for Razorpay
```

### To Go Live with Razorpay:
1. ✅ Complete Razorpay KYC verification
2. ✅ Get live API keys from Razorpay Dashboard
3. ✅ Set `PAYMENT_TEST_MODE = False`
4. ✅ Test with real payment methods (small amounts)
5. ✅ Deploy to production with HTTPS

---

## Support Resources

### Razorpay Resources:
- **Razorpay Documentation**: [https://razorpay.com/docs](https://razorpay.com/docs)
- **Razorpay Dashboard**: [https://dashboard.razorpay.com](https://dashboard.razorpay.com)
- **API Reference**: [https://razorpay.com/docs/api](https://razorpay.com/docs/api)
- **Test Credentials**: [https://razorpay.com/docs/payments/payments/test-card-details](https://razorpay.com/docs/payments/payments/test-card-details)
- **Support**: [https://razorpay.com/support](https://razorpay.com/support)

### Integration Support:
- **Python SDK**: [https://github.com/razorpay/razorpay-python](https://github.com/razorpay/razorpay-python)
- **Checkout Docs**: [https://razorpay.com/docs/payments/payment-gateway/web-integration/standard](https://razorpay.com/docs/payments/payment-gateway/web-integration/standard)

---

## Summary

✅ **Razorpay integration is complete!**

Your system now supports:
- 🇮🇳 Razorpay (India) - UPI, Cards, NetBanking, Wallets
- 🌍 Stripe (International) - Credit/Debit Cards
- 🧪 Test Mode - No real charges for development

**Next Steps:**
1. Install razorpay package: `pip install razorpay`
2. Run database migrations: `python manage.py migrate`
3. Add Razorpay test keys to settings.py
4. Test the payment flow with test credentials
5. Complete KYC when ready for production

**For Indian users**, Razorpay is the recommended payment gateway as it provides:
- Better success rates for Indian payment methods
- Lower fees and faster settlements
- Superior UPI and NetBanking integration
- Local customer support

---

**Need help?** Contact Razorpay support or check their comprehensive documentation.
