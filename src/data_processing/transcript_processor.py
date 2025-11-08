"""
Transcript processing module for chef AI training.
Handles loading, cleaning, and preprocessing of YouTube transcript data.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """Process and clean chef YouTube transcripts for AI training."""

    def __init__(self, raw_data_dir: str = "data/raw/transcripts",
                 processed_data_dir: str = "data/processed/cleaned"):
        """
        Initialize the transcript processor.

        Args:
            raw_data_dir: Directory containing raw transcript files
            processed_data_dir: Directory for processed output
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def load_transcript(self, file_path: Path) -> Optional[str]:
        """
        Load a transcript from a file.

        Args:
            file_path: Path to transcript file

        Returns:
            Transcript content or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def clean_transcript(self, text: str) -> str:
        """
        Clean transcript text by removing timestamps, formatting, etc.

        Args:
            text: Raw transcript text

        Returns:
            Cleaned transcript text
        """
        # Remove timestamps (e.g., [00:12:34])
        text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove speaker labels if present (e.g., "Speaker 1:")
        text = re.sub(r'^Speaker \d+:\s*', '', text, flags=re.MULTILINE)

        # Clean up excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text.strip()

    def extract_metadata(self, file_path: Path) -> Dict[str, str]:
        """
        Extract metadata from transcript filename or content.

        Args:
            file_path: Path to transcript file

        Returns:
            Dictionary of metadata
        """
        # Extract channel/chef name from directory structure or filename
        parts = file_path.parts
        metadata = {
            'filename': file_path.name,
            'channel': parts[-2] if len(parts) > 1 else 'unknown',
            'path': str(file_path)
        }
        return metadata

    def process_all_transcripts(self) -> List[Dict]:
        """
        Process all transcripts in the raw data directory.

        Returns:
            List of processed transcript dictionaries
        """
        processed_data = []

        # Find all transcript files (common formats)
        file_patterns = ['*.txt', '*.md', '*.json']
        transcript_files = []

        for pattern in file_patterns:
            transcript_files.extend(self.raw_data_dir.rglob(pattern))

        logger.info(f"Found {len(transcript_files)} transcript files")

        for file_path in transcript_files:
            logger.info(f"Processing {file_path.name}")

            content = self.load_transcript(file_path)
            if content is None:
                continue

            cleaned_content = self.clean_transcript(content)
            metadata = self.extract_metadata(file_path)

            processed_entry = {
                'text': cleaned_content,
                'metadata': metadata
            }

            processed_data.append(processed_entry)

        return processed_data

    def save_processed_data(self, data: List[Dict], output_file: str = "processed_transcripts.jsonl"):
        """
        Save processed transcripts to JSONL format.

        Args:
            data: List of processed transcript dictionaries
            output_file: Output filename
        """
        output_path = self.processed_data_dir / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in data:
                f.write(json.dumps(entry) + '\n')

        logger.info(f"Saved {len(data)} processed transcripts to {output_path}")

    def run(self):
        """Execute the full processing pipeline."""
        logger.info("Starting transcript processing pipeline")
        processed_data = self.process_all_transcripts()
        self.save_processed_data(processed_data)
        logger.info("Processing complete!")


if __name__ == "__main__":
    processor = TranscriptProcessor()
    processor.run()
