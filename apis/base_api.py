from abc import ABC, abstractmethod

class MusicAPI(ABC):
    """Base class for music APIs"""
    
    @abstractmethod
    def search_track(self, filename):
        """Search for track information"""
        pass
    
    @abstractmethod
    def get_cover_art(self, track_id):
        """Get cover art for track"""
        pass 