from pathlib import Path
import re
import shutil
import logging
from .metadata import update_metadata, get_original_metadata, get_audio_duration

logger = logging.getLogger(__name__)

def sanitize_path(path_string):
    """Remove invalid characters from path."""
    return re.sub(r'[<>:"/\\|?*]', '', path_string)

def clean_filename(filename):
    """Remove common patterns from filename to help with matching."""
    # Remove file extension
    filename = Path(filename).stem
    
    # Remove common patterns like (Official Video), [HD], etc.
    patterns = [
        r'\(.*?\)',  # Anything in parentheses
        r'\[.*?\]',  # Anything in square brackets
        r'Official.*?Video',
        r'HD',
        r'HQ',
        r'\d{3,4}p',  # Resolution patterns like 720p, 1080p
    ]
    
    for pattern in patterns:
        filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
    
    return filename.strip()

def process_file(file_path, destination_dir, dry_run, move, api, gather=False, current_file=None, total_files=None):
    """Process a single file."""
    try:
        logger.info(f"Processing {file_path}")
        
        # Get original metadata
        original_metadata = get_original_metadata(file_path)
        
        # Get audio duration
        duration = get_audio_duration(file_path)
        
        # Clean filename for search
        clean_name = clean_filename(file_path.name)
        
        # Get track information from API - pass both clean name and original metadata
        track_info = api.search_track(clean_name, original_metadata, file_path.name, duration, current_file, total_files)
        
        if track_info == "TRANSFER_ONLY":
            # Special case: Transfer file without changing metadata
            if gather:
                dest_dir = Path(destination_dir)
                dest_file = dest_dir / file_path.name
            else:
                # Use original metadata if available, or just the filename
                if original_metadata and original_metadata != f"Unknown - {Path(file_path).stem} (Unknown Album)":
                    parts = original_metadata.split(' - ')
                    artist = parts[0] if len(parts) > 1 else "Unknown"
                    title_album = parts[1] if len(parts) > 1 else original_metadata
                    title = title_album.split(' (')[0] if ' (' in title_album else title_album
                    dest_dir = Path(destination_dir) / sanitize_path(artist)
                    dest_file = dest_dir / file_path.name
                else:
                    # No useful metadata, put in "Unknown" folder
                    dest_dir = Path(destination_dir) / "Unknown"
                    dest_file = dest_dir / file_path.name
            
            if not dry_run:
                # Just copy/move the file without updating metadata
                dest_dir.mkdir(parents=True, exist_ok=True)
                if move:
                    shutil.move(str(file_path), str(dest_file))
                    logger.info(f"Moved {file_path} to {dest_file} (no metadata changes)")
                else:
                    shutil.copy2(str(file_path), str(dest_file))
                    logger.info(f"Copied {file_path} to {dest_file} (no metadata changes)")
            else:
                action = "move" if move else "copy"
                logger.info(f"Would {action} {file_path} to {dest_file} (no metadata changes)")
            
            return True, (original_metadata, "No change")
        elif track_info:
            # Create destination path based on gather flag
            if gather:
                dest_dir = Path(destination_dir)
                dest_file = dest_dir / f"{sanitize_path(track_info['artist'])} - {sanitize_path(track_info['title'])}{file_path.suffix}"
            else:
                dest_dir = Path(destination_dir) / sanitize_path(track_info['artist']) / sanitize_path(track_info['album'])
                dest_file = dest_dir / f"{sanitize_path(track_info['title'])}{file_path.suffix}"
            
            if not dry_run:
                # First copy/move the file
                dest_dir.mkdir(parents=True, exist_ok=True)
                if move:
                    shutil.move(str(file_path), str(dest_file))
                    logger.info(f"Moved {file_path} to {dest_file}")
                else:
                    shutil.copy2(str(file_path), str(dest_file))
                    logger.info(f"Copied {file_path} to {dest_file}")
                
                # Then update metadata on the destination file
                update_metadata(dest_file, track_info, api)
            else:
                action = "move" if move else "copy"
                logger.info(f"Would {action} {file_path} to {dest_file}")
            
            # Format new metadata
            new_metadata = f"{track_info['artist']} - {track_info['title']} ({track_info['album']})"
            
            return True, (original_metadata, new_metadata)
        else:
            logger.warning(f"Could not find track information for {file_path}")
            return False, (original_metadata, None)
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False, (None, None) 