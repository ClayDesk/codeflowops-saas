"""
Simple test to validate health check improvements
Run this to test if our new health system works
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_health_checker():
    """Test the new health checker system"""
    try:
        from src.utils.health_checker import health_checker
        
        print("Testing new comprehensive health check system...")
        print("=" * 50)
        
        # Test individual components
        print("1. Testing Database connectivity...")
        db_result = await health_checker.check_database()
        print(f"   Database: {db_result.get('status', 'unknown')}")
        if db_result.get('response_time_ms'):
            print(f"   Response time: {db_result['response_time_ms']}ms")
        
        print("\n2. Testing Redis connectivity...")
        redis_result = await health_checker.check_redis()
        print(f"   Redis: {redis_result.get('status', 'unknown')}")
        if redis_result.get('response_time_ms'):
            print(f"   Response time: {redis_result['response_time_ms']}ms")
        
        print("\n3. Testing System resources...")
        system_result = await health_checker.check_system_resources()
        print(f"   System: {system_result.get('status', 'unknown')}")
        
        print("\n4. Running comprehensive health check...")
        comprehensive_result = await health_checker.comprehensive_health_check()
        print(f"   Overall Status: {comprehensive_result.get('status', 'unknown')}")
        print(f"   Total Check Time: {comprehensive_result.get('total_check_time_ms', 0)}ms")
        
        print("\n" + "=" * 50)
        print("Health Check Test Results:")
        print("=" * 50)
        
        components = comprehensive_result.get('components', {})
        for component, status in components.items():
            print(f"{component.capitalize()}: {status.get('status', 'unknown')}")
            if status.get('error'):
                print(f"  Error: {status['error'][:100]}...")
        
        return comprehensive_result.get('status') == 'healthy'
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure you're running this from the backend directory")
        return False
    except Exception as e:
        print(f"Test Error: {e}")
        return False

if __name__ == "__main__":
    print("CodeFlowOps Health Check Test")
    print("=" * 50)
    
    # Set some environment variables for testing
    os.environ.setdefault("DATABASE_URL", "postgresql://codeflowops_adm:Allah4596adm@codeflowops-postgres.cluster-c4fi4mgye971.us-east-1.rds.amazonaws.com:5432/codeflowops")
    os.environ.setdefault("REDIS_URL", "redis://master.codeflowops-redis.xlsvbh.use1.cache.amazonaws.com:6379/0")
    
    success = asyncio.run(test_health_checker())
    
    if success:
        print("\n✅ Health check system is working properly!")
    else:
        print("\n❌ Health check system has issues that need attention.")
    
    print("\nNext steps:")
    print("1. Deploy this to your Elastic Beanstalk environment")
    print("2. Test the /health endpoint from your load balancer")
    print("3. Monitor the health check response times")
