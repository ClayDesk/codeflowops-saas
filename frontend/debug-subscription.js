/**
 * Subscription Page Debug Helper
 * Add this to browser console to diagnose authentication and subscription issues
 */

console.log('🔍 CodeFlowOps Subscription Debug Tool');
console.log('=====================================\n');

// Check authentication state
console.log('1️⃣ AUTHENTICATION STATE:');
console.log('------------------------');

// Check localStorage
const accessToken = localStorage.getItem('codeflowops_access_token');
const refreshToken = localStorage.getItem('codeflowops_refresh_token');
const userDataLS = localStorage.getItem('codeflowops_user');

console.log('localStorage.codeflowops_access_token:', accessToken ? '✅ EXISTS' : '❌ MISSING');
console.log('localStorage.codeflowops_refresh_token:', refreshToken ? '✅ EXISTS' : '❌ MISSING');
console.log('localStorage.codeflowops_user:', userDataLS ? '✅ EXISTS' : '❌ MISSING');

if (userDataLS) {
  try {
    const userData = JSON.parse(userDataLS);
    console.log('  - User ID:', userData.id);
    console.log('  - Email:', userData.email);
    console.log('  - Provider:', userData.provider);
  } catch (e) {
    console.error('  - ERROR parsing user data:', e);
  }
}

// Check sessionStorage
const userDataSS = sessionStorage.getItem('codeflowops_user');
console.log('\nsessionStorage.codeflowops_user:', userDataSS ? '✅ EXISTS' : '❌ MISSING');

// Check cookies
const cookies = document.cookie.split(';').reduce((acc, cookie) => {
  const [key, value] = cookie.trim().split('=');
  acc[key] = value;
  return acc;
}, {});

console.log('\n2️⃣ COOKIES:');
console.log('------------');
console.log('auth_token:', cookies.auth_token ? '✅ EXISTS' : '❌ MISSING');
console.log('codeflowops_access_token:', cookies.codeflowops_access_token ? '✅ EXISTS' : '❌ MISSING');
console.log('user_id:', cookies.user_id ? '✅ EXISTS' : '❌ MISSING');
console.log('session_id:', cookies.session_id ? '✅ EXISTS' : '❌ MISSING');

// Test API endpoints
console.log('\n3️⃣ API ENDPOINT TESTS:');
console.log('----------------------');

const API_BASE = 'https://api.codeflowops.com';
const token = cookies.codeflowops_access_token || cookies.auth_token || accessToken;

if (!token) {
  console.error('❌ NO TOKEN FOUND - Cannot test API endpoints');
  console.log('\n💡 DIAGNOSIS: User appears to be logged out');
  console.log('   Action: Try logging in again');
} else {
  console.log('Token found:', token.substring(0, 20) + '...');

  // Test 1: Health check
  console.log('\n📍 Testing /api/health...');
  fetch(`${API_BASE}/api/health`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
    .then(r => {
      console.log(`  Status: ${r.status} ${r.statusText}`);
      return r.json();
    })
    .then(data => console.log('  Response:', data))
    .catch(e => console.error('  Error:', e));

  // Test 2: Auth status
  console.log('\n📍 Testing /api/v1/auth/status...');
  fetch(`${API_BASE}/api/v1/auth/status`, {
    credentials: 'include',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
    .then(r => {
      console.log(`  Status: ${r.status} ${r.statusText}`);
      return r.json();
    })
    .then(data => console.log('  Response:', data))
    .catch(e => console.error('  Error:', e));

  // Test 3: Get user profile
  console.log('\n📍 Testing /api/v1/auth/me...');
  fetch(`${API_BASE}/api/v1/auth/me`, {
    credentials: 'include',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  })
    .then(r => {
      console.log(`  Status: ${r.status} ${r.statusText}`);
      return r.json();
    })
    .then(data => console.log('  Response:', data))
    .catch(e => console.error('  Error:', e));

  // Test 4: Get subscription status
  console.log('\n📍 Testing /api/v1/subscriptions/status...');
  fetch(`${API_BASE}/api/v1/subscriptions/status`, {
    credentials: 'include',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  })
    .then(r => {
      console.log(`  Status: ${r.status} ${r.statusText}`);
      return r.json();
    })
    .then(data => {
      console.log('  Response:', data);
      
      if (data.has_subscription) {
        console.log('\n✅ SUBSCRIPTION FOUND!');
        console.log('   ID:', data.id);
        console.log('   Status:', data.status);
        console.log('   Plan:', data.plan);
      } else {
        console.log('\nℹ️ No active subscription');
      }
    })
    .catch(e => console.error('  Error:', e));
}

console.log('\n4️⃣ REACT AUTH CONTEXT STATE:');
console.log('-----------------------------');
console.log('Check React DevTools for AuthContext values:');
console.log('  - user');
console.log('  - loading');
console.log('  - isAuthenticated');

console.log('\n📝 COMMON ISSUES:');
console.log('-----------------');
console.log('1. Token expired → Status 401 on API calls');
console.log('2. Token missing → Redirect to login page');
console.log('3. Auth state not initialized → Check useEffect in AuthProvider');
console.log('4. Health check failing → Token validation issue');
console.log('\n=====================================');
