import click
from pathlib import Path
import logging
from tqdm import tqdm
from colorama import init, Fore, Style
from apis.spotify_api import SpotifyAPI
from utils.file_handling import process_file

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Initialize colorama
init()

@click.command()
@click.argument('source_dir', 
                type=click.Path(exists=True),
                metavar='SOURCE_DIR')
@click.argument('destination_dir', 
                type=click.Path(),
                metavar='DESTINATION_DIR')
@click.option('--dry-run', is_flag=True, help="Show what would be done without making changes")
@click.option('--workers', default=4, help="Number of parallel workers")
@click.option('--threshold', default=98, help="Confidence threshold for automatic matching (0-100)")
@click.option('--move', is_flag=True, help="Move files instead of copying them")
@click.option('--gather', is_flag=True, help="Place all files directly in the destination directory without organizing into subdirectories")
@click.option('--api', type=click.Choice(['spotify']), default='spotify', 
              help="API to use for music information")
def main(source_dir, destination_dir, dry_run, workers, threshold, move, gather, api):
    """Organize music files by analyzing their metadata.

    Arguments:
    
        SOURCE_DIR: Directory containing the music files to organize
        DESTINATION_DIR: Directory where organized music files will be placed
    """
    source_path = Path(source_dir)
    
    # Supported audio formats
    audio_extensions = {'.mp3', '.wav', '.m4a'}
    
    # Get list of all audio files
    audio_files = [
        f for f in source_path.rglob('*') 
        if f.suffix.lower() in audio_extensions
    ]
    
    if not audio_files:
        logger.warning(f"No supported audio files found in {source_dir}")
        return
    
    # Initialize the appropriate API
    music_api = SpotifyAPI()
    
    # Store metadata changes
    metadata_changes = []
    
    # Process files with progress bar
    with tqdm(total=len(audio_files), desc="Processing files", unit="file", 
             position=1, leave=False) as pbar:
        # Clear the current line before starting
        print("\033[K", end="")
        
        for file_path in audio_files:
            # Move cursor up one line and clear it
            print("\033[F\033[K", end="")
            
            success, (original, new) = process_file(file_path, destination_dir, dry_run, move, music_api, gather)
            metadata_changes.append((success, original, new))
            
            pbar.update(1)
            if success:
                pbar.set_postfix(status="Success")
            else:
                pbar.set_postfix(status="Failed")
            
            # Ensure cursor is at the bottom
            print()
    
    # Clear the progress bar
    print("\033[K", end="")
    
    # Show summary
    print("\nMetadata Changes Summary:")
    print("------------------------")
    successful_changes = 0
    failed_changes = 0
    
    for success, original, new in metadata_changes:
        if success and original and new:
            print(f"{Fore.YELLOW}{original}{Style.RESET_ALL} → {Fore.CYAN}{new}{Style.RESET_ALL}")
            successful_changes += 1
        elif original:
            print(f"{Fore.YELLOW}{original}{Style.RESET_ALL} → {Fore.RED}No match found{Style.RESET_ALL}")
            failed_changes += 1
    
    print(f"\nSummary:")
    print(f"Successfully processed: {Fore.GREEN}{successful_changes}{Style.RESET_ALL}")
    print(f"Failed to process: {Fore.RED}{failed_changes}{Style.RESET_ALL}")
    print(f"Total files: {len(audio_files)}")

if __name__ == '__main__':
    main() 