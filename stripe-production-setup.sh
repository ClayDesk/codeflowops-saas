#!/bin/bash
# CodeFlowOps Stripe Production Configuration Script

echo "🚀 Setting up Stripe Production Configuration for CodeFlowOps"

# Step 1: Verify Stripe Keys
echo "✅ Stripe Keys Configuration:"
echo "   - Publishable Key: pk_live_mQw9ZU3awBV35fG4HB8zPWMH"
echo "   - Secret Key: sk_live_Sbqrh9FiTBt2SB7qeG7kgxao"
echo ""

# Step 2: AWS Amplify Frontend Environment Variables
echo "📱 AWS Amplify Frontend Environment Variables:"
echo "   Add these in AWS Amplify Console > App Settings > Environment Variables:"
echo "   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_mQw9ZU3awBV35fG4HB8zPWMH"
echo "   NEXT_PUBLIC_API_URL=https://api.codeflowops.com"
echo ""

# Step 3: AWS Elastic Beanstalk Backend Environment Variables
echo "🖥️  AWS Elastic Beanstalk Backend Environment Variables:"
echo "   Add these in EB Console > Configuration > Software > Environment Properties:"
echo "   STRIPE_SECRET_KEY=sk_live_Sbqrh9FiTBt2SB7qeG7kgxao"
echo "   STRIPE_PUBLISHABLE_KEY=pk_live_mQw9ZU3awBV35fG4HB8zPWMH"
echo "   STRIPE_WEBHOOK_SECRET=[TO_BE_SET_AFTER_WEBHOOK_CREATION]"
echo ""

# Step 4: Stripe Dashboard Webhook Configuration
echo "🔗 Stripe Dashboard Webhook Setup:"
echo "   1. Go to https://dashboard.stripe.com/webhooks"
echo "   2. Click 'Add endpoint'"
echo "   3. Set endpoint URL: https://api.codeflowops.com/api/v1/payments/webhook"
echo "   4. Select these events:"
echo "      - customer.subscription.created"
echo "      - customer.subscription.updated"
echo "      - customer.subscription.deleted"
echo "      - invoice.payment_succeeded"
echo "      - invoice.payment_failed"
echo "      - payment_intent.succeeded"
echo "   5. Copy the webhook signing secret and add it to EB environment variables"
echo ""

# Step 5: Testing Instructions
echo "🧪 Testing Instructions:"
echo "   1. Deploy backend with new environment variables"
echo "   2. Deploy frontend with new environment variables"
echo "   3. Test webhook endpoint: curl -X POST https://api.codeflowops.com/api/v1/payments/webhook"
echo "   4. Create test subscription through frontend"
echo "   5. Monitor Stripe Dashboard > Logs for webhook delivery"
echo ""

echo "✨ Configuration complete! Deploy and test your production Stripe integration."
