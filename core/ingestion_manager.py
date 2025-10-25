"""
Advanced Ingestion Queue Manager
Handles bulk ingestion with filtering, progress tracking, and queue management
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Will import at runtime to avoid circular dependencies
# from scripts.ingest_account import IdempotentIngestionManager
# from tiktok_transcriber import TikTokTranscriber


class IngestionStatus(str, Enum):
    """Status of ingestion job"""
    QUEUED = "queued"
    FETCHING_METADATA = "fetching_metadata"
    FILTERING = "filtering"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    EXTRACTING_TOPICS = "extracting_topics"
    EMBEDDING = "embedding"
    COMPLETE = "complete"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class VideoFilter:
    """Video filtering configuration"""
    # Count filters
    last_n_videos: Optional[int] = None  # Last N videos
    percentage: Optional[float] = None  # Top X% by views
    
    # Date filters
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    
    # History segment filter (0.0 to 1.0 range for start/end)
    history_start: Optional[float] = None  # 0.0 = oldest
    history_end: Optional[float] = None    # 1.0 = newest
    
    # Speech filters
    only_with_speech: bool = False
    skip_no_speech: bool = True
    
    # Topic filters (micro - video level)
    required_tags: Optional[List[str]] = None  # Videos must have these tags
    
    # Account filter (macro - account level)
    required_category: Optional[str] = None  # Account must have this category


@dataclass
class IngestionSettings:
    """Ingestion behavior settings"""
    whisper_mode: str = "balanced"  # fast, balanced, accurate, ultra
    skip_existing: bool = True
    retranscribe_low_confidence: bool = False
    max_duration_minutes: Optional[int] = None  # Stop after X minutes


@dataclass
class VideoProgress:
    """Progress for a single video"""
    video_id: str
    title: str
    status: IngestionStatus
    step: Optional[str] = None  # downloading, transcribing, topics, embedding
    progress: float = 0.0  # 0.0 to 100.0 (percentage)
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class AccountProgress:
    """Progress for an account ingestion"""
    username: str
    status: IngestionStatus
    total_videos: int = 0
    filtered_videos: int = 0
    processed_videos: int = 0
    skipped_videos: int = 0
    failed_videos: int = 0
    overall_progress: float = 0.0  # 0-100 percentage
    current_video: Optional[VideoProgress] = None
    videos: Optional[List[VideoProgress]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.videos is None:
            self.videos = []
    
    def update_progress(self):
        """Calculate overall progress based on video statuses"""
        if self.filtered_videos == 0:
            self.overall_progress = 0.0
            return
        
        # Calculate based on processed + skipped (skipped are already done from previous runs or intentionally skipped)
        done = self.processed_videos + self.skipped_videos
        self.overall_progress = min(round((done / self.filtered_videos) * 100, 1), 100.0)


@dataclass
class IngestionJob:
    """Complete ingestion job"""
    job_id: str
    usernames: List[str]
    filters: VideoFilter
    settings: IngestionSettings
    status: IngestionStatus
    accounts: List[AccountProgress]
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_duration_seconds: float = 0.0
    overall_progress: float = 0.0  # 0-100 percentage
    eta_seconds: Optional[float] = None
    
    def update_progress(self):
        """Calculate overall job progress"""
        if not self.accounts:
            self.overall_progress = 0.0
            return
        
        total_progress = sum(acc.overall_progress for acc in self.accounts)
        self.overall_progress = round(total_progress / len(self.accounts), 1)
    
    def calculate_eta(self):
        """Calculate ETA based on elapsed time and progress"""
        if not self.started_at or self.overall_progress == 0:
            self.eta_seconds = None
            return
        
        elapsed = (datetime.now() - datetime.fromisoformat(self.started_at)).total_seconds()
        
        if self.overall_progress >= 100:
            self.eta_seconds = 0
            return
        
        # ETA = (elapsed / progress) * (100 - progress)
        rate = elapsed / self.overall_progress
        remaining = 100 - self.overall_progress
        self.eta_seconds = round(rate * remaining)


class IngestionQueueManager:
    """Manages ingestion queue with filtering and progress tracking"""
    
    def __init__(self, base_dir: str = "accounts"):
        self.jobs: Dict[str, IngestionJob] = {}
        self.active_job_id: Optional[str] = None
        self.lock = asyncio.Lock()
        self.base_dir = Path(base_dir)
        
    def create_job(
        self,
        usernames: List[str],
        filters: Optional[Dict] = None,
        settings: Optional[Dict] = None
    ) -> str:
        """Create a new ingestion job"""
        job_id = str(uuid.uuid4())
        
        # Parse filters
        filter_obj = VideoFilter(**(filters or {}))
        settings_obj = IngestionSettings(**(settings or {}))
        
        # Create account progress trackers
        accounts = [
            AccountProgress(
                username=username.lstrip('@'),
                status=IngestionStatus.QUEUED
            )
            for username in usernames
        ]
        
        job = IngestionJob(
            job_id=job_id,
            usernames=[u.lstrip('@') for u in usernames],
            filters=filter_obj,
            settings=settings_obj,
            status=IngestionStatus.QUEUED,
            accounts=accounts,
            created_at=datetime.now().isoformat()
        )
        
        self.jobs[job_id] = job
        return job_id
    
    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status as dict"""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        # Update progress calculations
        for acc in job.accounts:
            acc.update_progress()
        job.update_progress()
        job.calculate_eta()
        
        # Calculate elapsed time
        elapsed_seconds = 0
        if job.started_at:
            if job.completed_at:
                elapsed_seconds = (
                    datetime.fromisoformat(job.completed_at) - 
                    datetime.fromisoformat(job.started_at)
                ).total_seconds()
            else:
                elapsed_seconds = (
                    datetime.now() - 
                    datetime.fromisoformat(job.started_at)
                ).total_seconds()
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "overall_progress": job.overall_progress,
            "eta_seconds": job.eta_seconds,
            "elapsed_seconds": round(elapsed_seconds, 1),
            "usernames": job.usernames,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "total_duration_seconds": job.total_duration_seconds,
            "accounts": [
                {
                    "username": acc.username,
                    "status": acc.status.value,
                    "overall_progress": acc.overall_progress,
                    "total_videos": acc.total_videos,
                    "filtered_videos": acc.filtered_videos,
                    "processed_videos": acc.processed_videos,
                    "skipped_videos": acc.skipped_videos,
                    "failed_videos": acc.failed_videos,
                    "counters": {
                        "total": acc.filtered_videos,
                        "processed": acc.processed_videos,
                        "skipped": acc.skipped_videos,
                        "failed": acc.failed_videos
                    },
                    "current_video": {
                        "video_id": acc.current_video.video_id,
                        "title": acc.current_video.title,
                        "status": acc.current_video.status.value,
                        "step": acc.current_video.step,
                        "progress": acc.current_video.progress
                    } if acc.current_video else None,
                    "videos": [
                        {
                            "video_id": v.video_id,
                            "title": v.title,
                            "status": v.status.value,
                            "step": v.step,
                            "progress": v.progress
                        }
                        for v in acc.videos
                    ] if acc.videos else [],
                    "error": acc.error
                }
                for acc in job.accounts
            ]
        }
    
    def list_jobs(self) -> List[Dict]:
        """List all jobs"""
        return [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "usernames": job.usernames,
                "created_at": job.created_at,
                "account_count": len(job.accounts)
            }
            for job in self.jobs.values()
        ]
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job"""
        async with self.lock:
            job = self.jobs.get(job_id)
            if not job or job.status not in [IngestionStatus.QUEUED, IngestionStatus.DOWNLOADING, IngestionStatus.TRANSCRIBING]:
                return False
            
            job.status = IngestionStatus.PAUSED
            return True
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        async with self.lock:
            job = self.jobs.get(job_id)
            if not job or job.status != IngestionStatus.PAUSED:
                return False
            
            job.status = IngestionStatus.QUEUED
            # Will be picked up by the worker
            return True
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        async with self.lock:
            job = self.jobs.get(job_id)
            if not job or job.status in [IngestionStatus.COMPLETE, IngestionStatus.CANCELLED]:
                return False
            
            job.status = IngestionStatus.CANCELLED
            job.completed_at = datetime.now().isoformat()
            return True
    
    async def fetch_video_metadata(self, username: str) -> List[Dict]:
        """Fetch video metadata for filtering"""
        import sys
        from pathlib import Path
        
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from tiktok_transcriber import TikTokTranscriber
        
        transcriber = TikTokTranscriber()
        videos = transcriber.fetch_account_videos(username)
        return videos
    
    def apply_filters(self, videos: List[Dict], filters: VideoFilter, username: str) -> List[Dict]:
        """Apply filters to video list"""
        if not videos:
            return []
        
        filtered = videos.copy()
        
        # Check account category (macro filter)
        if filters.required_category:
            category_file = Path("accounts") / username / "topics" / "account_category.json"
            if category_file.exists():
                with open(category_file, 'r') as f:
                    cat_data = json.load(f)
                    if cat_data.get('category') != filters.required_category:
                        # Account doesn't match category, skip all videos
                        return []
            else:
                # No category file, skip if filter requires one
                return []
        
        # Sort by date (oldest to newest) for history segment filtering
        filtered = sorted(filtered, key=lambda v: v.get('create_time', 0))
        
        # Apply history segment filter (first/middle/recent)
        if filters.history_start is not None or filters.history_end is not None:
            total = len(filtered)
            start_idx = int((filters.history_start or 0.0) * total)
            end_idx = int((filters.history_end or 1.0) * total)
            filtered = filtered[start_idx:end_idx]
        
        # Apply last N videos filter (most recent)
        if filters.last_n_videos:
            filtered = filtered[-filters.last_n_videos:]
        
        # Apply percentage filter (top X% by views)
        if filters.percentage:
            filtered = sorted(filtered, key=lambda v: v.get('view_count', 0), reverse=True)
            count = max(1, int(len(filtered) * (filters.percentage / 100.0)))
            filtered = filtered[:count]
        
        # Apply date filters
        if filters.date_from:
            from_timestamp = datetime.fromisoformat(filters.date_from.replace('Z', '+00:00')).timestamp()
            filtered = [v for v in filtered if v.get('create_time', 0) >= from_timestamp]
        
        if filters.date_to:
            to_timestamp = datetime.fromisoformat(filters.date_to.replace('Z', '+00:00')).timestamp()
            filtered = [v for v in filtered if v.get('create_time', 0) <= to_timestamp]
        
        # Apply tag filters (micro - requires tags to exist)
        if filters.required_tags:
            # Load video tags
            video_tags = {}
            topics_dir = Path("accounts") / username / "topics"
            if topics_dir.exists():
                for tag_file in topics_dir.glob("*_tags.json"):
                    video_id = tag_file.stem.replace('_tags', '')
                    with open(tag_file, 'r') as f:
                        tag_data = json.load(f)
                        video_tags[video_id] = [t.get('tag', '').lower() for t in tag_data.get('tags', [])]
            
            required_tags_lower = [t.lower() for t in filters.required_tags]
            filtered = [
                v for v in filtered
                if v.get('video_id') in video_tags and 
                any(tag in video_tags[v['video_id']] for tag in required_tags_lower)
            ]
        
        return filtered
    
    async def run_ingestion(self, job_id: str):
        """Run the actual ingestion for a job - calls the WORKING CLI script"""
        import subprocess
        import re
        import threading
        from queue import Queue
        
        job = self.jobs.get(job_id)
        if not job:
            return
        
        job.status = IngestionStatus.FETCHING_METADATA
        job.started_at = datetime.now().isoformat()
        start_time = datetime.now()
        
        for account_progress in job.accounts:
            if job.status == IngestionStatus.CANCELLED:
                break
            
            username = account_progress.username
            account_progress.status = IngestionStatus.FETCHING_METADATA
            account_progress.started_at = datetime.now().isoformat()
            
            # Create dummy video progress for visual feedback
            account_progress.current_video = VideoProgress(
                video_id="fetching",
                title="Fetching video list...",
                status=IngestionStatus.FETCHING_METADATA,
                step="fetching_metadata",
                progress=10.0
            )
            
            try:
                logging.info(f"Starting ingestion for @{username}")
                
                # Build command for the working CLI script
                cmd = [
                    "python3",
                    "scripts/ingest_account.py",
                    "--user", username,
                    "--model-size", job.settings.whisper_mode
                ]
                
                if job.filters.last_n_videos:
                    cmd.extend(["--max-videos", str(job.filters.last_n_videos)])
                    account_progress.filtered_videos = job.filters.last_n_videos
                
                # Update to downloading status
                account_progress.status = IngestionStatus.DOWNLOADING
                account_progress.current_video.status = IngestionStatus.DOWNLOADING
                account_progress.current_video.step = "downloading"
                account_progress.current_video.progress = 25.0
                account_progress.current_video.title = "Downloading videos..."
                
                logging.info(f"Running: {' '.join(cmd)}")
                
                # Run subprocess in a thread to avoid blocking the event loop
                output_queue = Queue()
                process_done = threading.Event()
                
                def stream_output():
                    """Read subprocess output in a separate thread"""
                    process = None
                    try:
                        process = subprocess.Popen(
                            cmd,
                            cwd=str(self.base_dir.parent),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True
                        )
                        
                        for line in process.stdout:
                            output_queue.put(('line', line))
                        
                        process.wait()
                        output_queue.put(('done', process.returncode))
                    except Exception as e:
                        logging.error(f"Thread error: {e}")
                        import traceback
                        logging.error(traceback.format_exc())
                        output_queue.put(('error', str(e)))
                    finally:
                        if process:
                            try:
                                process.kill()
                            except:
                                pass
                        process_done.set()
                
                # Start the thread
                thread = threading.Thread(target=stream_output, daemon=True)
                thread.start()
                
                # Process output asynchronously
                output_lines = []
                current_video_num = 0
                total_videos_found = 0
                return_code = None
                
                from queue import Empty
                
                while not process_done.is_set() or not output_queue.empty():
                    try:
                        item_type, data = output_queue.get(timeout=0.1)
                        
                        if item_type == 'line':
                            line = data
                            output_lines.append(line)
                            logging.info(f"[{username}] {line.rstrip()}")
                            
                            # Parse progress from output
                            if "Total videos found:" in line:
                                match = re.search(r'Total videos found: (\d+)', line)
                                if match:
                                    total_videos_found = int(match.group(1))
                                    account_progress.total_videos = total_videos_found
                                    # Always update filtered_videos to match actual available videos
                                    account_progress.filtered_videos = total_videos_found
                            
                            if "Already processed:" in line or "Previously processed:" in line:
                                match = re.search(r'(?:Already|Previously) processed: (\d+)', line)
                                if match:
                                    account_progress.skipped_videos = int(match.group(1))
                            
                            if "New videos to process:" in line:
                                match = re.search(r'New videos to process: (\d+)', line)
                                if match:
                                    new_count = int(match.group(1))
                                    if account_progress.filtered_videos == 0:
                                        account_progress.filtered_videos = new_count
                            
                            # Track current video being processed
                            if re.match(r'\[\d+/\d+\] Processing:', line):
                                match = re.search(r'\[(\d+)/(\d+)\] Processing: (.+)', line)
                                if match:
                                    current_video_num = int(match.group(1))
                                    total = int(match.group(2))
                                    title = match.group(3).strip()
                                    
                                    account_progress.status = IngestionStatus.DOWNLOADING
                                    account_progress.current_video = VideoProgress(
                                        video_id=f"video_{current_video_num}",
                                        title=title[:80],
                                        status=IngestionStatus.DOWNLOADING,
                                        step="downloading",
                                        progress=round((current_video_num / total) * 40, 1)
                                    )
                            
                            if "[download]" in line and "100%" in line:
                                if account_progress.current_video:
                                    account_progress.current_video.step = "transcribing"
                                    account_progress.current_video.status = IngestionStatus.TRANSCRIBING
                                    account_progress.current_video.progress = round((current_video_num / max(account_progress.filtered_videos, 1)) * 60, 1)
                            
                            if "Transcribed" in line and "chars" in line:
                                if account_progress.current_video:
                                    account_progress.current_video.progress = round((current_video_num / max(account_progress.filtered_videos, 1)) * 100, 1)
                                    account_progress.current_video.status = IngestionStatus.COMPLETE
                                    account_progress.current_video.step = "complete"
                                    
                                    account_progress.videos.append(VideoProgress(
                                        video_id=account_progress.current_video.video_id,
                                        title=account_progress.current_video.title,
                                        status=IngestionStatus.COMPLETE,
                                        step="complete",
                                        progress=100.0,
                                        completed_at=datetime.now().isoformat()
                                    ))
                                    account_progress.processed_videos += 1
                            
                            if "SKIPPED (no speech)" in line:
                                if account_progress.current_video:
                                    account_progress.skipped_videos += 1
                        
                        elif item_type == 'done':
                            return_code = data
                        
                        elif item_type == 'error':
                            raise Exception(data)
                        
                        # Yield control to event loop periodically
                        await asyncio.sleep(0.01)
                        
                    except Empty:
                        # Queue empty, yield and continue
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        # Real error in parsing - log but continue
                        logging.error(f"Error processing output: {e}")
                        import traceback
                        logging.error(traceback.format_exc())
                        await asyncio.sleep(0.1)
                
                full_output = ''.join(output_lines)
                
                if return_code == 0:
                    # Final parse to ensure we got the counts
                    if "TRANSCRIBED and SAVED" in full_output:
                        match = re.search(r'(\d+) new videos.*TRANSCRIBED', full_output)
                        if match:
                            final_count = int(match.group(1))
                            if account_progress.processed_videos < final_count:
                                account_progress.processed_videos = final_count
                    
                    if account_progress.processed_videos == 0 and total_videos_found == 0:
                        account_progress.status = IngestionStatus.FAILED
                        account_progress.error = "No videos found for this account"
                        logging.warning(f"⚠️  No videos found for @{username}")
                    else:
                        account_progress.status = IngestionStatus.COMPLETE
                        logging.info(f"✅ Completed ingestion for @{username}: {account_progress.processed_videos} videos")
                else:
                    account_progress.status = IngestionStatus.FAILED
                    account_progress.error = f"Script failed with exit code {return_code}"
                    logging.error(f"❌ Failed: {full_output[-500:]}")
                
                account_progress.completed_at = datetime.now().isoformat()
                account_progress.current_video = None
                
            except subprocess.TimeoutExpired:
                logging.error(f"Ingestion timeout for @{username}")
                account_progress.status = IngestionStatus.FAILED
                account_progress.error = "Ingestion timeout (>1 hour)"
                account_progress.completed_at = datetime.now().isoformat()
                account_progress.current_video = None
                
            except Exception as e:
                logging.error(f"Error ingesting account @{username}: {e}")
                import traceback
                logging.error(traceback.format_exc())
                account_progress.status = IngestionStatus.FAILED
                account_progress.error = str(e)
                account_progress.completed_at = datetime.now().isoformat()
                account_progress.current_video = None
        
        # Run post-processing for all accounts
        logging.info("🔄 Running post-processing: topics and embeddings...")
        try:
            from topic_extractor import AccountTopicManager
            from topic_extractor_v2 import TopicExtractorV2
            from umbrella_builder import UmbrellaBuilder
            from core.semantic_search.engine import TranscriptIndexer
            
            indexer = TranscriptIndexer()
            
            for account_progress in job.accounts:
                if job.status == IngestionStatus.CANCELLED:
                    break
                    
                logging.info(f"Checking {account_progress.username}: status={account_progress.status}, processed={account_progress.processed_videos}")
                if account_progress.status == IngestionStatus.COMPLETE and account_progress.processed_videos > 0:
                    try:
                        # Extract topics (V1 for backward compatibility)
                        account_progress.status = IngestionStatus.EXTRACTING_TOPICS
                        account_progress.current_video = VideoProgress(
                            video_id="post_processing",
                            title="Extracting topics (V1)...",
                            status=IngestionStatus.EXTRACTING_TOPICS,
                            step="topics",
                            progress=70.0
                        )
                        
                        logging.info(f"📝 Extracting topics V1 for @{account_progress.username}...")
                        manager = AccountTopicManager(account_progress.username)
                        manager.extract_all_topics(force=False)
                        logging.info(f"✅ Topics V1 extracted for @{account_progress.username}")
                        
                        # Extract topics V2 (enhanced with evidence, confidence, canonicalization)
                        account_progress.current_video.title = "Extracting topics (V2)..."
                        account_progress.current_video.progress = 75.0
                        
                        logging.info(f"📝 Extracting topics V2 for @{account_progress.username}...")
                        v2_extractor = TopicExtractorV2()
                        v2_extractor.extract_account_topics_v2(account_progress.username, force=False)
                        logging.info(f"✅ Topics V2 extracted for @{account_progress.username}")
                        
                        # Generate umbrella clusters
                        account_progress.current_video.title = "Building topic umbrellas..."
                        account_progress.current_video.progress = 80.0
                        
                        logging.info(f"🌂 Building umbrella clusters for @{account_progress.username}...")
                        umbrella_builder = UmbrellaBuilder()
                        result = umbrella_builder.build_account_umbrellas(account_progress.username, max_umbrellas=5)
                        if result:
                            logging.info(f"✅ Built {result['umbrella_count']} umbrellas (top {result['umbrella_count']} of {result.get('total_clusters', result['umbrella_count'])} clusters) from {result['total_topics']} topics")
                        else:
                            logging.warning(f"⚠️  Could not build umbrellas for @{account_progress.username}")
                        
                        logging.info(f"✅ All topic processing complete for @{account_progress.username}")
                        
                        # Index for search
                        account_progress.status = IngestionStatus.EMBEDDING
                        account_progress.current_video.status = IngestionStatus.EMBEDDING
                        account_progress.current_video.step = "embedding"
                        account_progress.current_video.title = "Generating embeddings..."
                        account_progress.current_video.progress = 90.0
                        
                        logging.info(f"🔍 Indexing @{account_progress.username} for search...")
                        result = indexer.index_account(account_progress.username)
                        logging.info(f"✅ Indexed {result['processed']} transcripts ({result['total_segments']} segments)")
                        
                        # Mark as fully complete
                        account_progress.status = IngestionStatus.COMPLETE
                        account_progress.current_video = None
                        account_progress.overall_progress = 100.0
                        
                    except Exception as e:
                        logging.error(f"❌ Post-processing failed for {account_progress.username}: {e}")
                        import traceback
                        logging.error(traceback.format_exc())
                        account_progress.current_video = None
                else:
                    logging.info(f"⏭️  Skipping {account_progress.username} - not eligible for post-processing")
            
            logging.info("✅ Post-processing complete")
            
        except Exception as e:
            logging.error(f"❌ Post-processing error: {e}")
            import traceback
            logging.error(traceback.format_exc())
        
        # Job complete
        if job.status != IngestionStatus.CANCELLED:
            job.status = IngestionStatus.COMPLETE
        job.completed_at = datetime.now().isoformat()
        job.total_duration_seconds = (datetime.now() - start_time).total_seconds()


# Global queue manager instance
queue_manager = IngestionQueueManager()
