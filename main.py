#!/usr/bin/env python3
"""
Simple Terminal Transcriber
Two main options: Browse & Select Audio File or Record Audio Live
"""

import os
import sys
from transcribe import VoiceTranscriber
import tkinter as tk
from tkinter import filedialog


def main():
    """Main application loop"""
    try:
        # Initialize transcriber
        transcriber = VoiceTranscriber()
        
        while True:
            print("🎤 VOICE TRANSCRIBER")
        
            print("1. Browse & Select Audio File")
            print("2. Record Audio Live")
            print("3. Exit")
            
            
            choice = input("Choose an option (1-3): ").strip()
            
            if choice == '1':
                browse_and_transcribe(transcriber)
            elif choice == '2':
                record_and_transcribe(transcriber)
            elif choice == '3':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def browse_and_transcribe(transcriber):
    """Handle file browsing and transcription"""
    print("\n📁 BROWSE & SELECT AUDIO FILE")
    
    try:
        # Hide the main tkinter window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)  # Bring dialog to front
        root.update()
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg *.mp4 *.webm *.aac"),
                ("WAV Files", "*.wav"),
                ("MP3 Files", "*.mp3"),
                ("All Files", "*.*")
            ],
            initialdir=os.path.expanduser("~")  # Start in user's home directory
        )
        
        # Close tkinter
        root.destroy()
        
        if not file_path:
            print("❌ No file selected.")
            return
        
        print(f"✅ Selected: {os.path.basename(file_path)}")
        
        # Process the file
        success = transcriber.process_file(file_path)
        
        if success:
            print("✅ File processed successfully!")
        else:
            print("❌ Failed to process file.")
            
    except Exception as e:
        print(f"❌ Error with file browser: {str(e)}")
        print("Falling back to manual file path entry...")
        
        # Fallback to manual entry
        file_path = input("Enter the full path to your audio file: ").strip().strip('"\'')
        
        if file_path:
            success = transcriber.process_file(file_path)
            if success:
                print("✅ File processed successfully!")
            else:
                print("❌ Failed to process file.")
        else:
            print("❌ No file path provided.")


def record_and_transcribe(transcriber):
    """Handle live recording and transcription"""
    print("\n🎤 RECORD AUDIO LIVE")
    print("-" * 20)
    print("Press Ctrl+C to stop recording")
    
    # Start recording and transcription
    success = transcriber.record_and_transcribe()
    
    if success:
        print("✅ Recording processed successfully!")
    else:
        print("❌ Failed to process recording.")


if __name__ == "__main__":
    main()