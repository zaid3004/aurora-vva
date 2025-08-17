import eel
import threading
from voice_assistant import VoiceAssistant

# path to web directory
WEB_DIR = 'web'

# initialize eel with web folder
eel.init(WEB_DIR)
eel.start('index.html', port=8000)

assistant = VoiceAssistant("Aurora")
listening_thread = None

# eel.expose


def start_listening():
    global listening_thread

    def run_listen():
        eel.set_status("\N{Microphone} Listening...")
        query = assistant.listen()
        if query in ['timeout', 'unclear', 'service_error', 'error', None]:
            eel.display_user_text("")
            err_map = {
                "timeout": "Listening timed out.",
                "unclear": "Sorry, I couldn't understand you.",
                "service_error": "Speech service error.",
                "error": "Listening error."
            }
            eel.display_assitant_text(err_map.get(
                query, "Couldn't get speech input."))
            eel.set_wave_status('idle')
            eel.set_status("Idle")
            return

        eel.display_user_texr(query)
        eel.set_status("Processing...")

        command, entities = assistant.enhanced_command_recognition(query)
        response_collector = []

        original_speak = assistant.speak

        def intercept_speak(text, log_message=True):
            eel.display_assistant_text(text)
            response_collector.append(text)
            return original_speak(text, log_message)

        assistant.speak = intercept_speak
        assistant.execute_command(command, query, entities)
        assistant.speak = original_speak
        eel.set_status("Idle")

    eel.set_wave_status('listening')
    listening_thread = threading.Thread(target=run_listen)
    listening_thread.start()


@eel.expose
def stop_listening():
    assistant.is_listening = False
    eel.set_status("Idle")
    eel.set_wave_status('idle')


if __name__ == '__main__':
    eel.start(
        'index.html',
        size=(480, 620),
        block=True,
        close_callback=lambda route, websockets: None
    )
