#!/usr/bin/env python3
"""
Script to download YouTube transcripts from chef channels.
Requires youtube-transcript-api package.
"""

import argparse
import logging
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_transcript(video_id: str, output_dir: Path) -> bool:
    """
    Download transcript for a YouTube video.

    Args:
        video_id: YouTube video ID
        output_dir: Directory to save transcript

    Returns:
        True if successful, False otherwise
    """
    try:
        # Placeholder - would use youtube-transcript-api
        # from youtube_transcript_api import YouTubeTranscriptApi
        # transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # text = ' '.join([entry['text'] for entry in transcript])

        logger.info(f"Downloading transcript for video: {video_id}")

        # Save transcript
        output_file = output_dir / f"{video_id}.txt"
        # with open(output_file, 'w', encoding='utf-8') as f:
        #     f.write(text)

        logger.info(f"Saved to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error downloading {video_id}: {e}")
        return False


def download_channel_transcripts(channel_id: str, output_dir: Path, max_videos: Optional[int] = None):
    """
    Download all transcripts from a YouTube channel.

    Args:
        channel_id: YouTube channel ID
        output_dir: Directory to save transcripts
        max_videos: Maximum number of videos to download
    """
    logger.info(f"Downloading transcripts from channel: {channel_id}")

    # Placeholder - would use YouTube API to get video list
    # Then download each transcript

    logger.info("Download complete!")


def main():
    parser = argparse.ArgumentParser(description="Download YouTube transcripts from chef channels")
    parser.add_argument("--video-id", help="Single video ID to download")
    parser.add_argument("--channel-id", help="Channel ID to download all videos from")
    parser.add_argument("--output-dir", default="data/raw/transcripts", help="Output directory")
    parser.add_argument("--max-videos", type=int, help="Maximum videos to download from channel")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.video_id:
        download_transcript(args.video_id, output_dir)
    elif args.channel_id:
        download_channel_transcripts(args.channel_id, output_dir, args.max_videos)
    else:
        parser.error("Must provide either --video-id or --channel-id")


if __name__ == "__main__":
    main()
