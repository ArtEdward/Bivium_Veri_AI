import os
from dotenv import load_dotenv

load_dotenv()
mic_volume = 0
# API та Секрети
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_PHRASE = os.getenv("ADMIN_SECRET_PHRASE", "код червоний")

# Налаштування заліза
VOICE_ID = 7  # Marianna (uk-UA)
#FS = 16000     # Частота дискретизації
#STRESS_LIMIT = 60
engine.setProperty('voice', voices[VOICE_ID].id)
# Візуал
FONT_PATH = "arial.ttf" # Переконайтеся, що цей файл є в папці
COLOR_SAFE = (0, 255, 0)
COLOR_DANGER = (0, 0, 255)
COLOR_AI = (255, 191, 0)
