from urllib import request
from winreg import QueryInfoKey
import speech_recognition as sr
import pyttsx3 as pt
import datetime as dt
import logging
import json
import re
import threading
import time
from typing import Optional, Dict, List
import requests

class VoiceAssistant:
    def __init__(self, name: str = "Aurora"):
        
        #initialize voice assistant
        self.name = name
        self.is_listening = True
        self.conversation_history = []

        #setup logging for easy debugging
        self._setup_logging()

        #initialize speech recognition
        self.recognizer = sr.Recognizer()
        self._configure_speech_recognition()
        
        #initialize text to speech engine
        self.engine = self._initialize_tts_engine()

        #command patterns
        self.command_patterns = self._setup_command_patterns()
        self.logger.info(f"{self.name} voice assistant initialized successfully")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('aurora_assistant.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.name)
    
    def _configure_speech_recognition(self):
        # FIXED: Better speech recognition settings
        self.recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Shorter pause detection
        self.recognizer.phrase_threshold = 0.3

        self.logger.info("Speech recognition configured with optimized settings")
    
    def _initialize_tts_engine(self):
        try:
            engine = pt.init()

            # Test if engine was created successfully
            if engine is None:
                self.logger.error("TTS engine returned None - trying alternative initialization")
                engine = pt.init('sapi5')  # Try Windows SAPI5 specifically
            
            if engine is None:
                self.logger.error("All TTS initialization attempts failed")
                return None

            #available voices
            voices = engine.getProperty('voices')
            self.logger.info(f"Found {len(voices) if voices else 0} available voices")
            
            if voices:
                # Log available voices for debugging
                for i, voice in enumerate(voices):
                    self.logger.info(f"Voice {i}: {voice.name} - {voice.id}")
                
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)
                else:
                    engine.setProperty('voice', voices[0].id)
            else:
                self.logger.warning("No voices found - TTS may not work properly")
            
            #configurable speech rate (WPM)
            engine.setProperty('rate', 150)  # Slightly faster for better responsiveness

            #configurable volume (0.0 to 1.0)
            engine.setProperty('volume', 0.9)

            # Test the engine by attempting to speak
            try:
                engine.runAndWait()
                self.logger.info("TTS engine initialized and tested successfully")
            except Exception as test_error:
                self.logger.warning(f"TTS test failed but engine initialized: {test_error}")
            
            return engine
        
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            print(f"TTS Error Details: {e}")
            return None
        
    def _setup_command_patterns(self) -> Dict[str, List[str]]:
        return {
            'time': [
                r'\b(what\s+time|current\s+time|tell\s+time|time\s+is|what\'s\s+the\s+time)\b',
                r'\b(clock)\b'
            ],
            'date': [
                r'\b(what\s+date|current\s+date|tell\s+date|today\'s\s+date|what\s+day)\b',
                r'\b(calendar)\b'
            ],
            'greeting': [
                r'\b(hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening)\b'
            ],
            'exit': [
                r'\b(stop|exit|quit|goodbye|bye|shut\s+down|turn\s+off)\b',
                r'\b(aurora\s+stop|aurora\s+exit|aurora\s+quit)\b'
            ],
            'help': [
                r'\b(help|what\s+can\s+you\s+do|commands|assistance)\b'
            ],
            'weather': [
                r'\b(weather|current weather|forecast)\b',
                r'\b(temperature in|weather in)\b'
            ]
        }
    
    def speak(self, text: str, log_message: bool = True):
        if not text:
            return
    
        if log_message:
            self.logger.info(f"Speaking: {text}")
    
        # Always print to console for debugging
        print(f"🔊 [AURORA SAYS]: {text}")
    
        try:
            if self.engine:
                # Stop any previous speech
                self.engine.stop()
                
                # Clear any pending speech
                try:
                    self.engine.endLoop()
                except:
                    pass
            
                # Say the text
                self.engine.say(text)
                
                # Try to run and wait with timeout
                try:
                    self.engine.runAndWait()
                except Exception as run_error:
                    self.logger.error(f"runAndWait failed: {run_error}")
                    # Try alternative method
                    self.engine.startLoop()
                    time.sleep(0.1)
                    self.engine.iterate()
                    self.engine.endLoop()
            
                # Small delay
                time.sleep(0.2)
            else:
                # Fallback to text if TTS failure occurred
                self.logger.warning("TTS engine is None - using text fallback")
                print(f"[TTS FAILED - TEXT ONLY]: {text}")

        except Exception as e:
            self.logger.error(f"TTS Error: {e}")
            print(f"[TTS ERROR - TEXT FALLBACK]: {text}")
            
            # Try to reinitialize TTS engine
            try:
                self.logger.info("Attempting to reinitialize TTS engine...")
                self.engine = self._initialize_tts_engine()
            except:
                pass

    def listen(self) -> Optional[str]:
        if not self.is_listening:
            return None
        
        try:
            with sr.Microphone() as source:
                #taking audio input from user's mic
                print("🎤Listening...")
                self.logger.debug("Starting to listen for audio input 🎤")

                #adjusting for ambient noise to increase user voice accuracy
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # FIXED: Better threshold management
                if self.recognizer.energy_threshold > 800:
                    self.recognizer.energy_threshold = 800
                    print("⚡ Energy threshold was too high, capped at 800")

                #listening to audio
                audio = self.recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=15
                )

                print("🔄 Processing Speech...")

                #connect to google's speech recognition software
                command = self.recognizer.recognize_google(audio, language='en-US')

                command= command.strip().lower()

                self.logger.info(f"User said: '{command}'")
                print(f"You said: {command}")

                #add to conversation history
                self.conversation_history.append({
                    'timestamp': dt.datetime.now().isoformat(),
                    'user_input': command,
                    'type': 'user_speech'
                })

                return command
                
        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timeout - no speech detected.")
            return "timeout"
            
        except sr.UnknownValueError:
            self.logger.warning("Speech recognition failed - could not understand audio")
            return "unclear"
            
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return "service_error"
            
        except Exception as e:
            self.logger.error(f"Unexpected error in listen(): {e}")
            return "error"
        
    def recognize_command(self, query: str) -> Optional[str]:
        if not query:
            return None
        query = query.lower().strip()

        #checking every command pattern
        for command, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    self.logger.debug(f"Matched command '{command}' with pattern: {pattern}")
                    return command
        
        #if no matching pattern found, the command is unknown
        self.logger.debug(f"No command pattern matched for: {query}")
        return 'unknown'
    
    def execute_command(self, command: str, original_query: str):
        try:
            if command == 'time':
                self.tell_time()
            elif command == 'date':
                self.tell_date()
            elif command == 'greeting':
                self.handle_greeting()
            elif command == 'exit':
                self.handle_exit()
            elif command == 'help':
                self.show_help()
            elif command == 'unknown':
                self.handle_unknown_command(original_query)
            elif command == 'weather':
                self.handle_weather(original_query)
            elif command in ['timeout', 'unclear', 'service_error', 'error']:
                self.handle_recognition_error(command)
            else:
                self.logger.warning(f"Unhandled command: {command}")

        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            self.speak("I encountered an error while processing your request. Please try again.")

    def handle_recognition_error(self, error_type: str):
        """Handle different types of speech recognition errors"""
        if error_type == 'timeout':
            self.speak("I didn't hear anything. Please try speaking again.", False)
        elif error_type == 'unclear':
            self.speak("I'm sorry, I couldn't understand what you said. Could you please repeat that?", False)
        elif error_type == 'service_error':
            self.speak("I'm having trouble with the speech service. Please check your internet connection.", False)
        elif error_type == 'error':
            self.speak("I encountered an unexpected error while listening. Let me try again.", False)

    def tell_time(self):
        try:
            now = dt.datetime.now()
            
            if now.hour == 0:
                time_str = f"midnight and {now.minute} minutes"
            elif now.hour == 12:
                time_str = f"noon and {now.minute} minutes" if now.minute > 0 else "noon"
            elif now.hour < 12:
                hour_12 = now.hour if now.hour > 0 else 12
                time_str = f"{hour_12}:{now.minute:02d} AM"
            else:
                hour_12 = now.hour - 12
                time_str = f"{hour_12}:{now.minute:02d} PM"
            
            response = f"The current time is {time_str}"
            self.speak(response)

            #log command execution
            self.conversation_history.append({
                'timestamp': now.isoformat(),
                'command': 'time',
                'response': response,
                'type': 'assistant_response'
            })
        except Exception as e:
            self.logger.error(f"Error telling time: {e}")
            self.speak("I'm sorry, I couldn't get the current time right now.")
    
    def tell_date(self):
        try:
            today = dt.date.today()
            now = dt.datetime.now()
            
            #date formatting
            formatted_date = today.strftime("%A, %B %d, %Y")
            
            #contextual info
            if today.weekday() >= 5:
                context = "It's the weekend!"
            else:
                context = "It's a weekday."
            
            response = f"Today is {formatted_date}. {context}"
            self.speak(response)
            
            #log command execution
            self.conversation_history.append({
                'timestamp': now.isoformat(),
                'command': 'date',
                'response': response,
                'type': 'assistant_response'
            })
            
        except Exception as e:
            self.logger.error(f"Error telling date: {e}")
            self.speak("I'm sorry, I couldn't get today's date right now.")

    def get_weather(self, city: str, country: str = None):
        try:
            api_key = "<INSERT API KEY HERE>"
            base_url = "https://api.openweathermap.org/data/2.5/weather"

            if country:
                location = (f"{city}, {country}")
            else:
                location = city

            params = {
                "q" : location,
                "appid" : api_key,
                "units" : "metric"
            }

            response = requests.get(base_url, params=params)
            data = response.json()

            #check if city is found
            if data.get("cod") != 200:
                self.speak(f"I couldn't find any information on {city}. Please check the city name and try again.")
                return
            
            #extracting weather info
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            #create a weather report
            weather_report = (f"The weather in {city} is {weather_desc} with a temperature of {temp}, humidity is at {humidity}%. The calculated wind speed is {wind_speed} metres per second.")
            #make aurora speak the weather report
            self.speak(weather_report)

        except Exception as e:
            self.logger.error(f"Error occurred while fetching the weather report: {e}")
            self.speak("Sorry, I was unable to retrieve the weather information right now.")

    def handle_weather(self, query: str):
        try:
            #trying to match 'weather for {city}' or 'weather in {city}' or 'temperature in {city}'
            match = re.search(r'(?:weather|temperature)(?: in| for)? ([a-zA-Z\s]+)', query, re.IGNORECASE)

            if match:
                city = match.group(1).strip()
                self.get_weather(city)
            else:
                #if no city detected, ask the user for it
                self.speak("Which city's weather would you like to know?")
                city_response = self.listen()
                if city_response and city_response not in ["timeout", "unclear", "service_error", "error"]:
                    self.get_weather(city_response)
                else:
                    self.speak("I couldn't get the city name. Please try again.")
        
        except Exception as e:
            self.logger.error(f"Error in handle_weather: {e}")
            self.speak("Sorry, I couldn't process the weather request.")

    def handle_greeting(self):
        """FIXED: Properly handle greeting commands"""
        hour = dt.datetime.now().hour
        
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        responses = [
            f"{greeting}! I'm {self.name}, your voice assistant. How can I help you today?",
            f"{greeting}! Great to hear from you. What can I do for you?",
            f"Hello there! {greeting}. How may I assist you?"
        ]
        
        # Use different greetings to keep it fresh
        import random
        response = random.choice(responses)
        self.speak(response)
        
        # Log the greeting interaction
        self.conversation_history.append({
            'timestamp': dt.datetime.now().isoformat(),
            'command': 'greeting',
            'response': response,
            'type': 'assistant_response'
        })

    def show_help(self):
        help_text = f"""Here's what I can help you with:

        ⏰ Time: Ask "What time is it?" or "Tell me the time"
        📅 Date: Ask "What's today's date?" or "Tell me the date"
        👋 Greetings: Say hello and I'll greet you back
        ❓ Help: Ask for help to hear this message again
        🔚 Exit: Say "stop", "exit", or "goodbye" to end our conversation

        Just speak naturally - I understand different ways of asking for things!
        """
        
        self.speak("Here are the things I can help you with: I can tell you the time, today's date, respond to greetings, provide help, and exit when you're done. Just speak naturally!")
        print(help_text)

    def handle_unknown_command(self, query: str):
        responses = [
            "I'm not sure how to help with that. Could you try asking about the time, date, or say 'help' for more options?",
            "I didn't recognize that command. I can tell you the time, date, or you can ask for help to see what I can do.",
            "I'm still learning! Right now I can help with time, date, and basic conversation. Try saying 'help' for more details."
        ]
        
        import random
        response = random.choice(responses)
        self.speak(response)
        
        #log unknown commands for future expansion and development
        self.logger.info(f"Unknown command received: '{query}'")

    def handle_exit(self):
        """FIXED: Proper exit handling"""
        responses = [
            f"Goodbye! It was nice talking to you.",
            f"Have a great day! See you next time.",
            f"Bye for now! Take care!"
        ]
        
        import random
        response = random.choice(responses)
        self.speak(response)
        
        # Stop the assistant
        self.is_listening = False
        
        # Save conversation history before exit
        self.save_conversation_history()
        
        #log exit command
        self.logger.info("Exit command executed - shutting down")

    def save_conversation_history(self):
        try:
            filename = f"conversation_history_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
            self.logger.info(f"Conversation history saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save conversation history: {e}")
        
    def run(self):
        print(f"\n🤖 {self.name} Voice Assistant 2.0 Starting Up...")
        print("=" * 50)
        
        #welcome message
        welcome_msg = f"Hello! I'm {self.name}, your enhanced voice assistant. Say 'help' if you need guidance, or 'stop' to exit."
        self.speak(welcome_msg)
        
        print("\n💡 Tip: Speak clearly and naturally. I understand many different ways of asking for things!")
        print("🎯 Try: 'What time is it?', 'Tell me today's date', 'Hello Aurora', or 'Help me'\n")
        
        #main interaction loop
        while self.is_listening:
            try:
                #listen for user input
                query = self.listen()
                
                #skip empty queries and error states that don't need processing
                if not query or query in ['timeout', 'unclear', 'service_error', 'error']:
                    if query in ['timeout', 'unclear', 'service_error', 'error']:
                        self.handle_recognition_error(query)
                    continue
                
                #recognize command from the query
                command = self.recognize_command(query)
                
                #execute the appropriate command
                self.execute_command(command, query)
                
                #small delay to prevent overwhelming the user
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Keyboard interrupt detected.")
                self.speak("Stopping the assistant.")
                break
                
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                self.speak("I encountered an unexpected error. Let me try to continue.")
                continue
        
        print("\n✅ Aurora has shut down successfully.")

def main():
    try:
        #create and run the VVA
        assistant = VoiceAssistant("Aurora")
        assistant.run()
        
    except Exception as e:
        print(f"❌ Failed to start the voice assistant: {e}")
        logging.error(f"Application startup failed: {e}")


if __name__ == "__main__":
    main()

