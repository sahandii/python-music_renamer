# Music Organizer

A command-line tool to organize your music files by analyzing their metadata using the Spotify API.

## Supported Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)

## Installation

1. Clone this repository
2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Set up your API keys:

- Create a new application on the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and get the `client_id` and `client_secret`.

4. Run the script:

```bash
python music_organizer.py SOURCE_DIR DESTINATION_DIR
```

## Command-Line Options

The following flags can be used to customize the behavior:

- `--dry-run`: Show what would be done without making actual changes
- `--workers N`: Number of parallel workers (default: 4)
- `--threshold N`: Confidence threshold for automatic matching (0-100, default: 98)
- `--move`: Move files instead of copying them
- `--gather`: Place all files directly in the destination directory without organizing into subdirectories

### Example Usage

```bash
# Basic usage - copy and organize files using Spotify API
python music_organizer.py ./my_music ./organized_music

# Move files instead of copying
python music_organizer.py ./my_music ./organized_music --move

# Test run without making changes
python music_organizer.py ./my_music ./organized_music --dry-run

# Gather all files in destination without subdirectories
python music_organizer.py ./my_music ./organized_music --gather
```
