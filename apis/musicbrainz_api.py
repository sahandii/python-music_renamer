from .base_api import MusicAPI
import musicbrainzngs
import logging
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

class MusicBrainzAPI(MusicAPI):
    def __init__(self):
        musicbrainzngs.set_useragent(
            "MusicOrganizer",
            "0.1",
            "https://github.com/yourusername/music-organizer"
        )
    
    def search_track(self, filename):
        # Existing MusicBrainz search logic from get_track_info
        # ... (move the existing MusicBrainz-specific code here)
        pass
    
    def get_cover_art(self, release_id):
        # Existing cover art logic
        if not release_id:
            return None
            
        try:
            url = f"http://coverartarchive.org/release/{release_id}/front"
            response = requests.get(url, allow_redirects=True)
            
            if response.status_code == 200:
                return response.content
        except Exception as e:
            logger.debug(f"Could not fetch cover art: {str(e)}")
        
        return None 