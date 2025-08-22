"""
Parallel API Startup Script
Runs both the legacy simple_api.py and new modular_api.py side by side
"""
import subprocess
import sys
import time
import logging
import signal
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ParallelAPIRunner:
    def __init__(self):
        self.legacy_process = None
        self.modular_process = None
        self.backend_dir = Path(__file__).parent
        
    def start_legacy_api(self):
        """Start the legacy simple_api.py on port 8000"""
        logger.info("🚀 Starting Legacy API (simple_api.py) on port 8000...")
        
        try:
            cmd = [sys.executable, "simple_api.py"]
            self.legacy_process = subprocess.Popen(
                cmd,
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("✅ Legacy API started (PID: {})".format(self.legacy_process.pid))
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start legacy API: {e}")
            return False
    
    def start_modular_api(self):
        """Start the new modular_api.py on port 8001"""
        logger.info("🚀 Starting Modular API (modular_api.py) on port 8001...")
        
        try:
            cmd = [sys.executable, "modular_api.py"]
            self.modular_process = subprocess.Popen(
                cmd,
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("✅ Modular API started (PID: {})".format(self.modular_process.pid))
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start modular API: {e}")
            return False
    
    def check_api_health(self, port, api_name):
        """Check if API is healthy"""
        import requests
        try:
            response = requests.get(f"http://localhost:{port}/api/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ {api_name} health check passed")
                return True
        except Exception as e:
            logger.warning(f"⚠️ {api_name} health check failed: {e}")
        return False
    
    def wait_for_startup(self):
        """Wait for both APIs to start up"""
        logger.info("⏳ Waiting for APIs to start up...")
        
        max_retries = 30
        legacy_ready = False
        modular_ready = False
        
        for i in range(max_retries):
            if not legacy_ready:
                legacy_ready = self.check_api_health(8000, "Legacy API")
            
            if not modular_ready:
                modular_ready = self.check_api_health(8001, "Modular API")
            
            if legacy_ready and modular_ready:
                logger.info("🎉 Both APIs are ready!")
                return True
            
            time.sleep(2)
        
        logger.warning("⚠️ Timeout waiting for APIs to start")
        return False
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed"""
        logger.info("👁️ Monitoring both API processes...")
        
        while True:
            try:
                # Check legacy API
                if self.legacy_process and self.legacy_process.poll() is not None:
                    logger.warning("⚠️ Legacy API process died, restarting...")
                    self.start_legacy_api()
                
                # Check modular API
                if self.modular_process and self.modular_process.poll() is not None:
                    logger.warning("⚠️ Modular API process died, restarting...")
                    self.start_modular_api()
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal, shutting down...")
                self.shutdown()
                break
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
    
    def shutdown(self):
        """Shutdown both API processes"""
        logger.info("🛑 Shutting down APIs...")
        
        if self.legacy_process:
            try:
                self.legacy_process.terminate()
                self.legacy_process.wait(timeout=10)
                logger.info("✅ Legacy API shut down")
            except:
                self.legacy_process.kill()
                logger.warning("⚠️ Force killed legacy API")
        
        if self.modular_process:
            try:
                self.modular_process.terminate()
                self.modular_process.wait(timeout=10)
                logger.info("✅ Modular API shut down")
            except:
                self.modular_process.kill()
                logger.warning("⚠️ Force killed modular API")
    
    def run(self):
        """Run both APIs in parallel"""
        logger.info("🚀 Starting Parallel API Runner...")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("🛑 Received shutdown signal")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start both APIs
        legacy_started = self.start_legacy_api()
        modular_started = self.start_modular_api()
        
        if not legacy_started and not modular_started:
            logger.error("❌ Failed to start any APIs")
            return False
        
        # Wait for startup
        if legacy_started or modular_started:
            self.wait_for_startup()
        
        # Show status
        self.show_status()
        
        # Monitor processes
        self.monitor_processes()
        
        return True
    
    def show_status(self):
        """Show current status of both APIs"""
        logger.info("\n" + "="*60)
        logger.info("📊 API STATUS")
        logger.info("="*60)
        
        if self.legacy_process:
            legacy_status = "Running" if self.legacy_process.poll() is None else "Stopped"
            logger.info(f"Legacy API (port 8000): {legacy_status}")
            logger.info(f"  PID: {self.legacy_process.pid}")
            logger.info(f"  URL: http://localhost:8000/api/health")
        
        if self.modular_process:
            modular_status = "Running" if self.modular_process.poll() is None else "Stopped"
            logger.info(f"Modular API (port 8001): {modular_status}")
            logger.info(f"  PID: {self.modular_process.pid}")
            logger.info(f"  URL: http://localhost:8001/api/health")
        
        logger.info("="*60)
        logger.info("💡 Use Ctrl+C to shutdown both APIs")
        logger.info("="*60 + "\n")

def main():
    """Main entry point"""
    runner = ParallelAPIRunner()
    
    try:
        return runner.run()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        runner.shutdown()
        return True
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        runner.shutdown()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
