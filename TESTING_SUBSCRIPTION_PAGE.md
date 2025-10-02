# Testing Subscription Page - Step by Step Guide

## Issue Fixed
**Problem:** After logging in with username/password, visiting `/subscriptions` redirected to home page instead of showing subscription data.

**Root Cause:** 
1. Auth tokens weren't being stored in localStorage (only cookies)
2. Auth initialization logic checked GitHub OAuth first and didn't properly set user state for Cognito logins
3. Without proper auth state, the subscription page thought user was not authenticated and redirected

## Changes Made

### 1. Fixed `storeAuthData()` Function
- Now properly stores access token and refresh token in **localStorage**
- Added logging to track auth state changes
- Location: `frontend/lib/auth-context.tsx`

### 2. Fixed Auth Initialization Logic  
- Changed order: Check token-based auth (Cognito) **FIRST**, then GitHub OAuth
- Removed unnecessary health check validation that was causing issues
- Trust stored user data if valid token exists
- Added comprehensive console logging
- Location: `frontend/lib/auth-context.tsx`

## Testing Instructions

### Step 1: Clear Browser State (Important!)
Before testing, clear your browser data to start fresh:

1. Open browser DevTools (F12)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Clear:
   - **Cookies** for `www.codeflowops.com` and `api.codeflowops.com`
   - **Local Storage** for `www.codeflowops.com`
   - **Session Storage** for `www.codeflowops.com`
4. Or just use Incognito/Private window

### Step 2: Deploy Frontend Changes

```bash
cd frontend

# Build the updated frontend
npm run build

# Deploy to Netlify
# (Automatic if configured via Git, or manual upload)
```

### Step 3: Test Login Flow

1. **Navigate to login page:**
   ```
   https://www.codeflowops.com/login
   ```

2. **Open browser console (F12)**

3. **Login with your credentials**
   - Enter username/email and password
   - Click "Sign In"

4. **Watch console logs** - You should see:
   ```
   💾 Storing auth data for user: your-email@example.com
   ✅ User data stored: your-email@example.com
   ✅ Auth state updated, isAuthenticated: true
   ```

5. **Verify storage** - In DevTools Application tab, check:
   - localStorage should have:
     - `codeflowops_access_token` ✅
     - `codeflowops_refresh_token` ✅
     - `codeflowops_user` ✅
   - Cookies should have:
     - `auth_token` ✅
     - `codeflowops_access_token` ✅
     - `user_id` ✅

### Step 4: Navigate to Subscriptions Page

1. **Go to subscriptions page:**
   ```
   https://www.codeflowops.com/subscriptions
   ```

2. **Watch console logs** - You should see:
   ```
   🔄 Initializing authentication state...
   📝 Stored user: ✅ Found
   🔑 Access token: ✅ Found
   ✅ Token-based auth detected (Cognito/username-password)
   ✅ User set from stored data: your-email@example.com
   ✅ Auth initialization complete
   📊 Fetching subscription data...
   📊 Profile data received: {...}
   ✅ Subscription found: {...}
   ```

3. **Expected behavior:**
   - ✅ Page loads without redirect
   - ✅ Loading state shows briefly
   - ✅ Subscription data displays (if you have active subscription)
   - ✅ OR "No subscription" message shows (if you don't have subscription)

### Step 5: Debug Issues (If Something Goes Wrong)

#### A. Use Debug Script

1. Copy contents of `frontend/debug-subscription.js`
2. Paste into browser console on `/subscriptions` page
3. Review output to identify issue

#### B. Check Console Logs

Look for these key indicators:

**Authentication Issue:**
```
❌ Stored user: ❌ Not found
❌ Access token: ❌ Not found
```
→ **Solution:** Login again, ensure tokens are being stored

**API Error:**
```
❌ Error fetching subscription: Failed to fetch
```
→ **Solution:** Check network tab, verify API is accessible

**Token Expired:**
```
Status: 401 Unauthorized
```
→ **Solution:** Login again to get fresh token

#### C. Manual API Test

Test the subscription endpoint directly:

1. Get your token from localStorage:
   ```javascript
   localStorage.getItem('codeflowops_access_token')
   ```

2. Test endpoint in console:
   ```javascript
   fetch('https://api.codeflowops.com/api/v1/subscriptions/status', {
     credentials: 'include',
     headers: {
       'Authorization': 'Bearer YOUR_TOKEN_HERE',
       'Content-Type': 'application/json'
     }
   })
   .then(r => r.json())
   .then(data => console.log(data))
   ```

3. Expected response:
   ```json
   {
     "has_subscription": true,
     "id": "sub_1234567890",
     "status": "active",
     "plan": {
       "product": "CodeFlowOps Pro",
       "amount": 1900,
       "currency": "usd",
       "interval": "month"
     },
     "current_period_end": 1729036800000,
     "cancel_at_period_end": false,
     "is_trial": false
   }
   ```

## Expected Console Output (Success Flow)

### On Login:
```
💾 Storing auth data for user: test@example.com
✅ User data stored: test@example.com
✅ Auth state updated, isAuthenticated: true
```

### On Page Load:
```
🔄 Initializing authentication state...
📝 Stored user: ✅ Found
🔑 Access token: ✅ Found
✅ Token-based auth detected (Cognito/username-password)
✅ User set from stored data: test@example.com
✅ Auth initialization complete
```

### On Subscriptions Page:
```
📊 Fetching subscription data...
✅ Subscription data received: {...}
📊 Profile data received: {...}
✅ Subscription found: {...}
```

## Verification Checklist

- [ ] Browser storage cleared before test
- [ ] Login successful with console logs showing auth data stored
- [ ] localStorage contains all required keys
- [ ] Cookies are set properly
- [ ] Navigating to `/subscriptions` doesn't redirect
- [ ] Subscription data displays (or "no subscription" message)
- [ ] No errors in browser console
- [ ] Network tab shows successful API calls

## Common Issues & Solutions

### Issue 1: Still Redirecting to Home
**Symptoms:** Page redirects immediately, console shows "Not authenticated"

**Solution:**
1. Clear all browser data
2. Login again
3. Verify localStorage has tokens BEFORE navigating to subscriptions page

### Issue 2: Blank Page
**Symptoms:** Page loads but shows nothing, no errors

**Solution:**
1. Check React DevTools for AuthContext state
2. Verify `isAuthenticated` is `true`
3. Check if `loading` is stuck on `true`

### Issue 3: 401 Unauthorized
**Symptoms:** API calls return 401 error

**Solution:**
1. Token might be expired - login again
2. Token might not be sent - check Network tab headers
3. Backend might not be recognizing token - verify backend deployment

### Issue 4: No Subscription Data
**Symptoms:** Page loads but says "No subscription"

**Solution:**
1. Verify you have active Stripe subscription in database
2. Test API endpoint directly (see Manual API Test above)
3. Check backend logs for subscription lookup errors

## Success Criteria

✅ **Login Flow Works:**
- User can login with username/password
- Auth data stored in localStorage and cookies
- User state set in React context

✅ **Subscriptions Page Loads:**
- No redirect to home/login page
- Page renders subscription UI
- Loading state shows then resolves

✅ **Subscription Data Displays:**
- If user has subscription: All details shown (plan, amount, status, etc.)
- If user has no subscription: Clear message displayed
- No console errors

## Next Steps After Testing

1. ✅ Verify both Cognito and GitHub OAuth logins work
2. ✅ Test on different browsers (Chrome, Firefox, Safari)
3. ✅ Test on mobile devices
4. ✅ Verify with real Stripe subscription data
5. ✅ Test subscription management actions (cancel, upgrade, etc.)

## Rollback Procedure

If testing reveals critical issues:

```bash
# Frontend rollback
cd frontend
git revert HEAD
npm run build
# Redeploy

# Backend rollback (if needed)
cd backend
eb deploy --version previous-version-label
```

---

**Last Updated:** 2025-01-16
**Status:** Ready for Testing
**Files Modified:**
- `frontend/lib/auth-context.tsx` (auth initialization & token storage)
- `frontend/debug-subscription.js` (debugging helper)

