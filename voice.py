import pyttsx3
import sounddevice as sd
import speech_recognition as sr
import numpy as np
import io
import threading
from scipy.io.wavfile import write
from core.config import VOICE_ID, FS

class ElenaVoice:
    def __init__(self):
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        if len(voices) > VOICE_ID:
            self.engine.setProperty('voice', voices[VOICE_ID].id)
        self.engine.setProperty('rate', 170)

    def speak(self, text):
        def _run():
            self.engine.say(text)
            self.engine.runAndWait()
        threading.Thread(target=_run, daemon=True).start()

    def listen(self, duration=4):
    r = sr.Recognizer()
    r.dynamic_energy_threshold = True # Авто-підлаштування під шум
    
    with sr.Microphone() as source:
        # Цей рядок критично важливий! 
        r.adjust_for_ambient_noise(source, duration=1) 
        try:
            # Зменшуємо таймаути для швидкості
            audio = r.listen(source, timeout=3, phrase_time_limit=duration)
            return r.recognize_google(audio, language="uk-UA").lower()
        except:
            return ""