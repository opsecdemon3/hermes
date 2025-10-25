#!/usr/bin/env python3
"""
TikTok Transcription Pipeline
Real yt-dlp + faster-whisper implementation for TikTok video transcription
Multi-account support with authentication and retry logic
"""

import os
import sys
import json
import logging
import tempfile
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import yt_dlp
from faster_whisper import WhisperModel
import pandas as pd

# Load environment variables
load_dotenv()

class TikTokTranscriber:
    """Real TikTok transcription pipeline using yt-dlp and faster-whisper"""
    
    def __init__(self, 
                 output_dir: str = "accounts",
                 temp_dir: str = "/tmp/tiktok_transcriber",
                 model_size: str = "small",
                 max_videos: Optional[int] = None,
                 cookies_file: Optional[str] = None,
                 min_speech_threshold: int = 50):
        """
        Initialize TikTok transcriber
        
        Args:
            output_dir: Base directory to save transcriptions (accounts/<username>/transcriptions)
            temp_dir: Temporary directory for audio files
            model_size: Whisper model size ('tiny', 'small', 'medium', 'large')
            max_videos: Maximum videos to process (None = use env var or default 10)
            cookies_file: Path to cookies.txt for authenticated scraping (optional)
            min_speech_threshold: Minimum characters to consider video has speech (default 50)
        """
        self.base_output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.model_size = model_size or os.getenv('WHISPER_MODEL_SIZE', 'small')
        
        # Get max_videos from parameter, env var, or default
        if max_videos is not None:
            self.max_videos = max_videos
        else:
            self.max_videos = int(os.getenv('MAX_VIDEOS', '10'))
        
        self.cookies_file = cookies_file
        self.min_speech_threshold = min_speech_threshold
        
        # Create directories
        self.base_output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize Whisper model
        self.whisper_model = None
        self.setup_whisper()
        
        # Processing stats
        self.stats = {
            'total_videos': 0,
            'processed_videos': 0,
            'failed_videos': 0,
            'skipped_videos': 0,
            'total_duration': 0.0,
            'processing_time': 0.0
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tiktok_transcriber.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_whisper(self):
        """Initialize faster-whisper model"""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            self.whisper_model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def process_account(self, username: str) -> Dict[str, Any]:
        """
        Process all videos for a TikTok account
        
        Args:
            username: TikTok username (without @)
            
        Returns:
            Processing results dictionary
        """
        start_time = datetime.now()
        
        # Clean username (remove @ if present)
        username = username.lstrip('@')
        
        # Setup output directory for this account
        self.output_dir = self.base_output_dir / username / "transcriptions"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Starting transcription for @{username}")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info(f"Max videos: {self.max_videos}")
        
        # Reset stats for this account
        self.stats = {
            'total_videos': 0,
            'processed_videos': 0,
            'failed_videos': 0,
            'skipped_videos': 0,
            'total_duration': 0.0,
            'processing_time': 0.0
        }
        
        try:
            # Get account videos
            videos = self.fetch_account_videos(username)
            self.stats['total_videos'] = len(videos)
            
            if not videos:
                self.logger.warning(f"No videos found for @{username}")
                return {"error": "No videos found", "videos": [], "stats": self.stats}
            
            self.logger.info(f"Found {len(videos)} videos, processing up to {self.max_videos}")
            
            # Process each video
            processed_videos = []
            for i, video in enumerate(videos[:self.max_videos], 1):
                self.logger.info(f"Processing video {i}/{min(len(videos), self.max_videos)}: {video.get('title', 'Unknown')}")
                
                try:
                    result = self.process_single_video(video)
                    if result.get('success'):
                        processed_videos.append(result)
                        self.stats['processed_videos'] += 1
                    elif result.get('skipped'):
                        self.stats['skipped_videos'] += 1
                        self.logger.info(f"Skipped video (no speech detected): {video.get('video_id')}")
                    else:
                        self.stats['failed_videos'] += 1
                        self.logger.error(f"Failed to process video: {result.get('error')}")
                
                except Exception as e:
                    self.logger.error(f"Error processing video: {e}")
                    self.stats['failed_videos'] += 1
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats['processing_time'] = processing_time
            
            # Save results
            results = {
                "account": username,
                "processed_videos": processed_videos,
                "stats": self.stats,
                "timestamp": datetime.now().isoformat()
            }
            
            self.save_results(username, results)
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Completed transcription for @{username}")
            self.logger.info(f"Total videos found: {self.stats['total_videos']}")
            self.logger.info(f"Successfully processed: {self.stats['processed_videos']}")
            self.logger.info(f"Skipped (no speech): {self.stats['skipped_videos']}")
            self.logger.info(f"Failed: {self.stats['failed_videos']}")
            self.logger.info(f"Processing time: {processing_time:.2f}s")
            self.logger.info(f"{'='*60}\n")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to process account @{username}: {e}")
            return {"error": str(e), "videos": [], "stats": self.stats}
    
    def fetch_account_videos(self, username: str, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch video metadata using yt-dlp with retry logic and authentication support
        
        Args:
            username: TikTok username
            max_retries: Maximum retry attempts
            
        Returns:
            List of video metadata dictionaries
        """
        account_url = f"https://www.tiktok.com/@{username}"
        
        # Build yt-dlp options
        ydl_opts = self._build_ydl_opts(extract_flat=False)
        ydl_opts['playlist_items'] = f"1:{self.max_videos}"
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Fetching videos for @{username} (attempt {attempt + 1}/{max_retries})")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(account_url, download=False)
                    
                    if not info:
                        self.logger.warning(f"No info returned for @{username}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return []
                    
                    # Handle both single video and playlist responses
                    entries = []
                    if 'entries' in info:
                        entries = [e for e in info['entries'] if e is not None]
                    elif info.get('id'):
                        # Single video response
                        entries = [info]
                    
                    if not entries:
                        self.logger.warning(f"No video entries found for @{username}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        return []
                    
                    # Parse video data
                    videos = []
                    for entry in entries[:self.max_videos]:
                        try:
                            video_data = {
                                'video_id': entry.get('id'),
                                'title': entry.get('title', ''),
                                'description': entry.get('description', ''),
                                'upload_date': entry.get('upload_date', ''),
                                'duration': entry.get('duration', 0),
                                'view_count': entry.get('view_count', 0),
                                'like_count': entry.get('like_count', 0),
                                'comment_count': entry.get('comment_count', 0),
                                'url': entry.get('webpage_url', '') or entry.get('url', ''),
                                'thumbnail': entry.get('thumbnail', ''),
                            }
                            
                            if video_data['video_id']:
                                videos.append(video_data)
                                self.logger.debug(f"Found video: {video_data.get('title', 'Unknown')}")
                        except Exception as e:
                            self.logger.warning(f"Failed to parse video entry: {e}")
                            continue
                    
                    if videos:
                        self.logger.info(f"Successfully found {len(videos)} videos for @{username}")
                        return videos
                    else:
                        self.logger.warning(f"No valid videos parsed for @{username}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                            
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for @{username}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} attempts failed for @{username}")
                    
        return []
    
    def _build_ydl_opts(self, extract_flat: bool = False) -> Dict[str, Any]:
        """
        Build yt-dlp options with headers, cookies, and fallback formats
        
        Args:
            extract_flat: Whether to extract flat (faster, less metadata)
            
        Returns:
            yt-dlp options dictionary
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': extract_flat,
            'format': 'best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'socket_timeout': 30,
            'retries': 3,
        }
        
        # Add cookies if available
        if self.cookies_file and Path(self.cookies_file).exists():
            opts['cookiefile'] = self.cookies_file
            self.logger.info(f"Using cookies from: {self.cookies_file}")
        
        return opts
    
    def process_single_video(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single video: download audio and transcribe
        Auto-skip videos with minimal/no speech
        
        Args:
            video: Video metadata dictionary
            
        Returns:
            Processing result dictionary
        """
        audio_path = None
        try:
            video_id = video.get('video_id')
            if not video_id:
                return {"success": False, "error": "No video ID"}
            
            # Download audio
            audio_path = self.download_audio(video)
            if not audio_path:
                return {"success": False, "error": "Failed to download audio"}
            
            # Transcribe audio
            transcription = self.transcribe_audio(audio_path)
            
            # Check if video has sufficient speech
            if not transcription or len(transcription) < self.min_speech_threshold:
                self.logger.info(f"Video {video_id} has minimal/no speech ({len(transcription) if transcription else 0} chars)")
                return {
                    "success": False,
                    "skipped": True,
                    "reason": "Minimal or no speech detected",
                    "transcription_length": len(transcription) if transcription else 0
                }
            
            # Save transcription
            result = {
                "success": True,
                "video_id": video_id,
                "title": video.get('title', ''),
                "transcription": transcription,
                "transcription_length": len(transcription),
                "video_metadata": video,
                "timestamp": datetime.now().isoformat()
            }
            
            self.save_transcription(video_id, result)
            self.logger.info(f"Successfully transcribed video {video_id} ({len(transcription)} chars)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing video {video.get('video_id')}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            # Always clean up audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp audio file {audio_path}: {e}")
    
    def download_audio(self, video: Dict[str, Any]) -> Optional[str]:
        """
        Download audio from video using yt-dlp with fallback formats
        
        Args:
            video: Video metadata dictionary
            
        Returns:
            Path to downloaded audio file or None if failed
        """
        try:
            video_url = video.get('url')
            if not video_url:
                self.logger.error("No video URL provided")
                return None
            
            video_id = video.get('video_id')
            
            # Create temporary audio file path
            audio_path = self.temp_dir / f"{video_id}.wav"
            
            # Build base options with headers and cookies
            ydl_opts = self._build_ydl_opts()
            
            # Add audio-specific options
            ydl_opts.update({
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': str(audio_path).replace('.wav', '.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
            })
            
            self.logger.debug(f"Downloading audio for video {video_id}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Check for downloaded audio file with different extensions
            audio_extensions = ['.wav', '.m4a', '.mp3', '.webm', '.ogg', '.opus']
            for ext in audio_extensions:
                test_path = self.temp_dir / f"{video_id}{ext}"
                if test_path.exists():
                    self.logger.debug(f"Downloaded audio: {test_path}")
                    return str(test_path)
            
            # If no audio file found, return None
            self.logger.error(f"No audio file found for video {video_id}")
            return None
                
        except Exception as e:
            self.logger.error(f"Failed to download audio for {video.get('video_id')}: {e}")
            return None
    
    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio using faster-whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            if not self.whisper_model:
                self.logger.error("Whisper model not initialized")
                return None
            
            # Transcribe audio
            segments, info = self.whisper_model.transcribe(
                audio_path,
                beam_size=5,
                language="en",  # You can detect language automatically
                condition_on_previous_text=True,
                initial_prompt="This is a TikTok video transcription."
            )
            
            # Combine segments into full text
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
            
            # Clean up text
            full_text = full_text.strip()
            
            if full_text:
                self.logger.info(f"Transcribed {len(full_text)} characters")
                return full_text
            else:
                self.logger.warning("No transcription generated")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to transcribe audio: {e}")
            return None
    
    def save_transcription(self, video_id: str, result: Dict[str, Any]):
        """Save transcription to file"""
        try:
            transcript_file = self.output_dir / f"{video_id}_transcript.txt"
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"# Transcription for Video {video_id}\n")
                f.write(f"Title: {result.get('title', 'Unknown')}\n")
                f.write(f"Timestamp: {result.get('timestamp')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(result.get('transcription', ''))
            
            self.logger.info(f"Saved transcription: {transcript_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save transcription: {e}")
    
    def save_results(self, username: str, results: Dict[str, Any]):
        """Save processing results to JSON file"""
        try:
            results_file = self.output_dir / f"{username}_results.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Saved results: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.stats.copy()


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='TikTok Transcription Pipeline - Multi-account support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tiktok_transcriber.py --user kwrt_
  python tiktok_transcriber.py --user matrix.v5 --max-videos 20
  python tiktok_transcriber.py --user beabettermandaily --cookies cookies.txt
        """
    )
    
    parser.add_argument('--user', '-u', required=True, help='TikTok username (with or without @)')
    parser.add_argument('--output-dir', default='accounts', help='Base output directory (default: accounts)')
    parser.add_argument('--model-size', default=None, choices=['tiny', 'small', 'medium', 'large'], 
                       help='Whisper model size (default: from env or "small")')
    parser.add_argument('--max-videos', type=int, default=None, 
                       help='Maximum videos to process (default: from env or 10)')
    parser.add_argument('--cookies', dest='cookies_file', default=None, 
                       help='Path to cookies.txt file for authenticated scraping')
    parser.add_argument('--min-speech', type=int, default=50,
                       help='Minimum characters to consider video has speech (default: 50)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"\n{'='*60}")
    print(f"TikTok Transcription Pipeline")
    print(f"{'='*60}")
    print(f"Account: @{args.user.lstrip('@')}")
    print(f"Max videos: {args.max_videos or os.getenv('MAX_VIDEOS', '10')}")
    print(f"Model size: {args.model_size or os.getenv('WHISPER_MODEL_SIZE', 'small')}")
    if args.cookies_file:
        print(f"Cookies: {args.cookies_file}")
    print(f"{'='*60}\n")
    
    # Initialize transcriber
    transcriber = TikTokTranscriber(
        output_dir=args.output_dir,
        model_size=args.model_size,
        max_videos=args.max_videos,
        cookies_file=args.cookies_file,
        min_speech_threshold=args.min_speech
    )
    
    # Process account
    results = transcriber.process_account(args.user)
    
    if results.get('error'):
        print(f"\n❌ Error: {results['error']}")
        sys.exit(1)
    
    # Print stats
    stats = results.get('stats', transcriber.get_stats())
    print(f"\n{'='*60}")
    print(f"✅ Processing Complete!")
    print(f"{'='*60}")
    print(f"Total videos found: {stats['total_videos']}")
    print(f"Successfully processed: {stats['processed_videos']}")
    print(f"Skipped (no speech): {stats['skipped_videos']}")
    print(f"Failed: {stats['failed_videos']}")
    print(f"Processing time: {stats['processing_time']:.2f}s")
    print(f"Results saved to: {transcriber.output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
