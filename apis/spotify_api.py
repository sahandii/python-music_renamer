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
                client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
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

    def search_track(self, filename):
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
                    
                    # Check if this is an exact match with the filename
                    if filename.lower().find(track_artist.lower()) != -1 and \
                       filename.lower().find(track_title.lower()) != -1:
                        perfect_match = track
                    
                    choices.append((choice_str, track))
                
                # Only auto-select if we have an exact match
                if perfect_match:
                    logger.info(f"Found exact match: '{perfect_match['name']}' by {perfect_match['artists'][0]['name']}")
                    return self._create_track_info(perfect_match)
                
                # Otherwise, show selection menu
                if choices:
                    # Add custom search and skip options
                    choices.append(("Custom search...", "CUSTOM_SEARCH"))
                    choices.append(("Skip this file", None))
                    
                    # Show selection menu
                    questions = [
                        inquirer.List('selection',
                                    message=f'Select the correct match for "{filename}":',
                                    choices=[c[0] for c in choices])
                    ]
                    answers = inquirer.prompt(questions)
                    
                    if answers:
                        if answers['selection'] == "Custom search...":
                            custom_result = self._custom_search(filename)
                            if custom_result:
                                return custom_result
                        elif answers['selection'] != "Skip this file":
                            selected_track = next(c[1] for c in choices if c[0] == answers['selection'])
                            return self._create_track_info(selected_track)
                
                logger.info(f"No matches found for {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching Spotify: {str(e)}")
            return None

    def _custom_search(self, filename):
        """Helper method to perform a custom search."""
        questions = [
            inquirer.Text('query',
                         message=f'Enter search query for "{filename}" (e.g., artist song):')
        ]
        answers = inquirer.prompt(questions)
        
        if answers and answers['query'].strip():
            query = answers['query'].strip()
            results = self.sp.search(q=query, type='track', limit=20)
            
            if results['tracks']['items']:
                choices = []
                for track in results['tracks']['items']:
                    album = track['album']
                    choice_str = f"{track['artists'][0]['name']} - {track['name']} ({album['name']})"
                    choices.append((choice_str, track))
                
                # Add options to try again or skip
                choices.append(("Try another search", "CUSTOM_SEARCH"))
                choices.append(("Skip this file", None))
                
                # Show selection menu
                questions = [
                    inquirer.List('selection',
                                message=f'Select the correct match for "{filename}":',
                                choices=[c[0] for c in choices])
                ]
                answers = inquirer.prompt(questions)
                
                if answers:
                    if answers['selection'] == "Try another search":
                        return self._custom_search(filename)
                    elif answers['selection'] != "Skip this file":
                        selected_track = next(c[1] for c in choices if c[0] == answers['selection'])
                        return self._create_track_info(selected_track)
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