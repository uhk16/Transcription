#!/usr/bin/env python3
"""
Enhanced AI Analysis Module
Improved incident analysis with better prompting and parsing
"""

import os
import requests
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIAnalyzer:
    def __init__(self):
        # Load configuration from environment
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # Validate API key
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
    
    def analyze_incident(self, transcribed_text):
        """
        Analyze transcribed text and extract incident information
        
        Args:
            transcribed_text (str): The transcribed text from audio
            
        Returns:
            dict: Structured incident information or None if failed
        """
        try:
            # Get structured analysis
            structured_data = self._get_structured_analysis(transcribed_text)
            
            if structured_data:
                return structured_data
            else:
                print("❌ Structured analysis failed")
                return None
                
        except Exception as e:
            print(f"❌ Error during AI analysis: {str(e)}")
            return None
    
    def _get_structured_analysis(self, transcribed_text):
        """
        Get structured analysis using improved prompting
        """
        try:
            # Enhanced prompt with better instructions
            prompt = f"""
You are an expert incident analyst. Analyze the following transcript and extract incident information. 

IMPORTANT: Generate a descriptive title based on the content, don't just say "Incident Report".

Please provide your analysis in this EXACT format (copy the structure exactly):

===ANALYSIS START===
INCIDENT_TITLE: [Generate a specific, descriptive title based on what happened]
WHO: [People involved, their roles, departments mentioned]
WHAT: [Detailed description of what happened, sequence of events]
WHERE: [Location, department, facility, or area where incident occurred]
IMMEDIATE_ACTION: [What was done immediately after the incident]
QUALITY_CONCERNS: [Quality issues, potential impacts on products/services]
QUALITY_CONTROLS: [Quality control measures that failed or were bypassed]
RCA_TOOL: [Recommend appropriate root cause analysis method]
EXPECTED_INTERIM_ACTION: [Actions needed to prevent immediate recurrence]
CAPA: [Corrective and Preventive Actions needed]
===ANALYSIS END===

TRANSCRIPT TO ANALYZE:
"{transcribed_text}"

INSTRUCTIONS:
- Be specific and detailed in your analysis
- If information is not available, write "Not specified in transcript"
- Generate a meaningful title that describes the actual incident
- Focus on extracting facts from the transcript
- Provide actionable recommendations for RCA_TOOL, EXPECTED_INTERIM_ACTION, and CAPA
"""
            
            # Use Groq API for analysis
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Try different models in order of preference
            models_to_try = [
                'llama3-70b-8192',
                'llama3-8b-8192', 
                'mixtral-8x7b-32768',
                'gemma2-9b-it'
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
                        'max_tokens': 3000,
                        'temperature': 0.2  # Lower temperature for more consistent output
                    }
                    
                    response = requests.post(
                        'https://api.groq.com/openai/v1/chat/completions',
                        headers=headers,
                        json=data,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        analysis_text = result['choices'][0]['message']['content'].strip()
                        
                        # Parse the structured response
                        incident_data = self._parse_enhanced_response(analysis_text)
                        
                        if incident_data and self._validate_analysis(incident_data):
                            print(f"✅ Analysis successful with model: {model}")
                            return incident_data
                        else:
                            print(f"⚠️ Analysis parsing failed with model: {model}")
                            continue
                    else:
                        print(f"❌ API Error with model {model}: {response.status_code}")
                        if response.status_code == 429:
                            print("⏳ Rate limit hit, trying next model...")
                        continue
                        
                except Exception as model_error:
                    print(f"❌ Error with model {model}: {str(model_error)}")
                    continue
            
            return None
                
        except Exception as e:
            print(f"❌ Error in structured analysis: {str(e)}")
            return None
    
    def _parse_enhanced_response(self, analysis_text):
        """
        Parse the enhanced AI response with better error handling
        """
        try:
            incident_data = {
                'title': '',
                'who': '',
                'what': '',
                'where': '',
                'immediate_action': '',
                'quality_concerns': '',
                'quality_controls': '',
                'rca_tool': '',
                'expected_interim_action': '',
                'capa': ''
            }
            
            # Extract content between markers if present
            start_marker = "===ANALYSIS START==="
            end_marker = "===ANALYSIS END==="
            
            if start_marker in analysis_text and end_marker in analysis_text:
                content = analysis_text.split(start_marker)[1].split(end_marker)[0]
            else:
                content = analysis_text
            
            # Parse using regex for more robust extraction
            patterns = {
                'title': r'INCIDENT_TITLE:\s*(.+?)(?=\n\w+:|$)',
                'who': r'WHO:\s*(.+?)(?=\n\w+:|$)',
                'what': r'WHAT:\s*(.+?)(?=\n\w+:|$)',
                'where': r'WHERE:\s*(.+?)(?=\n\w+:|$)',
                'immediate_action': r'IMMEDIATE_ACTION:\s*(.+?)(?=\n\w+:|$)',
                'quality_concerns': r'QUALITY_CONCERNS:\s*(.+?)(?=\n\w+:|$)',
                'quality_controls': r'QUALITY_CONTROLS:\s*(.+?)(?=\n\w+:|$)',
                'rca_tool': r'RCA_TOOL:\s*(.+?)(?=\n\w+:|$)',
                'expected_interim_action': r'EXPECTED_INTERIM_ACTION:\s*(.+?)(?=\n\w+:|$)',
                'capa': r'CAPA:\s*(.+?)(?=\n\w+:|$)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = re.sub(r'\n\s*', ' ', value)  # Replace newlines with spaces
                    value = re.sub(r'\s+', ' ', value)    # Normalize whitespace
                    incident_data[key] = value
            
            return incident_data
            
        except Exception as e:
            print(f"❌ Error parsing enhanced response: {str(e)}")
            return None
    
    def _validate_analysis(self, incident_data):
        """
        Validate that the analysis contains meaningful information
        """
        if not incident_data:
            return False
        
        # Check if at least title and what are filled with meaningful content
        title = incident_data.get('title', '').strip()
        what = incident_data.get('what', '').strip()
        
        if not title or title == 'N/A' or len(title) < 5:
            return False
        
        if not what or what == 'N/A' or len(what) < 10:
            return False
        
        return True
    
    def get_summary_analysis(self, transcribed_text):
        """
        Get a quick summary analysis of the incident
        """
        try:
            prompt = f"""
Provide a brief 2-3 sentence summary of this incident:

"{transcribed_text}"

Focus on: what happened, who was involved, and the key concern.
"""
            
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'llama3-8b-8192',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 300,
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting summary: {str(e)}")
            return None