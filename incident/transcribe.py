#!/usr/bin/env python3
"""
Enhanced Transcription Module with Grammar Correction
Handles all audio recording, transcription, and file processing using Groq API
Now includes grammar correction while preserving original meaning
"""

import os
import time
import wave
import pyaudio
import requests
from pathlib import Path
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()


class VoiceTranscriber:
    def __init__(self):
        # Load configuration from environment
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.whisper_model = os.getenv('WHISPER_MODEL')
        self.groq_api_url = os.getenv('GROQ_API_URL')
        
        # Audio settings
        self.chunk = int(os.getenv('CHUNK'))
        self.format = getattr(pyaudio, os.getenv('FORMAT'))
        self.channels = int(os.getenv('CHANNELS'))
        self.rate = int(os.getenv('RATE'))
        
        # Validate API key
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
    def __del__(self):
        """Cleanup PyAudio resources"""
        if hasattr(self, 'audio'):
            self.audio.terminate()

    def process_file(self, file_path):
        """
        Complete file processing workflow: validate, transcribe, and polish
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Expand user path (~)
            file_path = os.path.expanduser(file_path)
            
            # Validate file exists
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False
            
            # Validate audio file
            if not self._validate_audio_file(file_path):
                return False
            
            # Transcribe
            transcription = self._transcribe_file(file_path)
            
            if transcription:
                # Polish the transcription
                polished_transcription = self._polish_transcription(transcription)
                
                # Display results in the requested format
                self._display_results(transcription, polished_transcription)
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error processing file: {str(e)}")
            return False

    def record_and_transcribe(self):
        """
        Complete recording workflow: record, transcribe, and polish
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Record audio
            recorded_file = self._record_audio()
            
            if not recorded_file:
                return False
            
            # Transcribe
            transcription = self._transcribe_file(recorded_file)
            
            if transcription:
                # Polish the transcription
                polished_transcription = self._polish_transcription(transcription)
                
                # Display results in the requested format
                self._display_results(transcription, polished_transcription)
                
                # Clean up recording file
                self._cleanup_file(recorded_file)
                return True
            
            # Clean up even if transcription failed
            self._cleanup_file(recorded_file)
            return False
            
        except Exception as e:
            print(f"❌ Error during recording workflow: {str(e)}")
            return False

    def _display_results(self, original_transcription, polished_transcription):
        """
        Display transcription results in the requested format
        
        Args:
            original_transcription (str): Original transcription text
            polished_transcription (str): Polished transcription text
        """
        print("\nRaw text:")
     
        print(original_transcription)
        print("\nCorrected text:")
        
        print(polished_transcription)
        print()

    def _record_audio(self, duration=None):
        """
        Record audio from microphone
        
        Args:
            duration (int, optional): Recording duration in seconds
            
        Returns:
            str: Path to recorded audio file or None if failed
        """
        try:
            print("🎤 Recording... Press Ctrl+C to stop")
            
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            frames = []
            start_time = time.time()
            
            try:
                while True:
                    data = stream.read(self.chunk)
                    frames.append(data)
                    
                    if duration and (time.time() - start_time) >= duration:
                        break
                        
            except KeyboardInterrupt:
                print("\n🛑 Recording stopped")
            
            stream.stop_stream()
            stream.close()
            
            # Save recording to temporary file
            timestamp = int(time.time())
            filename = f"recording_{timestamp}.wav"
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
            
            return filename
            
        except Exception as e:
            print(f"❌ Error during recording: {str(e)}")
            return None

    def _transcribe_file(self, file_path):
        """
        Transcribe audio file using Groq API
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            str: Transcription text or None if failed
        """
        try:
            with open(file_path, 'rb') as audio_file:
                files = {
                    'file': (os.path.basename(file_path), audio_file, 'audio/wav')
                }
                
                data = {
                    'model': self.whisper_model,
                    'response_format': 'json'
                }
                
                headers = {
                    'Authorization': f'Bearer {self.groq_api_key}'
                }
                
                response = requests.post(
                    self.groq_api_url,
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get('text', '')
                    return transcription
                else:
                    print(f"❌ API Error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error during transcription: {str(e)}")
            return None

    def _polish_transcription(self, transcription):
        """
        Polish transcription using Groq API for grammar correction
        
        Args:
            transcription (str): Original transcription text
            
        Returns:
            str: Polished transcription text
        """
        try:
            # Skip polishing if transcription is too short
            if len(transcription.strip()) < 10:
                return transcription  # Return original unchanged
            
            # Create a grammar correction prompt
            prompt = f"""Please correct the grammar, punctuation, and standardize the following transcribed text while preserving the original meaning and content. Do not change the main ideas or add new information. Only fix grammatical errors, improve sentence structure, and ensure proper formatting:

"{transcription}"

Please provide only the corrected text without any explanations or additional commentary."""
            
            # Use Groq API for grammar correction
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Try different models in order of preference
            models_to_try = [
                'llama3-70b-8192',
                'llama3-8b-8192', 
                'mixtral-8x7b-32768',
                'gemma-7b-it'
            ]
            
            for model in models_to_try:
                try:
                    data = {
                        'model': model,
                        'messages': [
                            {
                                'role': 'user',
                                'content': prompt
                            }
                        ],
                        'max_tokens': min(2000, len(transcription) * 2),
                        'temperature': 0.1
                    }
                    
                    response = requests.post(
                        'https://api.groq.com/openai/v1/chat/completions',
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        polished_text = result['choices'][0]['message']['content'].strip()
                        
                        # Remove any quotation marks that might be added
                        polished_text = polished_text.strip('"\'')
                        
                        return polished_text
                    else:
                        continue
                        
                except Exception as model_error:
                    continue
            
            # If all models failed, return original unchanged
            return transcription
                
        except Exception as e:
            return transcription

    def _basic_text_cleanup(self, text):
        """
        Enhanced basic text cleanup as fallback
        
        Args:
            text (str): Original text
            
        Returns:
            str: Cleaned text
        """
        try:
            if not text or not text.strip():
                return text
            
            # Remove multiple spaces and normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Fix common capitalization issues
            if text:
                # Capitalize first letter
                text = text[0].upper() + text[1:]
                
                # Capitalize after sentence endings
                text = re.sub(r'([.!?])\s+([a-z])', r'\1 \2', text)
                
                # Fix "i" to "I" when it's a standalone word
                text = re.sub(r'\bi\b', 'I', text)
                
                # Fix common contractions
                text = re.sub(r"\bi'm\b", "I'm", text)
                text = re.sub(r"\bi'll\b", "I'll", text)
                text = re.sub(r"\bi'd\b", "I'd", text)
                text = re.sub(r"\bi've\b", "I've", text)
                text = re.sub(r"\bdon't\b", "don't", text)
                text = re.sub(r"\bcan't\b", "can't", text)
                text = re.sub(r"\bwon't\b", "won't", text)
                text = re.sub(r"\bwouldn't\b", "wouldn't", text)
                text = re.sub(r"\bshouldn't\b", "shouldn't", text)
                text = re.sub(r"\bcouldn't\b", "couldn't", text)
                
                # Fix spacing around punctuation
                text = re.sub(r'\s+([.!?,:;])', r'\1', text)
                text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
                
                # Ensure proper ending punctuation
                if text[-1] not in '.!?':
                    text += '.'
            
            print(f"✨ Applied basic text cleanup")
            return text
            
        except Exception as e:
            print(f"❌ Error in basic cleanup: {str(e)}")
            return text

    def _save_transcription(self, original_transcription, polished_transcription, audio_file_path):
        """
        Save both original and polished transcriptions to a text file (DEPRECATED - DISABLED)
        
        Args:
            original_transcription (str): Original transcription text (unchanged)
            polished_transcription (str): Polished transcription text (AI corrected)
            audio_file_path (str): Path to original audio file
            
        Returns:
            str: None (file saving disabled)
        """
        # File saving has been disabled - results are only displayed on screen
        return None

    def _validate_audio_file(self, file_path):
        """
        Validate if audio file is supported
        
        Args:
            file_path (str): Path to audio file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check file extension
            supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.mp4', '.webm', '.aac']
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in supported_formats:
                print(f"⚠️  Warning: File format '{file_ext}' might not be supported")
                print(f"Supported formats: {', '.join(supported_formats)}")
                
                proceed = input("Do you want to proceed anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating file: {str(e)}")
            return False

    def _show_file_info(self, file_path):
        """
        Display file information
        
        Args:
            file_path (str): Path to audio file
        """
        try:
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            file_ext = Path(file_path).suffix.lower()
            
            print(f"\n📊 File Information:")
            print(f"   • Name: {os.path.basename(file_path)}")
            print(f"   • Size: {file_size:.2f} MB")
            print(f"   • Format: {file_ext}")
            
            # Try to get duration for WAV files
            if file_ext == '.wav':
                try:
                    with wave.open(file_path, 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration = frames / float(rate)
                        print(f"   • Duration: {duration:.2f} seconds")
                except:
                    pass
            
        except Exception as e:
            print(f"❌ Error getting file info: {str(e)}")

    def _cleanup_file(self, file_path):
        """
        Clean up temporary files
        
        Args:
            file_path (str): Path to file to delete
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            pass

    # Public methods for backward compatibility
    def validate_audio_file(self, file_path):
        """Public wrapper for file validation"""
        return self._validate_audio_file(file_path)

    def transcribe_file(self, file_path):
        """Public wrapper for transcription"""
        return self._transcribe_file(file_path)

    def polish_transcription(self, transcription):
        """Public wrapper for transcription polishing"""
        return self._polish_transcription(transcription)

    def record_audio(self, duration=None):
        """Public wrapper for recording"""
        return self._record_audio(duration)

    def save_transcription(self, original_transcription, polished_transcription, audio_file_path):
        """Public wrapper for saving transcription (deprecated - file saving removed)"""
        print("⚠️  File saving has been disabled. Results are only displayed on screen.")
        return None

    def get_supported_formats(self):
        """
        Get list of supported audio formats
        
        Returns:
            list: List of supported file extensions
        """
        return ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.mp4', '.webm', '.aac']