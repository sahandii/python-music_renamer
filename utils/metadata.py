from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover
import mutagen.id3
import mutagen
import logging
import requests
import math

logger = logging.getLogger(__name__)

def get_audio_duration(file_path):
    """Get the duration of an audio file in mm:ss format."""
    try:
        suffix = file_path.suffix.lower()
        if suffix == '.mp3':
            audio = mutagen.File(file_path)
            if audio and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                seconds = int(audio.info.length)
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                return f"{minutes}:{remaining_seconds:02d}"
        elif suffix == '.m4a':
            audio = MP4(file_path)
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                seconds = int(audio.info.length)
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                return f"{minutes}:{remaining_seconds:02d}"
        elif suffix == '.wav':
            audio = mutagen.File(file_path)
            if audio and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                seconds = int(audio.info.length)
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                return f"{minutes}:{remaining_seconds:02d}"
        return "Unknown"
    except Exception as e:
        logger.error(f"Error getting duration for {file_path}: {str(e)}")
        return "Unknown"

def get_original_metadata(file_path):
    """Get original metadata from file."""
    try:
        suffix = file_path.suffix.lower()
        if suffix == '.wav':
            return f"Unknown - {file_path.stem} (Unknown Album)"
        elif suffix == '.m4a':
            audio = MP4(file_path)
            artist = audio.get('\xa9ART', ['Unknown'])[0]
            title = audio.get('\xa9nam', [file_path.stem])[0]
            album = audio.get('\xa9alb', ['Unknown Album'])[0]
            return f"{artist} - {title} ({album})"
        else:  # mp3
            audio = EasyID3(file_path)
            artist = audio.get('artist', ['Unknown'])[0]
            title = audio.get('title', [file_path.stem])[0]
            album = audio.get('album', ['Unknown Album'])[0]
            return f"{artist} - {title} ({album})"
    except Exception as e:
        return f"Unknown - {file_path.stem} (Unknown Album)"

def update_metadata(file_path, track_info, api):
    """Update the audio file's metadata."""
    try:
        suffix = file_path.suffix.lower()
        
        if suffix == '.wav':
            # WAV files don't support metadata
            logger.info(f"WAV file detected: {file_path}. Only organizing, not updating metadata.")
            return
        elif suffix == '.m4a':
            _update_m4a_metadata(file_path, track_info, api)
        else:  # mp3
            _update_mp3_metadata(file_path, track_info, api)
            
    except Exception as e:
        logger.error(f"Error updating metadata for {file_path}: {str(e)}")

def _update_mp3_metadata(file_path, track_info, api):
    """Update metadata for MP3 files."""
    # First update basic ID3 tags using EasyID3
    try:
        audio = EasyID3(file_path)
    except mutagen.id3.ID3NoHeaderError:
        audio = mutagen.File(file_path, easy=True)
        if audio is None:
            audio = EasyID3()
            audio.save(file_path)
    
    # Basic tags
    audio['title'] = track_info['title']
    audio['artist'] = track_info['artist']
    audio['album'] = track_info['album']
    audio['date'] = track_info['year']
    
    # Set album artist to first name only
    first_artist = track_info['artist'].split('&')[0].split('feat.')[0].split('ft.')[0].strip()
    audio['albumartist'] = first_artist
    
    # Additional tags
    if 'track_number' in track_info:
        audio['tracknumber'] = track_info['track_number']
    if 'genre' in track_info:
        audio['genre'] = track_info['genre']
    if 'bpm' in track_info and track_info['bpm']:
        audio['bpm'] = track_info['bpm']
    if 'key' in track_info and track_info['key']:
        audio['initialkey'] = track_info['key']
    
    # Remove composer and comments if they exist
    if 'composer' in audio:
        del audio['composer']
    if 'comment' in audio:
        del audio['comment']
    
    audio.save()
    
    # Handle album art
    if 'release_id' in track_info:
        cover_art = api.get_cover_art(track_info['release_id'])
        if cover_art:
            audio = ID3(file_path)
            
            # Remove existing art
            for key in list(audio.keys()):
                if key.startswith('APIC:'):
                    del audio[key]
            
            # Add new art
            audio.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=cover_art
                )
            )
            
            # Remove any comments in ID3 tags
            if 'COMM::eng' in audio:
                del audio['COMM::eng']
            for key in list(audio.keys()):
                if key.startswith('COMM:'):
                    del audio[key]
            
            audio.save()

def _update_m4a_metadata(file_path, track_info, api):
    """Update metadata for M4A files."""
    audio = MP4(file_path)
    
    # M4A tag mapping
    audio['\xa9nam'] = track_info['title']
    audio['\xa9ART'] = track_info['artist']
    audio['\xa9alb'] = track_info['album']
    audio['\xa9day'] = track_info['year']
    
    # Set album artist to first name only
    first_artist = track_info['artist'].split('&')[0].split('feat.')[0].split('ft.')[0].strip()
    audio['aART'] = [first_artist]
    
    # Additional tags
    if 'track_number' in track_info:
        audio['trkn'] = [(int(track_info['track_number']), 0)]
    if 'genre' in track_info:
        audio['\xa9gen'] = track_info['genre']
    if 'bpm' in track_info and track_info['bpm']:
        audio['tmpo'] = [int(track_info['bpm'])]
    
    # Remove composer and comments if they exist
    if '\xa9wrt' in audio:
        del audio['\xa9wrt']
    if '\xa9cmt' in audio:
        del audio['\xa9cmt']
    
    # Handle album art
    if 'release_id' in track_info:
        cover_art = api.get_cover_art(track_info['release_id'])
        if cover_art:
            # Convert to MP4Cover
            audio['covr'] = [MP4Cover(cover_art, imageformat=MP4Cover.FORMAT_JPEG)]
    
    audio.save() 