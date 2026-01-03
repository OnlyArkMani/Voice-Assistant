import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
from typing import Dict, Optional, Any
import base64

class VoiceAgent:
    """Handles text-to-speech and speech-to-text operations"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.temp_dir = tempfile.gettempdir()
        
        # Adjust for ambient noise (improves accuracy)
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
    
    def speech_to_text(self, audio_data: bytes = None, audio_file_path: str = None) -> dict[str, any]:
        """
        Convert speech to text
        
        Args:
            audio_data: Raw audio bytes (WAV format)
            audio_file_path: Path to audio file
            
        Returns:
            Dict with 'text' and 'confidence' or 'error'
        """
        try:
            if audio_file_path:
                with sr.AudioFile(audio_file_path) as source:
                    audio = self.recognizer.record(source)
            
            elif audio_data:
                # Convert bytes to AudioData
                # Assuming WAV format
                audio = sr.AudioData(audio_data, 16000, 2)
            
            else:
                return {'error': 'No audio data provided'}
            
            # Use Google Speech Recognition (free, no API key needed)
            text = self.recognizer.recognize_google(audio)
            
            return {
                'text': text,
                'confidence': 'high',
                'success': True
            }
        
        except sr.UnknownValueError:
            return {
                'error': 'Could not understand audio',
                'success': False
            }
        
        except sr.RequestError as e:
            return {
                'error': f'Speech recognition service error: {e}',
                'success': False
            }
        
        except Exception as e:
            return {
                'error': f'Unexpected error: {e}',
                'success': False
            }
    
    def record_from_microphone(self, duration: int = 5) -> dict[str, any]:
        """
        Record audio from microphone
        
        Args:
            duration: Recording duration in seconds
        """
        try:
            with sr.Microphone() as source:
                print("Adjusting for ambient noise... Please wait.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print(f"Recording for {duration} seconds...")
                audio = self.recognizer.listen(source, timeout=duration)
                
                # Convert to text
                text = self.recognizer.recognize_google(audio)
                
                return {
                    'text': text,
                    'success': True
                }
        
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def text_to_speech(self, text: str, lang: str = 'en', slow: bool = False) -> dict[str, any]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            lang: Language code (en, hi, etc.)
            slow: Speak slowly
            
        Returns:
            Dict with 'audio_path' or 'audio_base64' and status
        """
        try:
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=slow)
            
            # Save to temporary file
            filename = f"tts_{os.getpid()}_{hash(text)}.mp3"
            filepath = os.path.join(self.temp_dir, filename)
            tts.save(filepath)
            
            # Read file and encode as base64 for web transfer
            with open(filepath, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                'audio_path': filepath,
                'audio_base64': audio_base64,
                'success': True,
                'format': 'mp3'
            }
        
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def cleanup_temp_files(self):
        """Remove temporary audio files"""
        try:
            for filename in os.listdir(self.temp_dir):
                if filename.startswith('tts_') and filename.endswith('.mp3'):
                    filepath = os.path.join(self.temp_dir, filename)
                    # Only delete files older than 1 hour
                    if os.path.getmtime(filepath) < (os.time() - 3600):
                        os.remove(filepath)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def get_supported_languages(self) -> list[str]:
        """Return list of supported languages"""
        return [
            'en',  # English
            'hi',  # Hindi
            'bn',  # Bengali
            'te',  # Telugu
            'mr',  # Marathi
            'ta',  # Tamil
            'gu',  # Gujarati
        ]