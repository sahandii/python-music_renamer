# Music Organizer

A command-line tool to organize your music files by analyzing their metadata using the Spotify API.

## Supported Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)

## Features

- Automatically match music files with Spotify metadata
- Apply accurate metadata including artist, title, album, and cover art
- Organize files into folders by artist and album
- Resume interrupted processing with the `--start` parameter
- Manually search for tracks by name or enter Spotify track URLs directly
- Support for multiple audio formats
- Cross-platform compatibility

## Installation

1. Clone this repository

2. Install Python and pip:
   - Visit [Python's official website](https://www.python.org/downloads/)
   - Download and install the latest version of Python for your operating system
   - During installation, make sure to check "Add Python to PATH"
   - Verify the installation by running:
     ```bash
     python3 --version
     pip3 --version
     ```

3. Install requirements:

```bash
pip3 install -r requirements.txt
```

4. Set up your API keys:

- Create a new application on the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and get the `client_id` and `client_secret`.
- Create a `.env` file in the root directory of the project
- Add your Spotify API credentials to the `.env` file in the following format:
  ```
  SPOTIPY_CLIENT_ID="your_client_id_here"
  SPOTIPY_CLIENT_SECRET="your_client_secret_here"
  ```
- Make sure to replace `your_client_id_here` and `your_client_secret_here` with your actual Spotify API credentials
- The `.env` file is already included in `.gitignore`, so your credentials will remain secure

5. Run the script:

```bash
python3 music_organizer.py SOURCE_DIR DESTINATION_DIR
```

## Command-Line Options

The following flags can be used to customize the behavior:

- `--dry-run`: Show what would be done without making actual changes
- `--workers N`: Number of parallel workers (default: 4)
- `--threshold N`: Confidence threshold for automatic matching (0-100, default: 98)
- `--move`: Move files instead of copying them
- `--gather`: Place all files directly in the destination directory without organizing into subdirectories
- `--start N`: Skip the first N files (useful for resuming an interrupted processing)

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

# Resume processing from the 101st file
python music_organizer.py ./my_music ./organized_music --start=101
```

## Using Spotify Track URLs

For songs that are difficult to match automatically, you can directly use a Spotify track URL or ID. During the matching process:

1. Select "Enter Spotify track URL/ID..." from the options
2. Paste the URL from Spotify (e.g., `https://open.spotify.com/track/1fRHO3Bi9Pze9cCbk0qzTf`) or just the ID portion
3. The tool will fetch and apply metadata directly from the specified track

This is useful when:
- You already know exactly which track should match your file
- The automatic matching isn't finding the correct song
- You want to ensure perfect metadata for important tracks
