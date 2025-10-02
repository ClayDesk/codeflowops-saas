# 🚀 Quick Deployment & Testing Guide

## Current Issue
You're logged in but the subscriptions page redirects you to the home page.

## Changes Made

### 1. Enhanced Subscriptions Page
- **File:** `frontend/app/subscriptions/page.tsx`
- **Changes:**
  - Added comprehensive console logging
  - Added 1-second delay before redirect to allow auth initialization
  - Double-checks localStorage before redirecting
  - Shows auth state in console for debugging

### 2. Created Auth Test Page
- **File:** `frontend/app/auth-test/page.tsx`
- **Purpose:** Visual debug page to see authentication state
- **URL:** `https://www.codeflowops.com/auth-test`

## 🔧 Deploy to AWS Amplify

### Option 1: Git Push (Automatic)
```bash
# From project root
git add .
git commit -m "Fix: Enhanced auth state detection for subscriptions page"
git push origin master

# Amplify will automatically detect and deploy
```

### Option 2: Manual Deploy
```bash
cd frontend
npm run build

# Then upload the `out` folder to Amplify manually
```

## 🧪 Testing Steps

### Step 1: Visit Auth Test Page
1. Go to: `https://www.codeflowops.com/auth-test`
2. This page will show you:
   - ✅ Whether auth context thinks you're authenticated
   - ✅ What's in localStorage
   - ✅ What's in cookies
   - ✅ Current user data

### Step 2: Check Console Output
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for these logs:
   ```
   🔄 Initializing authentication state...
   📝 Stored user: ✅ Found
   🔑 Access token: ✅ Found
   ✅ Token-based auth detected
   ✅ User set from stored data: your-email@example.com
   ✅ Auth initialization complete
   ```

### Step 3: Test Subscriptions Page
1. Go to: `https://www.codeflowops.com/subscriptions`
2. Watch console for:
   ```
   🔐 Auth State: { authLoading: false, isAuthenticated: true, user: "your@email.com", hasToken: true }
   🔍 Checking if redirect needed: { authLoading: false, isAuthenticated: true }
   ✅ Auth check passed: Authenticated
   📊 Fetching subscription data...
   ```

## 🐛 If Still Redirecting

### Check 1: Are you actually logged in?
```javascript
// Run in console
console.log('Token:', !!localStorage.getItem('codeflowops_access_token'))
console.log('User:', !!localStorage.getItem('codeflowops_user'))
```

### Check 2: Is auth context initialized?
```javascript
// Run in console - should show auth state
setTimeout(() => {
  console.log('Check React DevTools → Components → AuthProvider → hooks → user')
}, 2000)
```

### Check 3: Did deployment finish?
- Check Amplify console
- Verify build completed successfully
- Check deployed URL matches your changes (view source, look for console.log statements)

## 🔍 Expected Console Output (Working State)

When you visit `/subscriptions` while logged in:

```
🔄 Initializing authentication state...
📝 Stored user: ✅ Found
🔑 Access token: ✅ Found
✅ Token-based auth detected (Cognito/username-password)
✅ User set from stored data: user@example.com
✅ Auth initialization complete
🔐 Auth State: {authLoading: false, isAuthenticated: true, user: "user@example.com", hasToken: true}
🔍 Checking if redirect needed: {authLoading: false, isAuthenticated: true}
✅ Auth check passed: Authenticated
📊 Fetching subscription data...
✅ Subscription data received: {...}
```

## 🚨 Troubleshooting

### Issue: "Auth context shows not authenticated but token exists"
**Cause:** Auth initialization failed or completed before stored data was checked

**Solution:**
1. Clear browser cache and cookies
2. Login again
3. Check console for initialization errors

### Issue: "Token missing from localStorage"
**Cause:** Login didn't properly store tokens

**Solution:**
1. We fixed `storeAuthData()` in `auth-context.tsx`
2. Need to login again AFTER deployment
3. Check console during login for "💾 Storing auth data" message

### Issue: "Still redirects after 1 second"
**Cause:** `isAuthenticated` is false even though token exists

**Solution:**
1. Visit `/auth-test` to see exact state
2. Check if `setUser()` is being called in auth initialization
3. Look for errors in auth initialization

## 📝 Quick Test Commands

### In Browser Console:
```javascript
// Check authentication state
console.log('Auth Check:', {
  token: !!localStorage.getItem('codeflowops_access_token'),
  user: !!localStorage.getItem('codeflowops_user'),
  cookies: document.cookie.includes('auth_token')
})

// If logged in but redirecting, this will show the mismatch:
setTimeout(() => {
  const hasStorage = !!localStorage.getItem('codeflowops_access_token')
  console.log('Storage has token:', hasStorage)
  console.log('Check React DevTools for auth context state')
}, 2000)
```

## ✅ Success Criteria

- [ ] Auth test page shows "✅ You are authenticated"
- [ ] Subscriptions page doesn't redirect
- [ ] Console shows "✅ Auth check passed: Authenticated"
- [ ] Subscription data fetches (or shows "No subscription" if none exists)
- [ ] No errors in console

## 🎯 Next Steps After Deployment

1. **Clear browser cache** (Ctrl+Shift+R or Cmd+Shift+R)
2. **Login again** to ensure new `storeAuthData()` logic runs
3. **Visit `/auth-test`** to verify authentication state
4. **Visit `/subscriptions`** to test the fix
5. **Share console output** if still having issues

---

**Files Modified:**
- ✅ `frontend/lib/auth-context.tsx` (auth initialization + token storage)
- ✅ `frontend/app/subscriptions/page.tsx` (redirect logic + debugging)
- ✅ `frontend/app/auth-test/page.tsx` (NEW - debug page)

**Need to Deploy:** YES - Changes are in code but not yet deployed to Amplify
