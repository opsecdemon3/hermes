#!/usr/bin/env python3
"""Test if save_transcription works"""

from pathlib import Path
from tiktok_transcriber import TikTokTranscriber

# Create transcriber
transcriber = TikTokTranscriber(output_dir="accounts")

# Set output_dir like we do in ingestion_manager
transcriber.output_dir = Path("accounts/test_account/transcriptions")
transcriber.output_dir.mkdir(parents=True, exist_ok=True)

# Test save
test_result = {
    "video_id": "test123",
    "title": "Test Video",
    "timestamp": "2025-10-22T12:00:00",
    "transcription": "This is a test transcription.",
    "transcription_length": 29
}

print(f"output_dir is set to: {transcriber.output_dir}")
print(f"output_dir type: {type(transcriber.output_dir)}")
print(f"output_dir exists: {transcriber.output_dir.exists()}")

try:
    transcriber.save_transcription("test123", test_result)
    print("✅ Save succeeded")
    
    # Check if file exists
    expected_file = transcriber.output_dir / "test123_transcript.txt"
    if expected_file.exists():
        print(f"✅ File created: {expected_file}")
        print(f"File contents:")
        print(expected_file.read_text())
    else:
        print(f"❌ File NOT created at: {expected_file}")
        
except Exception as e:
    print(f"❌ Save failed: {e}")
    import traceback
    traceback.print_exc()
