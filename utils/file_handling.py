from pathlib import Path
import re
import shutil
import logging
from .metadata import update_metadata, get_original_metadata

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

def process_file(file_path, destination_dir, dry_run, move, api, gather=False):
    """Process a single file."""
    try:
        logger.info(f"Processing {file_path}")
        
        # Get original metadata
        original_metadata = get_original_metadata(file_path)
        
        # Clean filename for search
        clean_name = clean_filename(file_path.name)
        
        # Get track information from API
        track_info = api.search_track(clean_name)
        
        if track_info:
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