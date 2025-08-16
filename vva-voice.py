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
import subprocess
import webbrowser
import psutil
from typing import Optional, Dict, List
import requests
from dotenv import load_dotenv
import os
import spacy
import math

# For notifications
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    try:
        from win10toast import ToastNotifier
        NOTIFICATIONS_AVAILABLE = True
        toaster = ToastNotifier()
    except ImportError:
        NOTIFICATIONS_AVAILABLE = False

load_dotenv()

# Access API keys
API_KEY = os.getenv("OPENWEATHER_API_KEY")


class TimerManager:
    """Manages timers and alarms"""

    def __init__(self, assistant):
        self.assistant = assistant
        self.timers = {}
        self.timer_counter = 0

    def set_timer(self, duration_seconds: int, name: str = None) -> int:
        """Set a timer for specified duration"""
        self.timer_counter += 1
        timer_id = self.timer_counter

        if not name:
            name = f"Timer {timer_id}"

        timer_thread = threading.Thread(
            target=self._timer_thread,
            args=(timer_id, duration_seconds, name),
            daemon=True
        )

        self.timers[timer_id] = {
            'name': name,
            'duration': duration_seconds,
            'start_time': time.time(),
            'thread': timer_thread
        }

        timer_thread.start()
        return timer_id

    def _timer_thread(self, timer_id: int, duration: int, name: str):
        """Timer thread that runs in background"""
        time.sleep(duration)

        if timer_id in self.timers:
            self.assistant.logger.info(f"Timer '{name}' completed")
            message = f"Timer '{name}' is complete!"

            # Show notification if available
            if NOTIFICATIONS_AVAILABLE:
                try:
                    if 'notification' in globals():
                        notification.notify(
                            title="Timer Complete!",
                            message=message,
                            timeout=10
                        )
                    elif 'toaster' in globals():
                        toaster.show_toast(
                            "Timer Complete!", message, duration=10)
                except Exception as e:
                    self.assistant.logger.error(f"Notification error: {e}")

            # Speak the notification
            self.assistant.speak(message)

            # Clean up
            del self.timers[timer_id]

    def set_alarm(self, target_time: dt.time, name: str = None) -> int:
        """Set an alarm for specific time"""
        now = dt.datetime.now()
        target_datetime = dt.datetime.combine(now.date(), target_time)

        # If target time is in the past, set for tomorrow
        if target_datetime <= now:
            target_datetime += dt.timedelta(days=1)

        duration_seconds = (target_datetime - now).total_seconds()

        if not name:
            name = f"Alarm for {target_time.strftime('%I:%M %p')}"

        return self.set_timer(int(duration_seconds), name)


class StopwatchManager:
    """Manages stopwatch functionality"""

    def __init__(self, assistant):
        self.assistant = assistant
        self.start_time = None
        self.running = False
        self.elapsed_time = 0

    def start(self):
        """Start the stopwatch"""
        if not self.running:
            self.start_time = time.time() - self.elapsed_time
            self.running = True
            return True
        return False

    def stop(self):
        """Stop the stopwatch"""
        if self.running:
            self.elapsed_time = time.time() - self.start_time
            self.running = False
            return self.elapsed_time
        return self.elapsed_time

    def reset(self):
        """Reset the stopwatch"""
        self.start_time = None
        self.running = False
        self.elapsed_time = 0

    def get_time(self):
        """Get current elapsed time"""
        if self.running:
            return time.time() - self.start_time
        return self.elapsed_time

    def format_time(self, seconds):
        """Format time in minutes:seconds.milliseconds"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:06.3f}"


class VoiceAssistant:
    def __init__(self, name: str = "Aurora"):

        # Initialize voice assistant
        self.name = name
        self.is_listening = True
        self.conversation_history = []

        # Setup logging for easy debugging
        self._setup_logging()

        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self._configure_speech_recognition()

        # Initialize text to speech engine
        self.engine = self._initialize_tts_engine()

        # Initialize managers for new features
        self.timer_manager = TimerManager(self)
        self.stopwatch_manager = StopwatchManager(self)

        # Command patterns (enhanced for new features)
        self.command_patterns = self._setup_command_patterns()

        # Initialize spaCy NLU
        self._initialize_spacy()

        # Common words that are not cities
        self.non_city_words = {
            'like', 'today', 'tomorrow', 'now', 'currently', 'outside', 'there',
            'going', 'to', 'be', 'will', 'is', 'it', 'the', 'weather', 'temperature',
            'forecast', 'report', 'update', 'please', 'tell', 'me', 'what', 'how',
            'when', 'where', 'nice', 'good', 'bad', 'hot', 'cold', 'warm', 'cool'
        }

        # App launcher mappings
        self.app_mappings = {
            'chrome': ['chrome.exe', 'google-chrome'],
            'firefox': ['firefox.exe'],
            'edge': ['msedge.exe'],
            'notepad': ['notepad.exe'],
            'calculator': ['calc.exe'],
            'paint': ['mspaint.exe'],
            'word': ['winword.exe'],
            'excel': ['excel.exe'],
            'powerpoint': ['powerpnt.exe'],
            'file explorer': ['explorer.exe'],
            'task manager': ['taskmgr.exe'],
            'command prompt': ['cmd.exe'],
            'powershell': ['powershell.exe']
        }

        self.logger.info(
            f"{self.name} voice assistant initialized successfully with enhanced features")

    def _initialize_spacy(self):
        """Initialize spaCy NLU for better language understanding"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.logger.info("spaCy NLU initialized successfully")

            # Enhanced intent keywords with new features
            self.intent_keywords = {
                'time': ['time', 'clock', 'hour', 'minute', 'current time', 'what time'],
                'date': ['date', 'day', 'today', 'calendar', 'what day', 'current date'],
                'weather': ['weather', 'temperature', 'rain', 'sunny', 'cloudy', 'forecast',
                            'climate', 'hot', 'cold', 'umbrella', 'storm', 'snow'],
                'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon',
                             'good evening', 'greetings', 'howdy'],
                'help': ['help', 'assist', 'what can you do', 'commands', 'support'],
                'exit': ['stop', 'exit', 'quit', 'goodbye', 'bye', 'shutdown', 'turn off'],
                'timer': ['timer', 'set timer', 'countdown', 'remind me', 'wake me up'],
                'alarm': ['alarm', 'set alarm', 'wake me', 'morning alarm'],
                'stopwatch': ['stopwatch', 'start stopwatch', 'stop stopwatch', 'reset stopwatch'],
                'app': ['open', 'launch', 'start', 'run', 'execute'],
                'search': ['search', 'look up', 'find', 'google'],
                'calculate': ['calculate', 'math', 'plus', 'minus', 'times', 'divided', 'equals'],
                'system': ['battery', 'storage', 'memory', 'cpu', 'system info', 'disk space']
            }

        except Exception as e:
            self.logger.error(f"Failed to initialize spaCy: {e}")
            self.nlp = None

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
        # Lower threshold for better sensitivity
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Shorter pause detection
        self.recognizer.phrase_threshold = 0.3

        self.logger.info(
            "Speech recognition configured with optimized settings")

    def _initialize_tts_engine(self):
        try:
            engine = pt.init()

            # Test if engine was created successfully
            if engine is None:
                self.logger.error(
                    "TTS engine returned None - trying alternative initialization")
                engine = pt.init('sapi5')  # Try Windows SAPI5 specifically

            if engine is None:
                self.logger.error("All TTS initialization attempts failed")
                return None

            # Available voices
            voices = engine.getProperty('voices')
            self.logger.info(
                f"Found {len(voices) if voices else 0} available voices")

            if voices:
                # Log available voices for debugging
                for i, voice in enumerate(voices):
                    self.logger.info(f"Voice {i}: {voice.name} - {voice.id}")

                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)
                else:
                    engine.setProperty('voice', voices[0].id)
            else:
                self.logger.warning(
                    "No voices found - TTS may not work properly")

            # Configurable speech rate (WPM)
            # Slightly faster for better responsiveness
            engine.setProperty('rate', 150)

            # Configurable volume (0.0 to 1.0)
            engine.setProperty('volume', 0.9)

            # Test the engine by attempting to speak
            try:
                engine.runAndWait()
                self.logger.info(
                    "TTS engine initialized and tested successfully")
            except Exception as test_error:
                self.logger.warning(
                    f"TTS test failed but engine initialized: {test_error}")

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
                r'\b(exit|quit|goodbye|bye|shut\s+down|turn\s+off)\b',
                r'\b(aurora\s+stop|aurora\s+exit|aurora\s+quit)\b',
                r'^stop$'
            ],
            'help': [
                r'\b(help|what\s+can\s+you\s+do|commands|assistance)\b'
            ],
            'weather': [
                r'\b(weather|current weather|forecast)\b',
                r'\b(temperature in|weather in)\b'
            ],
            'timer': [
                r'\b(set\s+timer|timer\s+for|countdown)\b'
            ],
            'alarm': [
                r'\b(set\s+alarm|alarm\s+for|wake\s+me)\b'
            ],
            'stopwatch': [
                r'\b(start\s+stopwatch|stop\s+stopwatch|reset\s+stopwatch|stopwatch)\b',
                r'\b(start|stop|reset)\s+(the\s+)?stopwatch\b'
            ],
            'app': [
                r'\b(open|launch|start|run)\s+\w+\b'
            ],
            'search': [
                r'\b(search\s+for|look\s+up|google|find)\b'
            ],
            'calculate': [
                r'\b(calculate|what\'s|whats|what\s+is)\s+.*[\+\-\*\/x×÷]\b',
                r'\b\d+\s*(plus|minus|times|divided\s+by|x|\*|\/|\+|\-)\s*\d+\b',
                r'\bwhat\s+is\s+\d+.*\d+\b'
            ],
            'system': [
                r'\b(battery\s+level|storage|disk\s+space|memory|system\s+info)\b'
            ]
        }

    def enhanced_command_recognition(self, query: str) -> tuple[Optional[str], Dict]:
        """Enhanced command recognition using spaCy NLU"""
        if not query:
            return None, {}

        # First try regex patterns (existing system)
        regex_result = self.recognize_command(query)
        if regex_result != 'unknown':
            self.logger.info(f"Regex matched: {regex_result}")
            return regex_result, {}

        # If regex fails, try spaCy NLU
        if self.nlp:
            return self._spacy_intent_recognition(query)

        return 'unknown', {}

    def _spacy_intent_recognition(self, query: str) -> tuple[str, Dict]:
        """Use spaCy for intelligent intent recognition and entity extraction"""
        try:
            doc = self.nlp(query.lower())

            # Extract entities
            entities = {
                'cities': [],
                'dates': [],
                'times': [],
                'locations': [],
                'numbers': [],
                'apps': []
            }

            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:  # Geopolitical entities, locations
                    entities['cities'].append(ent.text)
                elif ent.label_ in ['DATE', 'TIME']:
                    entities['dates'].append(ent.text)
                elif ent.label_ == 'TIME':
                    entities['times'].append(ent.text)
                elif ent.label_ in ['CARDINAL', 'QUANTITY']:
                    entities['numbers'].append(ent.text)

            # Extract numbers and time units for timers
            numbers = re.findall(r'\d+', query)
            if numbers:
                entities['numbers'].extend(numbers)

            # Extract app names
            for app in self.app_mappings.keys():
                if app in query.lower():
                    entities['apps'].append(app)

            # Intent classification using keyword matching with confidence
            intent_scores = {}

            for intent, keywords in self.intent_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword in query.lower():
                        score += 1
                    # Check for semantic similarity with spaCy
                    for token in doc:
                        if token.similarity(self.nlp(keyword)[0]) > 0.7:
                            score += 0.5

                if score > 0:
                    intent_scores[intent] = score

            # Get the highest scoring intent
            if intent_scores:
                best_intent = max(intent_scores, key=intent_scores.get)
                confidence = intent_scores[best_intent]

                self.logger.info(
                    f"spaCy matched intent: {best_intent} (confidence: {confidence})")
                self.logger.info(f"Extracted entities: {entities}")

                return best_intent, entities

            # If no clear intent, try context clues
            context_intent = self._analyze_context_clues(doc)
            if context_intent:
                return context_intent, entities

            return 'unknown', entities

        except Exception as e:
            self.logger.error(f"spaCy intent recognition error: {e}")
            return 'unknown', {}

    def _analyze_context_clues(self, doc) -> Optional[str]:
        """Analyze context clues for better intent recognition"""
        text = doc.text.lower()

        # Weather context clues
        weather_clues = ['outside', 'today',
                         'tomorrow', 'hot', 'cold', 'rain', 'sun']
        if any(clue in text for clue in weather_clues) and any(word in text for word in ['what', 'how', 'is']):
            return 'weather'

        # Time context clues
        if any(word in text for word in ['what', 'tell', 'current']) and 'now' in text:
            return 'time'

        # Timer/alarm context clues
        if any(word in text for word in ['minutes', 'seconds', 'hours']) and any(word in text for word in ['set', 'timer', 'alarm']):
            return 'timer'

        # Math context clues
        if any(op in text for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divided']):
            return 'calculate'

        # Question patterns
        if text.startswith(('what', 'how', 'when', 'where', 'tell me')):
            if any(word in text for word in ['weather', 'temperature']):
                return 'weather'
            elif any(word in text for word in ['time', 'clock']):
                return 'time'
            elif any(word in text for word in ['date', 'day']):
                return 'date'
            elif any(word in text for word in ['battery', 'storage', 'memory']):
                return 'system'

        return None

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
                # Taking audio input from user's mic
                print("🎤Listening...")
                self.logger.debug("Starting to listen for audio input 🎤")

                # Adjusting for ambient noise to increase user voice accuracy
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

                # FIXED: Better threshold management
                if self.recognizer.energy_threshold > 800:
                    self.recognizer.energy_threshold = 800
                    print("⚡ Energy threshold was too high, capped at 800")

                # Listening to audio
                audio = self.recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=15
                )

                print("🔄 Processing Speech...")

                # Connect to google's speech recognition software
                command = self.recognizer.recognize_google(
                    audio, language='en-US')

                command = command.strip().lower()

                self.logger.info(f"User said: '{command}'")
                print(f"You said: {command}")

                # Add to conversation history
                self.conversation_history.append({
                    'timestamp': dt.datetime.now().isoformat(),
                    'user_input': command,
                    'type': 'user_speech'
                })

                return command

        except sr.WaitTimeoutError:
            self.logger.warning(
                "Speech recognition timeout - no speech detected.")
            return "timeout"

        except sr.UnknownValueError:
            self.logger.warning(
                "Speech recognition failed - could not understand audio")
            return "unclear"

        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return "service_error"

        except Exception as e:
            self.logger.error(f"Unexpected error in listen(): {e}")
            return "error"

    def recognize_command(self, query: str) -> Optional[str]:
        """Original regex-based command recognition (kept for compatibility)"""
        if not query:
            return None
        query = query.lower().strip()

        # Checking every command pattern
        for command, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    self.logger.debug(
                        f"Matched command '{command}' with pattern: {pattern}")
                    return command

        # If no matching pattern found, the command is unknown
        self.logger.debug(f"No command pattern matched for: {query}")
        return 'unknown'

    def execute_command(self, command: str, original_query: str, entities: Dict = None):
        """Enhanced command execution with entity support"""
        if entities is None:
            entities = {}

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
            elif command == 'weather':
                self.handle_weather_enhanced(original_query, entities)
            elif command == 'timer':
                self.handle_timer(original_query, entities)
            elif command == 'alarm':
                self.handle_alarm(original_query, entities)
            elif command == 'stopwatch':
                self.handle_stopwatch(original_query, entities)
            elif command == 'app':
                self.handle_app_launch(original_query, entities)
            elif command == 'search':
                self.handle_web_search(original_query, entities)
            elif command == 'calculate':
                self.handle_calculation(original_query, entities)
            elif command == 'system':
                self.handle_system_info(original_query, entities)
            elif command == 'unknown':
                self.handle_unknown_command(original_query)
            elif command in ['timeout', 'unclear', 'service_error', 'error']:
                self.handle_recognition_error(command)
            else:
                self.logger.warning(f"Unhandled command: {command}")

        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            self.speak(
                "I encountered an error while processing your request. Please try again.")

    def handle_timer(self, query: str, entities: Dict):
        """Handle timer commands"""
        try:
            # Extract time duration from query
            duration_seconds = self._parse_time_duration(query)

            if duration_seconds > 0:
                timer_id = self.timer_manager.set_timer(duration_seconds)
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60

                if minutes > 0:
                    time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
                    if seconds > 0:
                        time_str += f" and {seconds} second{'s' if seconds != 1 else ''}"
                else:
                    time_str = f"{seconds} second{'s' if seconds != 1 else ''}"

                self.speak(
                    f"Timer set for {time_str}. I'll let you know when it's done.")
            else:
                self.speak(
                    "I couldn't understand the timer duration. Please try saying something like 'set timer for 5 minutes'.")

        except Exception as e:
            self.logger.error(f"Timer error: {e}")
            self.speak("Sorry, I couldn't set the timer. Please try again.")

    def handle_alarm(self, query: str, entities: Dict):
        """Handle alarm commands"""
        try:
            # Extract time from query
            alarm_time = self._parse_alarm_time(query)

            if alarm_time:
                alarm_id = self.timer_manager.set_alarm(alarm_time)
                time_str = alarm_time.strftime("%I:%M %p")
                self.speak(f"Alarm set for {time_str}. I'll wake you up then.")
            else:
                self.speak(
                    "I couldn't understand the alarm time. Please try saying something like 'set alarm for 7 AM'.")

        except Exception as e:
            self.logger.error(f"Alarm error: {e}")
            self.speak("Sorry, I couldn't set the alarm. Please try again.")

    def handle_stopwatch(self, query: str, entities: Dict):
        """Handle stopwatch commands"""
        try:
            query_lower = query.lower()

            if 'start' in query_lower:
                if self.stopwatch_manager.start():
                    self.speak("Stopwatch started.")
                else:
                    self.speak("Stopwatch is already running.")

            elif 'stop' in query_lower:
                elapsed = self.stopwatch_manager.stop()
                formatted_time = self.stopwatch_manager.format_time(elapsed)
                self.speak(
                    f"Stopwatch stopped. Elapsed time: {formatted_time}")

            elif 'reset' in query_lower:
                self.stopwatch_manager.reset()
                self.speak("Stopwatch reset.")

            else:
                # Show current time
                elapsed = self.stopwatch_manager.get_time()
                formatted_time = self.stopwatch_manager.format_time(elapsed)
                status = "running" if self.stopwatch_manager.running else "stopped"
                self.speak(
                    f"Stopwatch is {status}. Elapsed time: {formatted_time}")

        except Exception as e:
            self.logger.error(f"Stopwatch error: {e}")
            self.speak("Sorry, I encountered an error with the stopwatch.")

    def handle_app_launch(self, query: str, entities: Dict):
        """Handle app launching"""
        try:
            # Extract app name from query
            app_name = self._extract_app_name(query)

            if app_name and app_name in self.app_mappings:
                success = self._launch_app(app_name)
                if success:
                    self.speak(f"Opening {app_name}.")
                else:
                    self.speak(f"Sorry, I couldn't open {app_name}.")
            else:
                self.speak(
                    "I couldn't identify which application to open. Try saying 'open Chrome' or 'launch Calculator'.")

        except Exception as e:
            self.logger.error(f"App launch error: {e}")
            self.speak("Sorry, I couldn't launch the application.")

    def handle_web_search(self, query: str, entities: Dict):
        """Handle web search requests"""
        try:
            # Extract search term
            search_term = self._extract_search_term(query)

            if search_term:
                search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                webbrowser.open(search_url)
                self.speak(f"Searching for {search_term} on Google.")
            else:
                self.speak("What would you like me to search for?")
                search_response = self.listen()
                if search_response and search_response not in ["timeout", "unclear", "service_error", "error"]:
                    search_url = f"https://www.google.com/search?q={search_response.replace(' ', '+')}"
                    webbrowser.open(search_url)
                    self.speak(f"Searching for {search_response} on Google.")

        except Exception as e:
            self.logger.error(f"Web search error: {e}")
            self.speak("Sorry, I couldn't perform the search.")

    def handle_calculation(self, query: str, entities: Dict):
        """Handle mathematical calculations"""
        try:
            result = self._evaluate_math_expression(query)

            if result is not None:
                self.speak(f"The answer is {result}")
            else:
                self.speak(
                    "I couldn't understand the calculation. Try asking something like 'what's 15 times 23?'")

        except Exception as e:
            self.logger.error(f"Calculation error: {e}")
            self.speak("Sorry, I couldn't perform that calculation.")

    def handle_system_info(self, query: str, entities: Dict):
        """Handle system information requests"""
        try:
            query_lower = query.lower()

            if 'battery' in query_lower:
                battery = psutil.sensors_battery()
                if battery:
                    percent = battery.percent
                    plugged = "plugged in" if battery.power_plugged else "not plugged in"
                    self.speak(f"Battery is at {percent}% and {plugged}.")
                else:
                    self.speak(
                        "Sorry, I couldn't get battery information. You might be on a desktop computer.")

            elif 'storage' in query_lower or 'disk' in query_lower:
                disk_usage = psutil.disk_usage('/')
                total_gb = disk_usage.total / (1024**3)
                free_gb = disk_usage.free / (1024**3)
                used_percent = (disk_usage.used / disk_usage.total) * 100
                self.speak(
                    f"You have {free_gb:.1f} GB free out of {total_gb:.1f} GB total. Disk is {used_percent:.1f}% full.")

            elif 'memory' in query_lower or 'ram' in query_lower:
                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024**3)
                available_gb = memory.available / (1024**3)
                used_percent = memory.percent
                self.speak(
                    f"You have {available_gb:.1f} GB of RAM available out of {total_gb:.1f} GB total. Memory usage is {used_percent:.1f}%.")

            elif 'cpu' in query_lower:
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                self.speak(
                    f"CPU usage is {cpu_percent}% across {cpu_count} cores.")

            else:
                # General system info
                battery = psutil.sensors_battery()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                info = "Here's your system information: "

                if battery:
                    info += f"Battery at {battery.percent}%. "

                info += f"Memory usage is {memory.percent}%. "
                info += f"Disk is {(disk.used/disk.total)*100:.1f}% full."

                self.speak(info)

        except Exception as e:
            self.logger.error(f"System info error: {e}")
            self.speak("Sorry, I couldn't get the system information.")

    def _parse_time_duration(self, query: str) -> int:
        """Parse time duration from natural language"""
        total_seconds = 0

        # Extract hours
        hours_match = re.search(r'(\d+)\s*(?:hours?|hrs?)', query.lower())
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600

        # Extract minutes
        minutes_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', query.lower())
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        # Extract seconds
        seconds_match = re.search(r'(\d+)\s*(?:seconds?|secs?)', query.lower())
        if seconds_match:
            total_seconds += int(seconds_match.group(1))

        # If no specific unit found, assume minutes if only one number
        if total_seconds == 0:
            number_match = re.search(r'(\d+)', query)
            if number_match:
                # Default to minutes for single numbers
                total_seconds = int(number_match.group(1)) * 60

        return total_seconds

    def _parse_alarm_time(self, query: str) -> Optional[dt.time]:
        """Parse alarm time from natural language"""
        # Try to match various time formats
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})',
            r'(\d{4})'  # 24-hour format like 0730
        ]

        query_lower = query.lower()

        for pattern in time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    if len(match.groups()) == 3:  # Hour:minute AM/PM
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        ampm = match.group(3)

                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0

                    # Hour AM/PM
                    elif len(match.groups()) == 2 and match.group(2) in ['am', 'pm']:
                        hour = int(match.group(1))
                        minute = 0
                        ampm = match.group(2)

                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0

                    elif len(match.groups()) == 2:  # Hour:minute (24-hour assumed)
                        hour = int(match.group(1))
                        minute = int(match.group(2))

                    else:  # 4-digit format
                        time_str = match.group(1)
                        hour = int(time_str[:2])
                        minute = int(time_str[2:])

                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return dt.time(hour, minute)

                except ValueError:
                    continue

        return None

    def _extract_app_name(self, query: str) -> Optional[str]:
        """Extract application name from query"""
        query_lower = query.lower()

        # Remove common command words
        cleaned = re.sub(r'\b(open|launch|start|run|execute)\b',
                         '', query_lower).strip()

        # Check for exact matches first
        for app in self.app_mappings.keys():
            if app in cleaned:
                return app

        # Check for partial matches
        for app in self.app_mappings.keys():
            app_words = app.split()
            if any(word in cleaned for word in app_words):
                return app

        return None

    def _launch_app(self, app_name: str) -> bool:
        """Launch an application"""
        try:
            executables = self.app_mappings.get(app_name, [])

            for exe in executables:
                try:
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(exe, shell=True)
                    else:  # Unix-like systems
                        subprocess.Popen([exe])

                    self.logger.info(
                        f"Successfully launched {app_name} using {exe}")
                    return True

                except (subprocess.SubprocessError, FileNotFoundError):
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Error launching {app_name}: {e}")
            return False

    def _extract_search_term(self, query: str) -> Optional[str]:
        """Extract search term from query"""
        # Remove command words
        patterns = [
            r'search\s+for\s+(.+)',
            r'look\s+up\s+(.+)',
            r'google\s+(.+)',
            r'find\s+(.+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1).strip()

        return None

    def _evaluate_math_expression(self, query: str) -> Optional[float]:
        """Evaluate mathematical expressions from natural language"""
        try:
            # Clean the query and convert to math expression
            expression = self._convert_to_math_expression(query)

            if expression:
                # Safe evaluation of mathematical expressions
                # Only allow basic math operations and numbers
                allowed_chars = set('0123456789+-*/.() ')
                if all(c in allowed_chars for c in expression):
                    result = eval(expression)
                    return round(result, 6) if isinstance(result, float) else result

            return None

        except Exception as e:
            self.logger.error(f"Math evaluation error: {e}")
            return None

    def _convert_to_math_expression(self, query: str) -> Optional[str]:
        """Convert natural language to mathematical expression"""
        query = query.lower().strip()

        # Handle "what's" or "what is"
        query = re.sub(r"what'?s\s+", "", query)
        query = re.sub(r"what\s+is\s+", "", query)
        query = re.sub(r"calculate\s+", "", query)

        # Replace word operators with symbols
        replacements = [
            (r'\bplus\b', '+'),
            (r'\bminus\b', '-'),
            (r'\btimes\b', '*'),
            (r'\bmultiplied\s+by\b', '*'),
            (r'\bdivided\s+by\b', '/'),
            (r'\bover\b', '/'),
            (r'\bto\s+the\s+power\s+of\b', '**'),
            (r'\bsquared\b', '**2'),
            (r'\bcubed\b', '**3'),
            (r'\bx\b', '*'),  # Handle "x" as multiplication
            (r'×', '*'),      # Handle multiplication symbol
            (r'÷', '/'),      # Handle division symbol
        ]

        for pattern, replacement in replacements:
            query = re.sub(pattern, replacement, query)

        # Extract mathematical expression - more flexible pattern
        math_pattern = r'[\d+\-*/().\s]+'
        match = re.search(math_pattern, query)

        if match:
            expression = match.group().strip()
            # Basic validation - ensure we have numbers and operators
            if (any(char.isdigit() for char in expression) and
                any(op in expression for op in ['+', '-', '*', '/']) and
                    len(expression.replace(' ', '')) > 2):
                return expression

        # Fallback: try to find number operator number pattern
        number_op_pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/x×÷])\s*(\d+(?:\.\d+)?)'
        match = re.search(number_op_pattern, query)
        if match:
            num1, op, num2 = match.groups()
            if op in ['x', '×']:
                op = '*'
            elif op == '÷':
                op = '/'
            return f"{num1} {op} {num2}"

        return None

    def _extract_city_from_query(self, query: str) -> Optional[str]:
        """Extract city name from weather query with better filtering"""
        # More specific regex patterns for city extraction
        city_patterns = [
            # "weather in Paris" or "weather for New York"
            r'weather (?:in|for) ([a-zA-Z\s]{2,30})(?:\?|$)',
            # "temperature in London"
            r'temperature (?:in|for) ([a-zA-Z\s]{2,30})(?:\?|$)',
            # "how's weather in Tokyo"
            r'(?:how\'?s (?:the )?weather (?:in|at)) ([a-zA-Z\s]{2,30})(?:\?|$)',
            # "what's weather like in Berlin"
            r'(?:what\'?s (?:the )?weather (?:like )?(?:in|at)) ([a-zA-Z\s]{2,30})(?:\?|$)',
        ]

        for pattern in city_patterns:
            match = re.search(pattern, query.lower())
            if match:
                potential_city = match.group(1).strip()

                # Filter out common words that aren't cities
                city_words = potential_city.split()
                filtered_words = [
                    word for word in city_words if word.lower() not in self.non_city_words]

                if filtered_words:
                    city = ' '.join(filtered_words)
                    # Basic validation - city should be reasonable length and not all common words
                    if 2 <= len(city) <= 50 and not all(word.lower() in self.non_city_words for word in city.split()):
                        return city

        return None

    def _is_general_weather_query(self, query: str) -> bool:
        """Check if this is a general weather query without specific location"""
        general_patterns = [
            r'^what\'?s (?:the )?weather (?:like|going to be)?(?:\?)?$',
            r'^how\'?s (?:the )?weather(?:\?)?$',
            r'^weather (?:report|forecast|update)(?:\?)?$',
            r'^what\'?s (?:the )?weather (?:like )?(?:today|tomorrow|outside)(?:\?)?$',
            r'^tell me (?:about )?(?:the )?weather(?:\?)?$',
            r'^weather(?:\?)?$'
        ]

        query_clean = query.lower().strip()
        for pattern in general_patterns:
            if re.match(pattern, query_clean):
                return True
        return False

    def handle_weather_enhanced(self, query: str, entities: Dict):
        """Enhanced weather handling with spaCy entity extraction"""
        try:
            city = None

            # First check if we extracted a city from spaCy
            if entities and entities.get('cities'):
                # Filter spaCy entities to remove common words
                valid_cities = [city for city in entities['cities']
                                if city.lower() not in self.non_city_words]
                if valid_cities:
                    city = valid_cities[0]  # Use first valid detected city
                    self.logger.info(f"spaCy extracted valid city: {city}")

            # If no valid city from spaCy, try improved regex extraction
            if not city:
                city = self._extract_city_from_query(query)
                if city:
                    self.logger.info(f"Regex extracted city: {city}")

            # Check if this is a general weather query
            if not city and self._is_general_weather_query(query):
                self.speak(
                    "Which city would you like to know the weather for?")
                city_response = self.listen()
                if city_response and city_response not in ["timeout", "unclear", "service_error", "error"]:
                    # Clean the city response
                    potential_city = self._extract_city_from_query(
                        f"weather in {city_response}")
                    if potential_city:
                        self.get_weather(potential_city)
                    else:
                        # Use the response directly if no extraction worked
                        clean_city = ' '.join([word for word in city_response.split()
                                               if word.lower() not in self.non_city_words])
                        if clean_city:
                            self.get_weather(clean_city)
                        else:
                            self.speak(
                                "I couldn't understand the city name. Please try again.")
                else:
                    self.speak(
                        "I didn't catch the city name. Please try asking again.")
                return

            if city:
                self.get_weather(city)
            else:
                # Fallback - ask for city
                self.speak(
                    "I couldn't determine which city you're asking about. Which city's weather would you like to know?")
                city_response = self.listen()
                if city_response and city_response not in ["timeout", "unclear", "service_error", "error"]:
                    clean_city = ' '.join([word for word in city_response.split()
                                           if word.lower() not in self.non_city_words])
                    if clean_city:
                        self.get_weather(clean_city)
                    else:
                        self.speak(
                            "I couldn't understand the city name. Please try again.")
                else:
                    self.speak(
                        "I didn't catch the city name. Please try asking again.")

        except Exception as e:
            self.logger.error(f"Error in handle_weather_enhanced: {e}")
            self.speak("Sorry, I couldn't process the weather request.")

    def handle_recognition_error(self, error_type: str):
        """Handle different types of speech recognition errors"""
        if error_type == 'timeout':
            self.speak(
                "I didn't hear anything. Please try speaking again.", False)
        elif error_type == 'unclear':
            self.speak(
                "I'm sorry, I couldn't understand what you said. Could you please repeat that?", False)
        elif error_type == 'service_error':
            self.speak(
                "I'm having trouble with the speech service. Please check your internet connection.", False)
        elif error_type == 'error':
            self.speak(
                "I encountered an unexpected error while listening. Let me try again.", False)

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

            # Log command execution
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

            # Date formatting
            formatted_date = today.strftime("%A, %B %d, %Y")

            # Contextual info
            if today.weekday() >= 5:
                context = "It's the weekend!"
            else:
                context = "It's a weekday."

            response = f"Today is {formatted_date}. {context}"
            self.speak(response)

            # Log command execution
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
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                self.speak("API key for weather service is missing.")
                return
            base_url = "https://api.openweathermap.org/data/2.5/weather"

            if country:
                location = (f"{city}, {country}")
            else:
                location = city

            params = {
                "q": location,
                "appid": api_key,
                "units": "metric"
            }

            response = requests.get(base_url, params=params)
            data = response.json()

            # Check if city is found
            if data.get("cod") != 200:
                self.speak(
                    f"I couldn't find any information on {city}. Please check the city name and try again.")
                return

            # Extracting weather info
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            # Create a weather report
            weather_report = (
                f"The weather in {city} is {weather_desc} with a temperature of {temp} degrees Celsius, humidity is at {humidity}%. The wind speed is {wind_speed} metres per second.")
            # Make aurora speak the weather report
            self.speak(weather_report)

        except Exception as e:
            self.logger.error(
                f"Error occurred while fetching the weather report: {e}")
            self.speak(
                "Sorry, I was unable to retrieve the weather information right now.")

    def handle_weather(self, query: str):
        """Original weather handler (kept for compatibility)"""
        self.handle_weather_enhanced(query, {})

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

        ⏰ Time & Date: "What time is it?", "What's today's date?"
        🌤️  Weather: "What's the weather like in London?"
        ⏲️  Timers: "Set a timer for 5 minutes", "Set alarm for 7 AM"
        ⏱️  Stopwatch: "Start stopwatch", "Stop stopwatch", "Reset stopwatch"
        🚀 Apps: "Open Chrome", "Launch Calculator", "Start Notepad"
        🔍 Search: "Search for Python tutorials", "Look up weather forecast"
        🧮 Math: "What's 15 times 23?", "Calculate 100 divided by 7"
        💻 System: "What's my battery level?", "How much storage do I have?"
        👋 Greetings: Say hello and I'll greet you back
        ❓ Help: Ask for help to hear this message again
        🔚 Exit: Say "stop", "exit", or "goodbye" to end our conversation

        I understand natural language, so just speak naturally!
        """

        self.speak("Here are the things I can help you with: I can tell you the time and date, provide weather information, set timers and alarms, control a stopwatch, launch applications, search the web, do calculations, show system information, respond to greetings, provide help, and exit when you're done. I understand natural language, so just speak naturally!")
        print(help_text)

    def handle_unknown_command(self, query: str):
        responses = [
            "I'm not sure how to help with that. You can ask about time, weather, set timers, launch apps, do calculations, or say 'help' for more options.",
            "I didn't recognize that command. I can help with time, weather, timers, apps, calculations, system info, and more. Try saying 'help' to see everything I can do.",
            "I'm still learning! Right now I can help with many things like timers, weather, launching apps, and calculations. Say 'help' for the full list."
        ]

        import random
        response = random.choice(responses)
        self.speak(response)

        # Log unknown commands for future expansion and development
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

        # Log exit command
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
        print(
            f"\n🤖 {self.name} Voice Assistant 3.0 - Enhanced with Core Features")
        print("=" * 70)

        # Welcome message
        welcome_msg = (
            f"Hello! I'm {self.name}, your enhanced voice assistant. I can now set timers, launch apps, do calculations, and much more!")
        self.speak(welcome_msg)

        print("\n💡 New Features Available:")
        print("🎯 Timers & Alarms: 'Set timer for 10 minutes', 'Set alarm for 7 AM'")
        print("🎯 Stopwatch: 'Start stopwatch', 'Stop stopwatch', 'Reset stopwatch'")
        print("🎯 App Launcher: 'Open Chrome', 'Launch Calculator', 'Start Notepad'")
        print("🎯 Web Search: 'Search for Python tutorials', 'Look up the weather'")
        print("🎯 Calculator: 'What's 25 times 4?', 'Calculate 100 divided by 7'")
        print("🎯 System Info: 'What's my battery level?', 'How much storage do I have?'\n")

        # Main interaction loop
        while self.is_listening:
            try:
                # Listen for user input
                query = self.listen()

                # Skip empty queries and error states that don't need processing
                if not query or query in ['timeout', 'unclear', 'service_error', 'error']:
                    if query in ['timeout', 'unclear', 'service_error', 'error']:
                        self.handle_recognition_error(query)
                    continue

                # Enhanced command recognition with spaCy
                command, entities = self.enhanced_command_recognition(query)

                # Execute the appropriate command
                self.execute_command(command, query, entities)

                # Small delay to prevent overwhelming the user
                time.sleep(0.5)

            except KeyboardInterrupt:
                print("\n\n⚠️  Keyboard interrupt detected.")
                self.speak("Stopping the assistant.")
                break

            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                self.speak(
                    "I encountered an unexpected error. Let me try to continue.")
                continue

        print("\n✅ Aurora has shut down successfully.")


def main():
    try:
        # Check for required dependencies
        print("🔧 Checking dependencies...")

        # Check if notifications are available
        if NOTIFICATIONS_AVAILABLE:
            print("✅ Notifications available")
        else:
            print(
                "⚠️  Notifications not available (install plyer or win10toast for timer notifications)")

        # Check if psutil is available for system info
        try:
            psutil.cpu_percent()
            print("✅ System information features available")
        except:
            print("⚠️  System information features limited")

        # Create and run the enhanced voice assistant
        assistant = VoiceAssistant("Aurora")
        assistant.run()

    except Exception as e:
        print(f"❌ Failed to start the voice assistant: {e}")
        logging.error(f"Application startup failed: {e}")


if __name__ == "__main__":
    main()  # Only match "stop" by itself, not "stop stopwatch"
    {
        'help': [
            r'\b(help|what\s+can\s+you\s+do|commands|assistance)\b'
        ],
        'weather': [
            r'\b(weather|current weather|forecast)\b',
            r'\b(temperature in|weather in)\b'
        ],
        'timer': [
            r'\b(set\s+timer|timer\s+for|countdown)\b'
        ],
        'alarm': [
            r'\b(set\s+alarm|alarm\s+for|wake\s+me)\b'
        ],
        'stopwatch': [
            r'\b(start\s+stopwatch|stop\s+stopwatch|reset\s+stopwatch|stopwatch)\b',
            r'\b(start|stop|reset)\s+(the\s+)?stopwatch\b'
        ],
        'app': [
            r'\b(open|launch|start|run)\s+\w+\b'
        ],
        'search': [
            r'\b(search\s+for|look\s+up|google|find)\b'
        ],
        'calculate': [
            r'\b(calculate|what\'s|whats|what\s+is)\s+.*[\+\-\*\/x×÷]\b',
            r'\b\d+\s*(plus|minus|times|divided\s+by|x|\*|\/|\+|\-)\s*\d+\b',
            r'\bwhat\s+is\s+\d+.*\d+\b'
        ],
        'system': [
            r'\b(battery\s+level|storage|disk\s+space|memory|system\s+info)\b'
        ]
    }

    def enhanced_command_recognition(self, query: str) -> tuple[Optional[str], Dict]:
        """Enhanced command recognition using spaCy NLU"""
        if not query:
            return None, {}

        # First try regex patterns (existing system)
        regex_result = self.recognize_command(query)
        if regex_result != 'unknown':
            self.logger.info(f"Regex matched: {regex_result}")
            return regex_result, {}

        # If regex fails, try spaCy NLU
        if self.nlp:
            return self._spacy_intent_recognition(query)

        return 'unknown', {}

    def _spacy_intent_recognition(self, query: str) -> tuple[str, Dict]:
        """Use spaCy for intelligent intent recognition and entity extraction"""
        try:
            doc = self.nlp(query.lower())

            # Extract entities
            entities = {
                'cities': [],
                'dates': [],
                'times': [],
                'locations': [],
                'numbers': [],
                'apps': []
            }

            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:  # Geopolitical entities, locations
                    entities['cities'].append(ent.text)
                elif ent.label_ in ['DATE', 'TIME']:
                    entities['dates'].append(ent.text)
                elif ent.label_ == 'TIME':
                    entities['times'].append(ent.text)
                elif ent.label_ in ['CARDINAL', 'QUANTITY']:
                    entities['numbers'].append(ent.text)

            # Extract numbers and time units for timers
            numbers = re.findall(r'\d+', query)
            if numbers:
                entities['numbers'].extend(numbers)

            # Extract app names
            for app in self.app_mappings.keys():
                if app in query.lower():
                    entities['apps'].append(app)

            # Intent classification using keyword matching with confidence
            intent_scores = {}

            for intent, keywords in self.intent_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword in query.lower():
                        score += 1
                    # Check for semantic similarity with spaCy
                    for token in doc:
                        if token.similarity(self.nlp(keyword)[0]) > 0.7:
                            score += 0.5

                if score > 0:
                    intent_scores[intent] = score

            # Get the highest scoring intent
            if intent_scores:
                best_intent = max(intent_scores, key=intent_scores.get)
                confidence = intent_scores[best_intent]

                self.logger.info(
                    f"spaCy matched intent: {best_intent} (confidence: {confidence})")
                self.logger.info(f"Extracted entities: {entities}")

                return best_intent, entities

            # If no clear intent, try context clues
            context_intent = self._analyze_context_clues(doc)
            if context_intent:
                return context_intent, entities

            return 'unknown', entities

        except Exception as e:
            self.logger.error(f"spaCy intent recognition error: {e}")
            return 'unknown', {}

    def _analyze_context_clues(self, doc) -> Optional[str]:
        """Analyze context clues for better intent recognition"""
        text = doc.text.lower()

        # Weather context clues
        weather_clues = ['outside', 'today',
                         'tomorrow', 'hot', 'cold', 'rain', 'sun']
        if any(clue in text for clue in weather_clues) and any(word in text for word in ['what', 'how', 'is']):
            return 'weather'

        # Time context clues
        if any(word in text for word in ['what', 'tell', 'current']) and 'now' in text:
            return 'time'

        # Timer/alarm context clues
        if any(word in text for word in ['minutes', 'seconds', 'hours']) and any(word in text for word in ['set', 'timer', 'alarm']):
            return 'timer'

        # Math context clues
        if any(op in text for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divided']):
            return 'calculate'

        # Question patterns
        if text.startswith(('what', 'how', 'when', 'where', 'tell me')):
            if any(word in text for word in ['weather', 'temperature']):
                return 'weather'
            elif any(word in text for word in ['time', 'clock']):
                return 'time'
            elif any(word in text for word in ['date', 'day']):
                return 'date'
            elif any(word in text for word in ['battery', 'storage', 'memory']):
                return 'system'

        return None

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
                # Taking audio input from user's mic
                print("🎤Listening...")
                self.logger.debug("Starting to listen for audio input 🎤")

                # Adjusting for ambient noise to increase user voice accuracy
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

                # FIXED: Better threshold management
                if self.recognizer.energy_threshold > 800:
                    self.recognizer.energy_threshold = 800
                    print("⚡ Energy threshold was too high, capped at 800")

                # Listening to audio
                audio = self.recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=15
                )

                print("🔄 Processing Speech...")

                # Connect to google's speech recognition software
                command = self.recognizer.recognize_google(
                    audio, language='en-US')

                command = command.strip().lower()

                self.logger.info(f"User said: '{command}'")
                print(f"You said: {command}")

                # Add to conversation history
                self.conversation_history.append({
                    'timestamp': dt.datetime.now().isoformat(),
                    'user_input': command,
                    'type': 'user_speech'
                })

                return command

        except sr.WaitTimeoutError:
            self.logger.warning(
                "Speech recognition timeout - no speech detected.")
            return "timeout"

        except sr.UnknownValueError:
            self.logger.warning(
                "Speech recognition failed - could not understand audio")
            return "unclear"

        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return "service_error"

        except Exception as e:
            self.logger.error(f"Unexpected error in listen(): {e}")
            return "error"

    def recognize_command(self, query: str) -> Optional[str]:
        """Original regex-based command recognition (kept for compatibility)"""
        if not query:
            return None
        query = query.lower().strip()

        # Checking every command pattern
        for command, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    self.logger.debug(
                        f"Matched command '{command}' with pattern: {pattern}")
                    return command

        # If no matching pattern found, the command is unknown
        self.logger.debug(f"No command pattern matched for: {query}")
        return 'unknown'

    def execute_command(self, command: str, original_query: str, entities: Dict = None):
        """Enhanced command execution with entity support"""
        if entities is None:
            entities = {}

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
            elif command == 'weather':
                self.handle_weather_enhanced(original_query, entities)
            elif command == 'timer':
                self.handle_timer(original_query, entities)
            elif command == 'alarm':
                self.handle_alarm(original_query, entities)
            elif command == 'stopwatch':
                self.handle_stopwatch(original_query, entities)
            elif command == 'app':
                self.handle_app_launch(original_query, entities)
            elif command == 'search':
                self.handle_web_search(original_query, entities)
            elif command == 'calculate':
                self.handle_calculation(original_query, entities)
            elif command == 'system':
                self.handle_system_info(original_query, entities)
            elif command == 'unknown':
                self.handle_unknown_command(original_query)
            elif command in ['timeout', 'unclear', 'service_error', 'error']:
                self.handle_recognition_error(command)
            else:
                self.logger.warning(f"Unhandled command: {command}")

        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            self.speak(
                "I encountered an error while processing your request. Please try again.")

    def handle_timer(self, query: str, entities: Dict):
        """Handle timer commands"""
        try:
            # Extract time duration from query
            duration_seconds = self._parse_time_duration(query)

            if duration_seconds > 0:
                timer_id = self.timer_manager.set_timer(duration_seconds)
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60

                if minutes > 0:
                    time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
                    if seconds > 0:
                        time_str += f" and {seconds} second{'s' if seconds != 1 else ''}"
                else:
                    time_str = f"{seconds} second{'s' if seconds != 1 else ''}"

                self.speak(
                    f"Timer set for {time_str}. I'll let you know when it's done.")
            else:
                self.speak(
                    "I couldn't understand the timer duration. Please try saying something like 'set timer for 5 minutes'.")

        except Exception as e:
            self.logger.error(f"Timer error: {e}")
            self.speak("Sorry, I couldn't set the timer. Please try again.")

    def handle_alarm(self, query: str, entities: Dict):
        """Handle alarm commands"""
        try:
            # Extract time from query
            alarm_time = self._parse_alarm_time(query)

            if alarm_time:
                alarm_id = self.timer_manager.set_alarm(alarm_time)
                time_str = alarm_time.strftime("%I:%M %p")
                self.speak(f"Alarm set for {time_str}. I'll wake you up then.")
            else:
                self.speak(
                    "I couldn't understand the alarm time. Please try saying something like 'set alarm for 7 AM'.")

        except Exception as e:
            self.logger.error(f"Alarm error: {e}")
            self.speak("Sorry, I couldn't set the alarm. Please try again.")

    def handle_stopwatch(self, query: str, entities: Dict):
        """Handle stopwatch commands"""
        try:
            query_lower = query.lower()

            if 'start' in query_lower:
                if self.stopwatch_manager.start():
                    self.speak("Stopwatch started.")
                else:
                    self.speak("Stopwatch is already running.")

            elif 'stop' in query_lower:
                elapsed = self.stopwatch_manager.stop()
                formatted_time = self.stopwatch_manager.format_time(elapsed)
                self.speak(
                    f"Stopwatch stopped. Elapsed time: {formatted_time}")

            elif 'reset' in query_lower:
                self.stopwatch_manager.reset()
                self.speak("Stopwatch reset.")

            else:
                # Show current time
                elapsed = self.stopwatch_manager.get_time()
                formatted_time = self.stopwatch_manager.format_time(elapsed)
                status = "running" if self.stopwatch_manager.running else "stopped"
                self.speak(
                    f"Stopwatch is {status}. Elapsed time: {formatted_time}")

        except Exception as e:
            self.logger.error(f"Stopwatch error: {e}")
            self.speak("Sorry, I encountered an error with the stopwatch.")

    def handle_app_launch(self, query: str, entities: Dict):
        """Handle app launching"""
        try:
            # Extract app name from query
            app_name = self._extract_app_name(query)

            if app_name and app_name in self.app_mappings:
                success = self._launch_app(app_name)
                if success:
                    self.speak(f"Opening {app_name}.")
                else:
                    self.speak(f"Sorry, I couldn't open {app_name}.")
            else:
                self.speak(
                    "I couldn't identify which application to open. Try saying 'open Chrome' or 'launch Calculator'.")

        except Exception as e:
            self.logger.error(f"App launch error: {e}")
            self.speak("Sorry, I couldn't launch the application.")

    def handle_web_search(self, query: str, entities: Dict):
        """Handle web search requests"""
        try:
            # Extract search term
            search_term = self._extract_search_term(query)

            if search_term:
                search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                webbrowser.open(search_url)
                self.speak(f"Searching for {search_term} on Google.")
            else:
                self.speak("What would you like me to search for?")
                search_response = self.listen()
                if search_response and search_response not in ["timeout", "unclear", "service_error", "error"]:
                    search_url = f"https://www.google.com/search?q={search_response.replace(' ', '+')}"
                    webbrowser.open(search_url)
                    self.speak(f"Searching for {search_response} on Google.")

        except Exception as e:
            self.logger.error(f"Web search error: {e}")
            self.speak("Sorry, I couldn't perform the search.")

    def handle_calculation(self, query: str, entities: Dict):
        """Handle mathematical calculations"""
        try:
            result = self._evaluate_math_expression(query)

            if result is not None:
                self.speak(f"The answer is {result}")
            else:
                self.speak(
                    "I couldn't understand the calculation. Try asking something like 'what's 15 times 23?'")

        except Exception as e:
            self.logger.error(f"Calculation error: {e}")
            self.speak("Sorry, I couldn't perform that calculation.")

    def handle_system_info(self, query: str, entities: Dict):
        """Handle system information requests"""
        try:
            query_lower = query.lower()

            if 'battery' in query_lower:
                battery = psutil.sensors_battery()
                if battery:
                    percent = battery.percent
                    plugged = "plugged in" if battery.power_plugged else "not plugged in"
                    self.speak(f"Battery is at {percent}% and {plugged}.")
                else:
                    self.speak(
                        "Sorry, I couldn't get battery information. You might be on a desktop computer.")

            elif 'storage' in query_lower or 'disk' in query_lower:
                disk_usage = psutil.disk_usage('/')
                total_gb = disk_usage.total / (1024**3)
                free_gb = disk_usage.free / (1024**3)
                used_percent = (disk_usage.used / disk_usage.total) * 100
                self.speak(
                    f"You have {free_gb:.1f} GB free out of {total_gb:.1f} GB total. Disk is {used_percent:.1f}% full.")

            elif 'memory' in query_lower or 'ram' in query_lower:
                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024**3)
                available_gb = memory.available / (1024**3)
                used_percent = memory.percent
                self.speak(
                    f"You have {available_gb:.1f} GB of RAM available out of {total_gb:.1f} GB total. Memory usage is {used_percent:.1f}%.")

            elif 'cpu' in query_lower:
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                self.speak(
                    f"CPU usage is {cpu_percent}% across {cpu_count} cores.")

            else:
                # General system info
                battery = psutil.sensors_battery()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                info = "Here's your system information: "

                if battery:
                    info += f"Battery at {battery.percent}%. "

                info += f"Memory usage is {memory.percent}%. "
                info += f"Disk is {(disk.used/disk.total)*100:.1f}% full."

                self.speak(info)

        except Exception as e:
            self.logger.error(f"System info error: {e}")
            self.speak("Sorry, I couldn't get the system information.")

    def _parse_time_duration(self, query: str) -> int:
        """Parse time duration from natural language"""
        total_seconds = 0

        # Extract hours
        hours_match = re.search(r'(\d+)\s*(?:hours?|hrs?)', query.lower())
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600

        # Extract minutes
        minutes_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', query.lower())
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        # Extract seconds
        seconds_match = re.search(r'(\d+)\s*(?:seconds?|secs?)', query.lower())
        if seconds_match:
            total_seconds += int(seconds_match.group(1))

        # If no specific unit found, assume minutes if only one number
        if total_seconds == 0:
            number_match = re.search(r'(\d+)', query)
            if number_match:
                # Default to minutes for single numbers
                total_seconds = int(number_match.group(1)) * 60

        return total_seconds

    def _parse_alarm_time(self, query: str) -> Optional[dt.time]:
        """Parse alarm time from natural language"""
        # Try to match various time formats
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})',
            r'(\d{4})'  # 24-hour format like 0730
        ]

        query_lower = query.lower()

        for pattern in time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    if len(match.groups()) == 3:  # Hour:minute AM/PM
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        ampm = match.group(3)

                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0

                    # Hour AM/PM
                    elif len(match.groups()) == 2 and match.group(2) in ['am', 'pm']:
                        hour = int(match.group(1))
                        minute = 0
                        ampm = match.group(2)

                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0

                    elif len(match.groups()) == 2:  # Hour:minute (24-hour assumed)
                        hour = int(match.group(1))
                        minute = int(match.group(2))

                    else:  # 4-digit format
                        time_str = match.group(1)
                        hour = int(time_str[:2])
                        minute = int(time_str[2:])

                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return dt.time(hour, minute)

                except ValueError:
                    continue

        return None

    def _extract_app_name(self, query: str) -> Optional[str]:
        """Extract application name from query"""
        query_lower = query.lower()

        # Remove common command words
        cleaned = re.sub(r'\b(open|launch|start|run|execute)\b',
                         '', query_lower).strip()

        # Check for exact matches first
        for app in self.app_mappings.keys():
            if app in cleaned:
                return app

        # Check for partial matches
        for app in self.app_mappings.keys():
            app_words = app.split()
            if any(word in cleaned for word in app_words):
                return app

        return None

    def _launch_app(self, app_name: str) -> bool:
        """Launch an application"""
        try:
            executables = self.app_mappings.get(app_name, [])

            for exe in executables:
                try:
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(exe, shell=True)
                    else:  # Unix-like systems
                        subprocess.Popen([exe])

                    self.logger.info(
                        f"Successfully launched {app_name} using {exe}")
                    return True

                except (subprocess.SubprocessError, FileNotFoundError):
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Error launching {app_name}: {e}")
            return False

    def _extract_search_term(self, query: str) -> Optional[str]:
        """Extract search term from query"""
        # Remove command words
        patterns = [
            r'search\s+for\s+(.+)',
            r'look\s+up\s+(.+)',
            r'google\s+(.+)',
            r'find\s+(.+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1).strip()

        return None

    def _evaluate_math_expression(self, query: str) -> Optional[float]:
        """Evaluate mathematical expressions from natural language"""
        try:
            # Clean the query and convert to math expression
            expression = self._convert_to_math_expression(query)

            if expression:
                # Safe evaluation of mathematical expressions
                # Only allow basic math operations and numbers
                allowed_chars = set('0123456789+-*/.() ')
                if all(c in allowed_chars for c in expression):
                    result = eval(expression)
                    return round(result, 6) if isinstance(result, float) else result

            return None

        except Exception as e:
            self.logger.error(f"Math evaluation error: {e}")
            return None

    def _convert_to_math_expression(self, query: str) -> Optional[str]:
        """Convert natural language to mathematical expression"""
        query = query.lower().strip()

        # Handle "what's" or "what is"
        query = re.sub(r"what'?s\s+", "", query)
        query = re.sub(r"what\s+is\s+", "", query)
        query = re.sub(r"calculate\s+", "", query)

        # Replace word operators with symbols
        replacements = [
            (r'\bplus\b', '+'),
            (r'\bminus\b', '-'),
            (r'\btimes\b', '*'),
            (r'\bmultiplied\s+by\b', '*'),
            (r'\bdivided\s+by\b', '/'),
            (r'\bover\b', '/'),
            (r'\bto\s+the\s+power\s+of\b', '**'),
            (r'\bsquared\b', '**2'),
            (r'\bcubed\b', '**3')
        ]

        for pattern, replacement in replacements:
            query = re.sub(pattern, replacement, query)

        # Extract mathematical expression
        math_pattern = r'[\d+\-*/().\s]+'
        match = re.search(math_pattern, query)

        if match:
            expression = match.group().strip()
            # Basic validation
            if any(char.isdigit() for char in expression) and any(op in expression for op in ['+', '-', '*', '/']):
                return expression

        return None

    def _extract_city_from_query(self, query: str) -> Optional[str]:
        """Extract city name from weather query with better filtering"""
        # More specific regex patterns for city extraction
        city_patterns = [
            # "weather in Paris" or "weather for New York"
            r'weather (?:in|for) ([a-zA-Z\s]{2,30})(?:\?|$)',
            # "temperature in London"
            r'temperature (?:in|for) ([a-zA-Z\s]{2,30})(?:\?|$)',
            # "how's weather in Tokyo"
            r'(?:how\'?s (?:the )?weather (?:in|at)) ([a-zA-Z\s]{2,30})(?:\?|$)',
            # "what's weather like in Berlin"
            r'(?:what\'?s (?:the )?weather (?:like )?(?:in|at)) ([a-zA-Z\s]{2,30})(?:\?|$)',
        ]

        for pattern in city_patterns:
            match = re.search(pattern, query.lower())
            if match:
                potential_city = match.group(1).strip()

                # Filter out common words that aren't cities
                city_words = potential_city.split()
                filtered_words = [
                    word for word in city_words if word.lower() not in self.non_city_words]

                if filtered_words:
                    city = ' '.join(filtered_words)
                    # Basic validation - city should be reasonable length and not all common words
                    if 2 <= len(city) <= 50 and not all(word.lower() in self.non_city_words for word in city.split()):
                        return city

        return None

    def _is_general_weather_query(self, query: str) -> bool:
        """Check if this is a general weather query without specific location"""
        general_patterns = [
            r'^what\'?s (?:the )?weather (?:like|going to be)?(?:\?)?$',
            r'^how\'?s (?:the )?weather(?:\?)?$',
            r'^weather (?:report|forecast|update)(?:\?)?$',
            r'^what\'?s (?:the )?weather (?:like )?(?:today|tomorrow|outside)(?:\?)?$',
            r'^tell me (?:about )?(?:the )?weather(?:\?)?$',
            r'^weather(?:\?)?$'
        ]

        query_clean = query.lower().strip()
        for pattern in general_patterns:
            if re.match(pattern, query_clean):
                return True
        return False

    def handle_weather_enhanced(self, query: str, entities: Dict):
        """Enhanced weather handling with spaCy entity extraction"""
        try:
            city = None

            # First check if we extracted a city from spaCy
            if entities and entities.get('cities'):
                # Filter spaCy entities to remove common words
                valid_cities = [city for city in entities['cities']
                                if city.lower() not in self.non_city_words]
                if valid_cities:
                    city = valid_cities[0]  # Use first valid detected city
                    self.logger.info(f"spaCy extracted valid city: {city}")

            # If no valid city from spaCy, try improved regex extraction
            if not city:
                city = self._extract_city_from_query(query)
                if city:
                    self.logger.info(f"Regex extracted city: {city}")

            # Check if this is a general weather query
            if not city and self._is_general_weather_query(query):
                self.speak(
                    "Which city would you like to know the weather for?")
                city_response = self.listen()
                if city_response and city_response not in ["timeout", "unclear", "service_error", "error"]:
                    # Clean the city response
                    potential_city = self._extract_city_from_query(
                        f"weather in {city_response}")
                    if potential_city:
                        self.get_weather(potential_city)
                    else:
                        # Use the response directly if no extraction worked
                        clean_city = ' '.join([word for word in city_response.split()
                                               if word.lower() not in self.non_city_words])
                        if clean_city:
                            self.get_weather(clean_city)
                        else:
                            self.speak(
                                "I couldn't understand the city name. Please try again.")
                else:
                    self.speak(
                        "I didn't catch the city name. Please try asking again.")
                return

            if city:
                self.get_weather(city)
            else:
                # Fallback - ask for city
                self.speak(
                    "I couldn't determine which city you're asking about. Which city's weather would you like to know?")
                city_response = self.listen()
                if city_response and city_response not in ["timeout", "unclear", "service_error", "error"]:
                    clean_city = ' '.join([word for word in city_response.split()
                                           if word.lower() not in self.non_city_words])
                    if clean_city:
                        self.get_weather(clean_city)
                    else:
                        self.speak(
                            "I couldn't understand the city name. Please try again.")
                else:
                    self.speak(
                        "I didn't catch the city name. Please try asking again.")

        except Exception as e:
            self.logger.error(f"Error in handle_weather_enhanced: {e}")
            self.speak("Sorry, I couldn't process the weather request.")

    def handle_recognition_error(self, error_type: str):
        """Handle different types of speech recognition errors"""
        if error_type == 'timeout':
            self.speak(
                "I didn't hear anything. Please try speaking again.", False)
        elif error_type == 'unclear':
            self.speak(
                "I'm sorry, I couldn't understand what you said. Could you please repeat that?", False)
        elif error_type == 'service_error':
            self.speak(
                "I'm having trouble with the speech service. Please check your internet connection.", False)
        elif error_type == 'error':
            self.speak(
                "I encountered an unexpected error while listening. Let me try again.", False)

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

            # Log command execution
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

            # Date formatting
            formatted_date = today.strftime("%A, %B %d, %Y")

            # Contextual info
            if today.weekday() >= 5:
                context = "It's the weekend!"
            else:
                context = "It's a weekday."

            response = f"Today is {formatted_date}. {context}"
            self.speak(response)

            # Log command execution
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
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                self.speak("API key for weather service is missing.")
                return
            base_url = "https://api.openweathermap.org/data/2.5/weather"

            if country:
                location = (f"{city}, {country}")
            else:
                location = city

            params = {
                "q": location,
                "appid": api_key,
                "units": "metric"
            }

            response = requests.get(base_url, params=params)
            data = response.json()

            # Check if city is found
            if data.get("cod") != 200:
                self.speak(
                    f"I couldn't find any information on {city}. Please check the city name and try again.")
                return

            # Extracting weather info
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            # Create a weather report
            weather_report = (
                f"The weather in {city} is {weather_desc} with a temperature of {temp} degrees Celsius, humidity is at {humidity}%. The wind speed is {wind_speed} metres per second.")
            # Make aurora speak the weather report
            self.speak(weather_report)

        except Exception as e:
            self.logger.error(
                f"Error occurred while fetching the weather report: {e}")
            self.speak(
                "Sorry, I was unable to retrieve the weather information right now.")

    def handle_weather(self, query: str):
        """Original weather handler (kept for compatibility)"""
        self.handle_weather_enhanced(query, {})

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

        ⏰ Time & Date: "What time is it?", "What's today's date?"
        🌤️  Weather: "What's the weather like in London?"
        ⏲️  Timers: "Set a timer for 5 minutes", "Set alarm for 7 AM"
        ⏱️  Stopwatch: "Start stopwatch", "Stop stopwatch", "Reset stopwatch"
        🚀 Apps: "Open Chrome", "Launch Calculator", "Start Notepad"
        🔍 Search: "Search for Python tutorials", "Look up weather forecast"
        🧮 Math: "What's 15 times 23?", "Calculate 100 divided by 7"
        💻 System: "What's my battery level?", "How much storage do I have?"
        👋 Greetings: Say hello and I'll greet you back
        ❓ Help: Ask for help to hear this message again
        🔚 Exit: Say "stop", "exit", or "goodbye" to end our conversation

        I understand natural language, so just speak naturally!
        """

        self.speak("Here are the things I can help you with: I can tell you the time and date, provide weather information, set timers and alarms, control a stopwatch, launch applications, search the web, do calculations, show system information, respond to greetings, provide help, and exit when you're done. I understand natural language, so just speak naturally!")
        print(help_text)

    def handle_unknown_command(self, query: str):
        responses = [
            "I'm not sure how to help with that. You can ask about time, weather, set timers, launch apps, do calculations, or say 'help' for more options.",
            "I didn't recognize that command. I can help with time, weather, timers, apps, calculations, system info, and more. Try saying 'help' to see everything I can do.",
            "I'm still learning! Right now I can help with many things like timers, weather, launching apps, and calculations. Say 'help' for the full list."
        ]

        import random
        response = random.choice(responses)
        self.speak(response)

        # Log unknown commands for future expansion and development
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

        # Log exit command
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
        print(
            f"\n🤖 {self.name} Voice Assistant 3.0 - Enhanced with Core Features")
        print("=" * 70)

        # Welcome message
        welcome_msg = (
            f"Hello! I'm {self.name}, your enhanced voice assistant. I can now set timers, launch apps, do calculations, and much more!")
        self.speak(welcome_msg)

        print("\n💡 New Features Available:")
        print("🎯 Timers & Alarms: 'Set timer for 10 minutes', 'Set alarm for 7 AM'")
        print("🎯 Stopwatch: 'Start stopwatch', 'Stop stopwatch', 'Reset stopwatch'")
        print("🎯 App Launcher: 'Open Chrome', 'Launch Calculator', 'Start Notepad'")
        print("🎯 Web Search: 'Search for Python tutorials', 'Look up the weather'")
        print("🎯 Calculator: 'What's 25 times 4?', 'Calculate 100 divided by 7'")
        print("🎯 System Info: 'What's my battery level?', 'How much storage do I have?'\n")

        # Main interaction loop
        while self.is_listening:
            try:
                # Listen for user input
                query = self.listen()

                # Skip empty queries and error states that don't need processing
                if not query or query in ['timeout', 'unclear', 'service_error', 'error']:
                    if query in ['timeout', 'unclear', 'service_error', 'error']:
                        self.handle_recognition_error(query)
                    continue

                # Enhanced command recognition with spaCy
                command, entities = self.enhanced_command_recognition(query)

                # Execute the appropriate command
                self.execute_command(command, query, entities)

                # Small delay to prevent overwhelming the user
                time.sleep(0.5)

            except KeyboardInterrupt:
                print("\n\n⚠️  Keyboard interrupt detected.")
                self.speak("Stopping the assistant.")
                break

            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                self.speak(
                    "I encountered an unexpected error. Let me try to continue.")
                continue

        print("\n✅ Aurora has shut down successfully.")


def main():
    try:
        # Check for required dependencies
        print("🔧 Checking dependencies...")

        # Check if notifications are available
        if NOTIFICATIONS_AVAILABLE:
            print("✅ Notifications available")
        else:
            print(
                "⚠️  Notifications not available (install plyer or win10toast for timer notifications)")

        # Check if psutil is available for system info
        try:
            psutil.cpu_percent()
            print("✅ System information features available")
        except:
            print("⚠️  System information features limited")

        # Create and run the enhanced voice assistant
        assistant = VoiceAssistant("Aurora")
        assistant.run()

    except Exception as e:
        print(f"❌ Failed to start the voice assistant: {e}")
        logging.error(f"Application startup failed: {e}")


if __name__ == "__main__":
    main()
