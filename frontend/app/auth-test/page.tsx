'use client'

import React, { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth-context'

export default function AuthTestPage() {
  const { user, isAuthenticated, loading } = useAuth()
  const [storageData, setStorageData] = useState<any>({})
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const data = {
        localStorage: {
          access_token: localStorage.getItem('codeflowops_access_token'),
          refresh_token: localStorage.getItem('codeflowops_refresh_token'),
          user: localStorage.getItem('codeflowops_user'),
        },
        sessionStorage: {
          user: sessionStorage.getItem('codeflowops_user'),
        },
        cookies: document.cookie,
        authContext: {
          loading,
          isAuthenticated,
          user: user ? { email: user.email, id: user.id } : null,
        }
      }
      setStorageData(data)
      console.log('🔍 Auth Test Data:', data)
    }
  }, [user, isAuthenticated, loading])
  
  return (
    <div style={{ padding: '40px', fontFamily: 'monospace', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '24px', marginBottom: '20px' }}>🔐 Authentication Debug Page</h1>
      
      <div style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '18px', marginBottom: '10px' }}>Auth Context State</h2>
        <div style={{ display: 'grid', gap: '10px' }}>
          <div>
            <strong>Loading:</strong> {loading ? '⏳ Yes' : '✅ No'}
          </div>
          <div>
            <strong>Authenticated:</strong> {isAuthenticated ? '✅ Yes' : '❌ No'}
          </div>
          <div>
            <strong>User:</strong> {user ? `✅ ${user.email}` : '❌ None'}
          </div>
        </div>
      </div>
      
      <div style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '18px', marginBottom: '10px' }}>localStorage</h2>
        <div style={{ display: 'grid', gap: '10px' }}>
          <div>
            <strong>access_token:</strong> {storageData.localStorage?.access_token ? `✅ ${storageData.localStorage.access_token.substring(0, 30)}...` : '❌ Missing'}
          </div>
          <div>
            <strong>refresh_token:</strong> {storageData.localStorage?.refresh_token ? `✅ ${storageData.localStorage.refresh_token.substring(0, 30)}...` : '❌ Missing'}
          </div>
          <div>
            <strong>user:</strong> {storageData.localStorage?.user ? '✅ Exists' : '❌ Missing'}
          </div>
          {storageData.localStorage?.user && (
            <pre style={{ backgroundColor: '#fff', padding: '10px', borderRadius: '4px', overflow: 'auto' }}>
              {JSON.stringify(JSON.parse(storageData.localStorage.user), null, 2)}
            </pre>
          )}
        </div>
      </div>
      
      <div style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '18px', marginBottom: '10px' }}>sessionStorage</h2>
        <div>
          <strong>user:</strong> {storageData.sessionStorage?.user ? '✅ Exists' : '❌ Missing'}
        </div>
        {storageData.sessionStorage?.user && (
          <pre style={{ backgroundColor: '#fff', padding: '10px', borderRadius: '4px', overflow: 'auto', marginTop: '10px' }}>
            {JSON.stringify(JSON.parse(storageData.sessionStorage.user), null, 2)}
          </pre>
        )}
      </div>
      
      <div style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '18px', marginBottom: '10px' }}>Cookies</h2>
        <pre style={{ backgroundColor: '#fff', padding: '10px', borderRadius: '4px', overflow: 'auto' }}>
          {storageData.cookies || 'No cookies'}
        </pre>
      </div>
      
      <div style={{ padding: '20px', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '18px', marginBottom: '10px' }}>💡 Diagnosis</h2>
        {loading && <p>⏳ Authentication is still loading...</p>}
        {!loading && isAuthenticated && <p style={{ color: 'green', fontWeight: 'bold' }}>✅ You are authenticated! Subscriptions page should work.</p>}
        {!loading && !isAuthenticated && storageData.localStorage?.access_token && (
          <p style={{ color: 'orange', fontWeight: 'bold' }}>⚠️ Token exists in storage but auth context shows not authenticated. Auth initialization might have failed.</p>
        )}
        {!loading && !isAuthenticated && !storageData.localStorage?.access_token && (
          <p style={{ color: 'red', fontWeight: 'bold' }}>❌ No authentication found. Please login first.</p>
        )}
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <button 
          onClick={() => window.location.href = '/login'}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: '#4f46e5', 
            color: 'white', 
            border: 'none', 
            borderRadius: '6px', 
            cursor: 'pointer',
            marginRight: '10px'
          }}
        >
          Go to Login
        </button>
        <button 
          onClick={() => window.location.href = '/subscriptions'}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: '#10b981', 
            color: 'white', 
            border: 'none', 
            borderRadius: '6px', 
            cursor: 'pointer'
          }}
        >
          Go to Subscriptions
        </button>
      </div>
    </div>
  )
}
