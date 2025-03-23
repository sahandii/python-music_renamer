from .base_api import MusicAPI
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
from dotenv import load_dotenv
import os
import requests
import re
from thefuzz import fuzz
import inquirer
from pathlib import Path

logger = logging.getLogger(__name__)

class SpotifyAPI(MusicAPI):
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Initialize Spotify client
        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
            )
        )
    
    def _clean_filename(self, filename):
        """Clean up filename to extract artist and title."""
        # Remove file extension
        filename = Path(filename).stem
        
        # Remove leading track numbers (e.g., "01 ", "01_", "01-")
        filename = re.sub(r'^(\d{1,3}[\s_-]+)', '', filename)
        
        # Remove common patterns
        patterns = [
            r'\(feat\..*?\)',  # Featuring
            r'\(ft\..*?\)',    # Ft.
            r'\(featuring.*?\)', # Featuring
            r'\(with.*?\)',    # With
            r'\[.*?\]',        # Anything in square brackets
            r'\|.*$',          # Everything after pipe symbol
        ]
        
        for pattern in patterns:
            filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
        
        return filename.strip()

    def _extract_search_terms(self, filename):
        """Extract artist and title from filename or metadata."""
        clean_filename = self._clean_filename(filename)
        parts = re.split(r' - ', clean_filename, maxsplit=1)
        
        if len(parts) == 2:
            return f"{parts[0]} {parts[1]}"  # Simple space-separated artist and title
        
        # If no separator found, clean up the filename and return it
        return re.sub(r'^(\d{1,3}[\s_-]+)', '', clean_filename)

    def search_track(self, filename, original_metadata=None, original_filename=None, duration=None, current_file=None, total_files=None):
        try:
            # Get search terms from filename
            search_query = self._extract_search_terms(filename)
            results = self.sp.search(q=search_query, type='track', limit=5)  # Reduced from 20 to 5
            
            if results['tracks']['items']:
                choices = []
                perfect_match = None
                
                for track in results['tracks']['items']:
                    track_artist = track['artists'][0]['name']
                    track_title = track['name']
                    album = track['album']
                    
                    # Create display string
                    choice_str = f"{track_artist} - {track_title} ({album['name']})"
                    
                    # Check for exact matches more effectively
                    # Case 1: The song title and artist both appear in the filename
                    filename_matches_track = (
                        filename.lower().find(track_title.lower()) != -1 and 
                        filename.lower().find(track_artist.lower()) != -1
                    )
                    
                    # Case 2: The original metadata matches exactly
                    metadata_matches_track = False
                    if original_metadata:
                        expected_metadata = f"{track_artist} - {track_title} ({album['name']})"
                        metadata_matches_track = original_metadata.lower() == expected_metadata.lower()
                    
                    # Case 3: First result is exact match for the search query (useful for well-formatted filenames)
                    is_first_result = track == results['tracks']['items'][0]
                    clean_filename = self._clean_filename(filename)
                    formatted_filename = clean_filename.lower().replace(' - ', ' ')
                    search_string = f"{track_artist} {track_title}".lower()
                    search_match = (
                        is_first_result and
                        (formatted_filename == search_string or
                         formatted_filename.startswith(search_string) or
                         search_string.startswith(formatted_filename))
                    )
                    
                    # Case 4: The example "Fleetwood Mac - Peacekeeper" case
                    display_filename = original_filename if original_filename else Path(filename).name
                    exact_match_in_list = choice_str == f"{original_metadata}"
                    
                    # Determine perfect match
                    if filename_matches_track or metadata_matches_track or search_match or exact_match_in_list:
                        perfect_match = track
                        logger.info(f"Found perfect match: '{track_title}' by {track_artist}")
                    
                    choices.append((choice_str, track))
                
                # Only auto-select if we have an exact match
                if perfect_match:
                    logger.info(f"Auto-selecting perfect match: '{perfect_match['name']}' by {perfect_match['artists'][0]['name']}")
                    return self._create_track_info(perfect_match)
                
                # Otherwise, show selection menu
                if choices:
                    # Add custom search and skip options
                    choices.append(("Custom search...", "CUSTOM_SEARCH"))
                    choices.append(("Enter Spotify track URL/ID...", "SPOTIFY_ID"))
                    choices.append(("Transfer song, no ID change", "TRANSFER_ONLY"))
                    choices.append(("Skip song", None))
                    
                    # Print file information first, before launching inquirer
                    display_filename = original_filename if original_filename else Path(filename).name
                    metadata_display = original_metadata if original_metadata and original_metadata != f"Unknown - {Path(filename).stem} (Unknown Album)" else f"Unknown - {Path(filename).stem} (Unknown Album)"
                    
                    # Show track progress if available
                    if current_file is not None and total_files is not None:
                        print(f"[Track {current_file}/{total_files}]")
                    
                    print(f"[{metadata_display}]")
                    print(f'"{display_filename}"')
                    if duration and duration != "Unknown":
                        print(f"Length: {duration}")
                    print("─" * 40 + "\n")
                    
                    # Use standardized inquirer format to prevent duplication
                    try:
                        # Only display the list choice prompt without file info
                        questions = [
                            inquirer.List('selection',
                                        message="Select the correct match:",
                                        choices=[c[0] for c in choices])
                        ]
                        
                        # For terminal compatibility, don't use carousel option
                        answers = inquirer.prompt(questions)
                        
                        if answers:
                            if answers['selection'] == "Custom search...":
                                # Clear any possible duplicate lines
                                os.system('clear' if os.name != 'nt' else 'cls')
                                custom_result = self._custom_search(filename, original_metadata, original_filename, duration, current_file, total_files)
                                if custom_result:
                                    return custom_result
                            elif answers['selection'] == "Enter Spotify track URL/ID...":
                                # Clear any possible duplicate lines
                                os.system('clear' if os.name != 'nt' else 'cls')
                                # Print file information again
                                print("\n" + "─" * 40)
                                print("File Information:")
                                if current_file is not None and total_files is not None:
                                    print(f"[Track {current_file}/{total_files}]")
                                print(f"[{metadata_display}]")
                                print(f'"{display_filename}"')
                                if duration and duration != "Unknown":
                                    print(f"Length: {duration}")
                                print("─" * 40 + "\n")
                                # Prompt for Spotify track URL or ID
                                print("Enter Spotify track URL or ID (e.g., https://open.spotify.com/track/1fRHO3Bi9Pze9cCbk0qzTf or 1fRHO3Bi9Pze9cCbk0qzTf):")
                                track_id_or_url = input("> ")
                                if track_id_or_url.strip():
                                    track_result = self.get_track_by_id(track_id_or_url)
                                    if track_result:
                                        return track_result
                                    else:
                                        print("Invalid Spotify track URL or ID. Returning to search...")
                                        return self.search_track(filename, original_metadata, original_filename, duration, current_file, total_files)
                            elif answers['selection'] == "Transfer song, no ID change":
                                return "TRANSFER_ONLY"
                            elif answers['selection'] != "Skip song":
                                selected_track = next(c[1] for c in choices if c[0] == answers['selection'])
                                return self._create_track_info(selected_track)
                    except Exception as e:
                        logger.error(f"Error displaying selection menu: {str(e)}")
                        # Fallback to numbered list if inquirer fails
                        print("Available matches:")
                        for i, choice in enumerate(choices):
                            print(f"  {i+1}. {choice[0]}")
                        
                        try:
                            selection = input("\nEnter number of your selection: ")
                            idx = int(selection) - 1
                            if 0 <= idx < len(choices):
                                if choices[idx][1] == "CUSTOM_SEARCH":
                                    return self._custom_search(filename, original_metadata, original_filename, duration, current_file, total_files)
                                elif choices[idx][1] == "SPOTIFY_ID":
                                    # Prompt for Spotify track URL or ID
                                    print("Enter Spotify track URL or ID:")
                                    track_id_or_url = input("> ")
                                    if track_id_or_url.strip():
                                        track_result = self.get_track_by_id(track_id_or_url)
                                        if track_result:
                                            return track_result
                                elif choices[idx][1] == "TRANSFER_ONLY":
                                    return "TRANSFER_ONLY"
                                elif choices[idx][1] is not None:
                                    return self._create_track_info(choices[idx][1])
                        except:
                            pass
                    
                    return None
                
                logger.info(f"No matches found for {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching Spotify: {str(e)}")
            return None

    def _custom_search(self, filename, original_metadata=None, original_filename=None, duration=None, current_file=None, total_files=None):
        """Helper method to perform a custom search."""
        # Format display filename and metadata
        display_filename = original_filename if original_filename else Path(filename).name
        metadata_display = original_metadata if original_metadata and original_metadata != f"Unknown - {Path(filename).stem} (Unknown Album)" else f"Unknown - {Path(filename).stem} (Unknown Album)"
        
        # Print file information first
        print("\n" + "─" * 40)
        print("File Information:")
        
        # Show track progress if available
        if current_file is not None and total_files is not None:
            print(f"[Track {current_file}/{total_files}]")
        
        print(f"[{metadata_display}]")
        print(f'"{display_filename}"')
        if duration and duration != "Unknown":
            print(f"Length: {duration}")
        print("─" * 40 + "\n")
        
        # Get search query directly - no options for Track ID in custom search
        print("Enter search query (e.g., artist song):")
        query = input("> ")
        
        if query.strip():
            results = self.sp.search(q=query.strip(), type='track', limit=20)
            
            if results['tracks']['items']:
                choices = []
                for track in results['tracks']['items']:
                    album = track['album']
                    choice_str = f"{track['artists'][0]['name']} - {track['name']} ({album['name']})"
                    choices.append((choice_str, track))
                
                # Add options to try again or skip - NO Spotify ID option here
                choices.append(("Try another search", "CUSTOM_SEARCH"))
                choices.append(("Transfer song, no ID change", "TRANSFER_ONLY"))
                choices.append(("Skip song", None))
                
                # Print choices manually to avoid inquirer issues
                print("\n" + "─" * 40)
                print("File Information:")
                
                # Show track progress if available
                if current_file is not None and total_files is not None:
                    print(f"[Track {current_file}/{total_files}]")
                
                print(f"[{metadata_display}]")
                print(f'"{display_filename}"')
                if duration and duration != "Unknown":
                    print(f"Length: {duration}")
                print("─" * 40 + "\n")
                
                # Use standardized inquirer format to prevent duplication
                try:
                    # Only display the list choice prompt without file info
                    questions = [
                        inquirer.List('selection',
                                     message="Select the correct match:",
                                     choices=[c[0] for c in choices])
                    ]
                    
                    # For terminal compatibility, don't use carousel option
                    answers = inquirer.prompt(questions)
                    
                    if answers:
                        if answers['selection'] == "Try another search":
                            # Clear any possible duplicate lines
                            os.system('clear' if os.name != 'nt' else 'cls')
                            return self._custom_search(filename, original_metadata, original_filename, duration, current_file, total_files)
                        elif answers['selection'] == "Transfer song, no ID change":
                            return "TRANSFER_ONLY"
                        elif answers['selection'] != "Skip song":
                            selected_track = next(c[1] for c in choices if c[0] == answers['selection'])
                            return self._create_track_info(selected_track)
                except Exception as e:
                    logger.error(f"Error displaying selection menu: {str(e)}")
                    # Fallback to numbered list if inquirer fails
                    print("Available matches:")
                    for i, choice in enumerate(choices):
                        print(f"  {i+1}. {choice[0]}")
                    
                    try:
                        selection = input("\nEnter number of your selection: ")
                        idx = int(selection) - 1
                        if 0 <= idx < len(choices):
                            if choices[idx][1] == "CUSTOM_SEARCH":
                                return self._custom_search(filename, original_metadata, original_filename, duration, current_file, total_files)
                            elif choices[idx][1] == "TRANSFER_ONLY":
                                return "TRANSFER_ONLY"
                            elif choices[idx][1] is not None:
                                return self._create_track_info(choices[idx][1])
                    except:
                        pass
        
        return None

    def get_cover_art(self, album_id):
        try:
            # Get album details
            album = self.sp.album(album_id)
            if album['images']:
                # Get the largest image (first in the list)
                image_url = album['images'][0]['url']
                response = requests.get(image_url)
                if response.status_code == 200:
                    return response.content
            return None
        except Exception as e:
            logger.error(f"Error fetching cover art: {str(e)}")
            return None
    
    def _get_artist_genres(self, artist_id):
        try:
            artist = self.sp.artist(artist_id)
            if artist['genres']:
                return artist['genres'][0]  # Return first genre
        except:
            pass
        return "Unknown Genre"

    def _create_track_info(self, track):
        """Helper method to create track info dictionary."""
        album = track['album']
        return {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'album': album['name'],
            'year': album['release_date'][:4],
            'genre': self._get_artist_genres(track['artists'][0]['id']),
            'release_id': album['id'],
            'track_number': str(track['track_number']),
            'album_artist': album['artists'][0]['name']
        }

    def get_track_by_id(self, track_id_or_url):
        """Get track info directly from a Spotify track ID or URL."""
        try:
            # Extract track ID from URL if needed
            if "spotify.com/track/" in track_id_or_url:
                track_id = track_id_or_url.split("spotify.com/track/")[1].split("?")[0].strip()
            else:
                track_id = track_id_or_url.strip()
            
            # Get track info from Spotify API
            track = self.sp.track(track_id)
            if track:
                logger.info(f"Found track by ID: '{track['name']}' by {track['artists'][0]['name']}")
                return self._create_track_info(track)
            
            return None
        except Exception as e:
            logger.error(f"Error getting track by ID: {str(e)}")
            return None 