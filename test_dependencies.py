#!/usr/bin/env python3
"""
Test script to verify all dependencies are working
"""

import sys
import subprocess

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        if package_name:
            print(f"   Install with: pip install {package_name}")
        return False

def test_command(command):
    """Test if a command is available"""
    try:
        # Use -version for ffmpeg, --version for others
        version_flag = '-version' if command == 'ffmpeg' else '--version'
        result = subprocess.run([command, version_flag], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {command}: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {command}: Command failed")
            return False
    except FileNotFoundError:
        print(f"❌ {command}: Not found")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ {command}: Timeout")
        return False

def main():
    """Test all dependencies"""
    print("🧪 Testing TikTok Transcription Pipeline Dependencies")
    print("=" * 60)
    
    # Test Python modules
    print("\n📦 Python Modules:")
    modules = [
        ("yt_dlp", "yt-dlp"),
        ("faster_whisper", "faster-whisper"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("pathlib", None),
        ("json", None),
        ("logging", None),
        ("tempfile", None),
        ("subprocess", None),
        ("datetime", None),
    ]
    
    python_ok = True
    for module, package in modules:
        if not test_import(module, package):
            python_ok = False
    
    # Test system commands
    print("\n🔧 System Commands:")
    commands = ["ffmpeg", "python3"]
    
    system_ok = True
    for command in commands:
        if not test_command(command):
            system_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPENDENCY TEST SUMMARY")
    print("=" * 60)
    
    if python_ok and system_ok:
        print("🎉 All dependencies are working!")
        print("\n🚀 Ready to use TikTok Transcription Pipeline:")
        print("   python3 tiktok_transcriber.py username")
        return True
    else:
        print("⚠️  Some dependencies are missing.")
        print("\n🔧 To fix:")
        print("   1. Install system dependencies: brew install ffmpeg")
        print("   2. Install Python dependencies: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
