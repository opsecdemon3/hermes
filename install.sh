#!/bin/bash
# TikTok Transcription Pipeline Installation Script

echo "🚀 Installing TikTok Transcription Pipeline"
echo "=========================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg not found. Installing..."
    
    # Detect OS and install ffmpeg
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo "❌ Homebrew not found. Please install ffmpeg manually:"
            echo "   https://ffmpeg.org/download.html"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt update
            sudo apt install -y ffmpeg
        elif command -v yum &> /dev/null; then
            sudo yum install -y ffmpeg
        else
            echo "❌ Package manager not found. Please install ffmpeg manually:"
            echo "   https://ffmpeg.org/download.html"
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install ffmpeg manually:"
        echo "   https://ffmpeg.org/download.html"
        exit 1
    fi
else
    echo "✅ ffmpeg found: $(ffmpeg -version | head -n1)"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Test installation
echo "🧪 Testing installation..."
python3 test_dependencies.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Installation complete!"
    echo ""
    echo "🚀 Usage:"
    echo "   python3 tiktok_transcriber.py username"
    echo ""
    echo "📖 For more options:"
    echo "   python3 tiktok_transcriber.py --help"
else
    echo "❌ Installation test failed"
    exit 1
fi
