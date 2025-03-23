from abc import ABC, abstractmethod

class MusicAPI(ABC):
    """Base class for music APIs"""
    
    @abstractmethod
    def search_track(self, filename, original_metadata=None, original_filename=None, duration=None, current_file=None, total_files=None):
        """Search for track information"""
        pass
    
    @abstractmethod
    def get_cover_art(self, track_id):
        """Get cover art for track"""
        pass 