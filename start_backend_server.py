#!/usr/bin/env python3
"""
🚀 Background Backend Starter
Starts the backend and returns terminal prompt immediately with detailed startup info
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def monitor_startup_output(process, startup_complete_event):
    """Monitor initial startup output and show details"""
    startup_lines = []
    startup_timeout = 30  # 30 seconds timeout for startup
    start_time = time.time()
    
    try:
        while time.time() - start_time < startup_timeout:
            if process.poll() is not None:
                # Process ended unexpectedly
                print("❌ Backend process ended unexpectedly during startup")
                break
                
            # Check if we can read a line (non-blocking)
            try:
                line = process.stdout.readline()
                if line:
                    line_text = line.strip()
                    startup_lines.append(line_text)
                    print(f"📋 {line_text}")
                    
                    # Check for startup completion indicators
                    if any(indicator in line_text.lower() for indicator in [
                        "uvicorn running", "application startup complete", 
                        "started server process", "server started"
                    ]):
                        print("✅ Server startup completed successfully!")
                        startup_complete_event.set()
                        break
                else:
                    time.sleep(0.1)  # Brief pause if no output
            except:
                time.sleep(0.1)
                continue
                
    except Exception as e:
        print(f"⚠️ Error monitoring startup: {e}")
    
    return startup_lines

def start_background_backend():
    """Start the backend in background with detailed monitoring and return terminal prompt"""
    backend_dir = Path(__file__).parent / "backend"
    
    print("🚀 Starting CodeFlowOps Backend with Enhanced Monitoring...")
    print("🔥 Features: Firebase/Supabase support, Enhanced database detection, Local data fallback")
    print("📊 Monitoring startup process...")
    print("=" * 70)
    
    try:
        # Start backend with output capture for monitoring
        process = subprocess.Popen(
            [sys.executable, "simple_api.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        print(f"🚀 Backend process started (PID: {process.pid})")
        print("📋 Startup logs:")
        print("-" * 50)
        
        # Create event to signal startup completion
        startup_complete = threading.Event()
        
        # Monitor startup in separate thread
        monitor_thread = threading.Thread(
            target=monitor_startup_output, 
            args=(process, startup_complete), 
            daemon=True
        )
        monitor_thread.start()
        
        # Wait for startup completion or timeout
        if startup_complete.wait(timeout=30):
            print("-" * 50)
            print("🎉 BACKEND STARTUP COMPLETE!")
            print(f"🌐 Server URL: http://localhost:8000")
            print(f"🔧 Process ID: {process.pid}")
            print("✅ Backend is running in background")
            print(f"� To stop manually: taskkill /PID {process.pid} /F")
            print("📋 Server will continue running independently")
            print("=" * 70)
            print("💡 Terminal prompt returned - you can continue working")
            
            # Start background monitoring for restarts
            restart_monitor = threading.Thread(
                target=monitor_background_process, 
                args=(process,), 
                daemon=True
            )
            restart_monitor.start()
            
        else:
            print("⚠️ Startup monitoring timeout reached")
            print(f"🌐 Server should be at: http://localhost:8000")
            print(f"🔧 Process ID: {process.pid}")
            print("💡 Check manually if server is responding")
        
        return process.pid
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def monitor_background_process(process):
    """Monitor the background process and handle restarts"""
    restart_count = 0
    max_restarts = 5
    
    while restart_count < max_restarts:
        # Wait for process to end
        process.wait()
        
        restart_count += 1
        print(f"\n⚠️ Backend stopped unexpectedly. Auto-restart #{restart_count}/{max_restarts}")
        
        if restart_count < max_restarts:
            try:
                backend_dir = Path(__file__).parent / "backend"
                process = subprocess.Popen(
                    [sys.executable, "simple_api.py"],
                    cwd=backend_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )
                print(f"✅ Backend restarted (PID: {process.pid})")
                time.sleep(2)  # Brief pause before monitoring again
            except Exception as e:
                print(f"❌ Restart failed: {e}")
                break
        else:
            print("💥 Max restarts reached. Manual intervention required.")
            break

if __name__ == "__main__":
    start_background_backend()
