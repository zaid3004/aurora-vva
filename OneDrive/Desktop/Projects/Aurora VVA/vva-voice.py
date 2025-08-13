import speech_recognition as sr
import pyttsx3 as pt

recognizer = sr.Recognizer()
engine = pt.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("Listening")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio)
        print("You said", command)
        return command.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't quite catch that. Could you please repeat?")
        return ""
    except sr.RequestError:
        speak("Sorry, looks like the servers are down. Want me to try again?")
        return ""
    

if __name__ == "__main__":
    speak("Hello, I am Aurora. How may I assist you today?")

    while True:
        query = listen()

        if "stop" in query or "exit" in query:
            speak("Goodbye!")
            break
        elif query:
            speak(f"You said: {query}")
