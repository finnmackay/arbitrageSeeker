#!/usr/bin/env python3
"""
Script to import transcripts from Obsidian vault.
Handles markdown files and preserves metadata.
"""

import argparse
import shutil
import logging
from pathlib import Path
from typing import List
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_obsidian_metadata(content: str) -> dict:
    """
    Extract YAML frontmatter from Obsidian markdown file.

    Args:
        content: File content

    Returns:
        Dictionary of metadata
    """
    metadata = {}

    # Check for YAML frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            # Parse YAML (simplified - would use yaml library)
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

    return metadata


def process_obsidian_file(file_path: Path) -> dict:
    """
    Process an Obsidian markdown file.

    Args:
        file_path: Path to Obsidian file

    Returns:
        Dictionary with content and metadata
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    metadata = extract_obsidian_metadata(content)

    # Remove frontmatter from content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    # Remove Obsidian-specific syntax
    # Remove wiki links [[link]]
    content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)

    # Remove tags #tag
    content = re.sub(r'#(\w+)', '', content)

    return {
        'content': content,
        'metadata': metadata,
        'source_file': str(file_path)
    }


def import_from_obsidian(obsidian_vault: Path, output_dir: Path, pattern: str = "**/*.md"):
    """
    Import transcript files from Obsidian vault.

    Args:
        obsidian_vault: Path to Obsidian vault
        output_dir: Output directory for transcripts
        pattern: Glob pattern for files to import
    """
    logger.info(f"Importing from Obsidian vault: {obsidian_vault}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all matching files
    files = list(obsidian_vault.glob(pattern))
    logger.info(f"Found {len(files)} files matching pattern '{pattern}'")

    for file_path in files:
        try:
            logger.info(f"Processing {file_path.name}")

            # Process the file
            result = process_obsidian_file(file_path)

            # Save to output directory
            output_file = output_dir / file_path.name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result['content'])

            logger.info(f"Saved to {output_file}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")

    logger.info(f"Import complete! Processed {len(files)} files")


def main():
    parser = argparse.ArgumentParser(description="Import transcripts from Obsidian vault")
    parser.add_argument("vault_path", help="Path to Obsidian vault")
    parser.add_argument("--output-dir", default="data/raw/transcripts",
                       help="Output directory for transcripts")
    parser.add_argument("--pattern", default="**/*.md",
                       help="Glob pattern for files to import")
    parser.add_argument("--subfolder", help="Specific subfolder in vault to import from")

    args = parser.parse_args()

    vault_path = Path(args.vault_path)

    if not vault_path.exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        return

    # Use subfolder if specified
    if args.subfolder:
        vault_path = vault_path / args.subfolder

    output_dir = Path(args.output_dir)

    import_from_obsidian(vault_path, output_dir, args.pattern)


if __name__ == "__main__":
    main()
