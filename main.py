#!/usr/bin/env python3
"""
Enhanced Terminal Transcriber with AI-Powered Incident Analysis
Three main options: Browse & Select Audio File, Record Audio Live, or Exit
Now includes AI analysis and incident report generation
"""

import os
import sys
from transcribe import VoiceTranscriber
from incident import IncidentManager
import tkinter as tk
from tkinter import filedialog


def main():
    """Main application loop"""
    try:
        # Initialize transcriber and incident manager
        transcriber = VoiceTranscriber()
        incident_manager = IncidentManager()
        
        while True:
            print("\n🎤 AI-POWERED INCIDENT TRANSCRIBER")
 
            print("1. Browse & Select Audio File")
            print("2. Record Audio Live")
            print("3. Exit")
      
            
            choice = input("Choose an option (1-3): ").strip()
            
            if choice == '1':
                browse_and_transcribe(transcriber, incident_manager)
            elif choice == '2':
                record_and_transcribe(transcriber, incident_manager)
            elif choice == '3':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def browse_and_transcribe(transcriber, incident_manager):
    """Handle file browsing, transcription, and incident analysis"""
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
        
        # Process the file and get transcription results
        original_transcription, polished_transcription = transcriber.process_file_with_results(file_path)
        
        if original_transcription:
            # Process through incident analysis
            success = incident_manager.process_incident(original_transcription, polished_transcription)
            
            if success:
                # Display the incident report
                incident_manager.display_incident_report()
            else:
                print("❌ Failed to analyze incident from transcription.")
        else:
            print("❌ Failed to transcribe file.")
            
    except Exception as e:
        print(f"❌ Error with file browser: {str(e)}")
        print("Falling back to manual file path entry...")
        
        # Fallback to manual entry
        file_path = input("Enter the full path to your audio file: ").strip().strip('"\'')
        
        if file_path:
            original_transcription, polished_transcription = transcriber.process_file_with_results(file_path)
            if original_transcription:
                # Process through incident analysis
                success = incident_manager.process_incident(original_transcription, polished_transcription)
                
                if success:
                    # Display the incident report
                    incident_manager.display_incident_report()
                else:
                    print("❌ Failed to analyze incident from transcription.")
            else:
                print("❌ Failed to transcribe file.")
        else:
            print("❌ No file path provided.")


def record_and_transcribe(transcriber, incident_manager):
    """Handle live recording, transcription, and incident analysis"""
    print("\n🎤 RECORD AUDIO LIVE")
    print("-" * 20)
    print("Press Ctrl+C to stop recording")
    
    # Start recording and transcription
    original_transcription, polished_transcription = transcriber.record_and_transcribe_with_results()
    
    if original_transcription:
        print("✅ Recording transcribed successfully!")
        
        # Process through incident analysis
        success = incident_manager.process_incident(original_transcription, polished_transcription)
        
        if success:
            # Display the incident report
            incident_manager.display_incident_report()
        else:
            print("❌ Failed to analyze incident from transcription.")
    else:
        print("❌ Failed to transcribe recording.")


if __name__ == "__main__":
    main()