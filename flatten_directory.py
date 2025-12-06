#!/usr/bin/env python3
"""
Flatten a directory structure by moving all files from subdirectories to the root level.
Logs warnings when filename conflicts occur.
"""

import os
import shutil
import logging
from pathlib import Path
import argparse


def setup_logging():
    """Configure logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('flatten_directory.log'),
            logging.StreamHandler()
        ]
    )


def flatten_directory(root_dir, dry_run=False):
    """
    Flatten a directory structure by moving all files to the root level.
    
    Args:
        root_dir (str): Path to the directory to flatten
        dry_run (bool): If True, only simulate the operation without moving files
    """
    root_path = Path(root_dir).resolve()
    
    if not root_path.exists():
        logging.error(f"Directory does not exist: {root_path}")
        return
    
    if not root_path.is_dir():
        logging.error(f"Path is not a directory: {root_path}")
        return
    
    logging.info(f"{'[DRY RUN] ' if dry_run else ''}Flattening directory: {root_path}")
    
    # Track files that already exist at root level to detect conflicts
    existing_files = set()
    files_to_move = []
    
    # First pass: collect all files and detect conflicts
    for dirpath, dirnames, filenames in os.walk(root_path):
        current_dir = Path(dirpath)
        
        # Skip the root directory itself
        if current_dir == root_path:
            # Track files already at root level
            for filename in filenames:
                existing_files.add(filename)
            continue
        
        # Collect files from subdirectories
        for filename in filenames:
            source_path = current_dir / filename
            target_path = root_path / filename
            
            # Check for conflicts
            if filename in existing_files:
                logging.warning(
                    f"Filename conflict detected: '{filename}' "
                    f"already exists at root level. Source: {source_path.relative_to(root_path)}"
                )
                # Generate a unique name by adding parent directory prefix
                relative_parent = current_dir.relative_to(root_path)
                safe_filename = f"{str(relative_parent).replace('/', '_')}_{filename}"
                target_path = root_path / safe_filename
                logging.info(f"Renaming to: {safe_filename}")
            
            files_to_move.append((source_path, target_path))
            existing_files.add(target_path.name)
    
    # Second pass: move the files
    moved_count = 0
    for source_path, target_path in files_to_move:
        try:
            if dry_run:
                logging.info(f"Would move: {source_path.relative_to(root_path)} -> {target_path.name}")
            else:
                shutil.move(str(source_path), str(target_path))
                logging.info(f"Moved: {source_path.relative_to(root_path)} -> {target_path.name}")
            moved_count += 1
        except Exception as e:
            logging.error(f"Error moving {source_path}: {e}")
    
    # Third pass: remove empty subdirectories
    if not dry_run:
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
            current_dir = Path(dirpath)
            
            # Skip the root directory
            if current_dir == root_path:
                continue
            
            # Remove empty directories
            try:
                if not any(current_dir.iterdir()):
                    current_dir.rmdir()
                    logging.info(f"Removed empty directory: {current_dir.relative_to(root_path)}")
            except Exception as e:
                logging.warning(f"Could not remove directory {current_dir}: {e}")
    
    logging.info(
        f"{'[DRY RUN] ' if dry_run else ''}"
        f"Flattening complete. {moved_count} files {'would be' if dry_run else ''} moved."
    )


def main():
    parser = argparse.ArgumentParser(
        description='Flatten a directory structure by moving all files to the root level.'
    )
    parser.add_argument(
        'directory',
        help='Path to the directory to flatten'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate the operation without actually moving files'
    )
    
    args = parser.parse_args()
    
    setup_logging()
    flatten_directory(args.directory, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

