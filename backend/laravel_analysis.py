#!/usr/bin/env python3
"""
Laravel detection analysis for repository enhancer
"""

import sys
import json
import asyncio
import os
from repository_enhancer import RepositoryEnhancer

async def analyze_laravel_detection(repo_url):
    """Analyze Laravel detection capabilities"""
    print(f"Testing Laravel detection for: {repo_url}")
    
    try:
        enhancer = RepositoryEnhancer()
        result = await enhancer.clone_and_enhance_repository(repo_url, "laravel_analysis")
        
        # Analysis results
        print("\n" + "="*60)
        print("FRAMEWORK DETECTION ANALYSIS")
        print("="*60)
        
        # Check framework detection
        if 'framework' in result:
            fw_info = result['framework']
            fw_type = fw_info.get('type', 'unknown')
            fw_confidence = fw_info.get('confidence', 0)
            print(f"Framework Detected: {fw_type} (confidence: {fw_confidence:.2f})")
            print(f"Framework Scores: {fw_info.get('scores', {})}")
        else:
            print("No framework detection found")
        
        # Check plugin detection  
        if 'plugin_detection' in result:
            plugin = result['plugin_detection']
            print(f"Plugin Framework: {plugin.get('framework', 'N/A')}")
            print(f"Build Tool: {plugin.get('build_tool', 'N/A')}")
            print(f"Build Ready: {plugin.get('is_build_ready', False)}")
        else:
            print("No plugin detection found")
            
        # Check validation
        if 'validation' in result:
            val = result['validation']
            print(f"Validation Build Ready: {val.get('is_build_ready', False)}")
            print(f"Build Commands: {val.get('build_commands', [])}")
        
        # Success indicator
        laravel_detected = (
            result.get('framework', {}).get('type') == 'laravel' or
            (result.get('plugin_detection', {}).get('framework') == 'laravel')
        )
        
        if laravel_detected:
            print("\nSUCCESS: Laravel framework properly detected!")
            return True
        else:
            print("\nWARNING: Laravel not detected or wrong framework detected")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python laravel_analysis.py <repo_url>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    success = asyncio.run(analyze_laravel_detection(repo_url))
    sys.exit(0 if success else 1)
