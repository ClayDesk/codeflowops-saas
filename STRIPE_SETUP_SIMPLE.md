# Simple Stripe Setup Instructions

## Backend Environment Variables
Create a `.env` file in the `backend/` directory with:

```bash
STRIPE_SECRET_KEY=sk_live_Sbqrh9FiTBt2SB7qeG7kgxao
STRIPE_WEBHOOK_SECRET=your_webhook_secret_from_stripe_dashboard
STRIPE_PUBLISHABLE_KEY=pk_live_mQw9ZU3awBV35fG4HB8zPWMH
```

## Frontend Environment Variables  
Create a `.env.local` file in the `frontend/` directory with:

```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_mQw9ZU3awBV35fG4HB8zPWMH
NEXT_PUBLIC_API_URL=https://api.codeflowops.com
```

## Stripe Dashboard Setup
1. Go to your Stripe Dashboard
2. Navigate to **Developers > Webhooks**
3. Click **Add endpoint**
4. URL: `https://api.codeflowops.com/api/v1/payments/webhook`
5. Events to send:
   - `customer.subscription.created`
   - `customer.subscription.trial_will_end`  
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
6. Copy the webhook secret and add it to your backend `.env`

## Quick Test
1. Start backend: `python backend/simple_api.py`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to your checkout page
4. Enter an email and start trial
5. Check Stripe dashboard for new customer/subscription

## Production Deployment
- Set environment variables in your deployment platform
- Update webhook URL in Stripe dashboard to production URL
- Test webhook delivery in Stripe dashboard

Your setup is complete! 🎉
