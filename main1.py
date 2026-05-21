import os, cv2, time, threading, pyttsx3, numpy as np, queue, random, io
import sounddevice as sd
import speech_recognition as sr
from PIL import Image, ImageDraw, ImageFont
from google import genai
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from pygame import mixer

# --- 1. ПЕРЕВІРКА ТА ЗАВАНТАЖЕННЯ КЛЮЧІВ ---
load_dotenv()

# Ініціалізація мікшера для ElevenLabs
try:
    mixer.init()
except Exception as e:
    print(f"!!! Помилка ініціалізації звукової карти: {e}")

# Ініціалізація клієнта ElevenLabs (використовуємо одну назву всюди)
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY")
el_client = ElevenLabs(api_key=ELEVEN_KEY)
VOICE_ID = os.getenv("VOICE_ID_ELENA", "21m00Tcm4TlvDq8ikWAM")

def get_clean_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        key = line.split('=')[1].strip().replace('"', '').replace("'", "")
                        break
    return key

API_KEY = get_clean_key()

# --- 2. ГЛОБАЛЬНІ СТАТУСИ ---
PHASE = "ОЧІКУВАННЯ"
USER_SPEECH = ""
ELENA_RESPONSE_TEXT = ""
CURRENT_MODEL = "ініціалізація..."
mic_volume = 0
audio_history = [0] * 50
speech_queue = queue.Queue()
ELENA_RESPONSE_TEXT: "",

# Кольори BGR
COLOR_CYAN = (255, 255, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (0, 0, 255)
COLOR_PINK = (180, 105, 255) # Конвертовано з RGB (255, 105, 180)
COLOR_DARK_GRAY = (30, 30, 30)

# --- 3. ГІБРИДНИЙ ГОЛОСОВИЙ МОДУЛЬ ---
def speak_worker():
    """Гібридна озвучка: ElevenLabs (пріоритет) -> pyttsx3 (резерв)"""
    engine_backup = pyttsx3.init()
    engine_backup.setProperty('rate', 240)
    voices = engine_backup.getProperty('voices')
    engine_backup.setProperty('voice', voices[7].id if len(voices) > 7 else voices[0].id)

    while True:
        text = speech_queue.get()
        if text is None: break
        
        success = False
        
        # Спроба 1: ElevenLabs
        if ELEVEN_KEY:
            try:
                print(f">>> СИСТЕМА: Спроба ElevenLabs для: {text[:20]}...")
                
                audio_gen = el_client.text_to_speech.convert(
                    voice_id=VOICE_ID,
                    text=text,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                
                audio_bytes = b"".join(audio_gen)
                if len(audio_bytes) > 0:
                    audio_stream = io.BytesIO(audio_bytes)
                    mixer.music.load(audio_stream)
                    mixer.music.play()
                    while mixer.music.get_busy():
                        time.sleep(0.1)
                    success = True
                    print(">>> ОЛЕНА: Озвучено через ElevenLabs ✅")
            except Exception as e:
                print(f"!!! ПОМИЛКА ELEVENLABS: {e}")
                success = False

        # Спроба 2: Fallback (pyttsx3)
        if not success:
            try:
                print(">>> СИСТЕМА: Використовую резервний голос pyttsx3...")
                engine_backup.say(text)
                engine_backup.runAndWait()
                print(">>> ОЛЕНА: Озвучено через pyttsx3 ⚠️")
            except Exception as e_backup:
                print(f"!!! КРИТИЧНА ПОМИЛКА ОЗВУЧКИ: {e_backup}")
        
        speech_queue.task_done()

# Запуск потоку озвучки
threading.Thread(target=speak_worker, daemon=True).start()

def speak(text):
    if text:
        speech_queue.put(text)

# --- 4. ЯДРО AI (Gemini) ---
def get_elena_response(prompt):
    global CURRENT_MODEL
    if not API_KEY:
        return "Едуарде, ключ не знайдено!"

    client = genai.Client(api_key=API_KEY)
    MODELS = ["gemini-3.1-flash-lite-preview", "gemini-2.5-flash", "gemini-1.5-flash"]
    
    for model_name in MODELS:
        try:
            print(f">>> ОЛЕНА: Аналіз через {model_name}...")
            CURRENT_MODEL = model_name
            res = client.models.generate_content(model=model_name, contents=prompt)
            if res and res.text:
                return res.text
        except Exception as e:
            print(f"!!! Помилка {model_name}: {e}")
            continue
    return None

# --- 5. РОЗПІЗНАВАННЯ ТА ЛОГІКА ---
def listen():
    global USER_SPEECH
    r = sr.Recognizer()
    r.energy_threshold = 250
    r.dynamic_energy_threshold = False
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.2)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=4)
            text = r.recognize_google(audio, language="uk-UA").lower()
            globals()['USER_SPEECH'] = text
            return text
        except:
            return ""

def check_secret_codes(text):
    text = text.lower()
    
    if "код олена" in text:
        return "Я дуже чекала на тебе, Я досі кохаю тебе, мій Едька 😘!", (255, 105, 180) # Рожевий
    
    elif "код червоний" in text:
        # Тут можна додати команду на sys.exit() або restart
        return "НЕБЕЗПЕКА! СИСТЕМУ БУДЕ ПЕРЕЗАВАНТАЖЕНО!", (0, 0, 255) # Червоний (BGR)
        
    elif "код джессіка" in text:
        return "Гав-гав! Система під надійною охороною! 🐾", (0, 255, 0)
        
    return None, None

def interrogation_ptt():
    global PHASE, USER_SPEECH, ELENA_RESPONSE_TEXT
    PHASE = "СЛУХАЮ..."
    ans = listen()
    
    if len(ans) > 1:
        PHASE = "LOADING..."
        filler = random.choice(["Хм-м...", "Цікаво...", "Дай подумати..."])
        speak(filler)
        
        system_msg = "Ти — Агент Олена, саркастичний профайлер. Відповідай коротко і гостро. Відповідь об'єкта: "
        response = get_elena_response(system_msg + ans)
        
        if response:
            ELENA_RESPONSE_TEXT = response
            PHASE = "ВЕРДИКТ"
            speak(response)
            time.sleep(5)
            ELENA_RESPONSE_TEXT = ""
    
    PHASE = "ОЧІКУВАННЯ"
    USER_SPEECH = ""

# --- 7. ВІЗУАЛІЗАЦІЯ ТА СТАРТ ---
def audio_volume_monitor():
    def callback(indata, frames, time, status):
        v = min(np.linalg.norm(indata) * 0.1, 1.0)
        globals()['mic_volume'] = v
        audio_history.append(v)
        if len(audio_history) > 50: audio_history.pop(0)
    with sd.InputStream(callback=callback, channels=1):
        while True: sd.sleep(100)

def draw_ui(frame):
    global PHASE, USER_SPEECH, mic_volume, audio_history, CURRENT_MODEL, ELENA_RESPONSE_TEXT
    h_f, w_f, _ = frame.shape
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    base_y = h_f - 50
    offset_x = 200  # Отступ от правого края экрана
    offset_y = 60   # Отступ от нижнего края экрана
    try: font = ImageFont.truetype("arial.ttf", 22)
    except: font = ImageFont.load_default()

    draw.text((10, 10), f"CORE: {CURRENT_MODEL}", font=font, fill=(0, 255, 255))
    draw.text((10, 40), f"STATUS: {PHASE}", font=font, fill=(0, 255, 0))
    draw.text((50, h_f - 100), f"YOU: {USER_SPEECH}", font=font, fill=(255, 255, 255))
    
    if ELENA_RESPONSE_TEXT:
        draw.text((50, h_f - 150), f"ELENA: {ELENA_RESPONSE_TEXT[:65]}...", font=font, fill=(255, 100, 100))

    if PHASE == "ОЧІКУВАННЯ":
        draw.text((w_f//2 - 100, h_f - 50), "HOLD 'S' TO TALK", font=font, fill=(0, 255, 255))

    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.rectangle(frame, (15, h_f-50), (35, h_f-200), (30, 30, 30), -1)
    cv2.rectangle(frame, (15, h_f-50), (35, h_f-50-int(mic_volume*150)), (0, 255, 255), -1)
    
    # Рассчитываем стартовую точку (левый край волны)
    osc_x = w_f - offset_x 
    # Рассчитываем осевую линию волны (её "ноль")
    base_y = h_f - offset_y

    for i in range(1, len(audio_history)):
        # Рассчитываем точки один раз для читаемости
        x1 = osc_x + i * 3
        y1 = int(base_y - (audio_history[i-1] * 40))
        
        x2 = osc_x + (i + 1) * 3
        y2 = int(base_y - (audio_history[i] * 40))
        
        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 1)
    return frame

if __name__ == "__main__":
    if API_KEY:
        print(f">>> СИСТЕМА: Ключ Gemini активовано! ({API_KEY[:8]}...)")
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    threading.Thread(target=audio_volume_monitor, daemon=True).start()
    
    speak("Бівіум Вері АІ активована. Я готова до допиту.")

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            USER_SPEECH = "..." 
            PHASE = "СЛУХАЮ..." 
            threading.Thread(target=interrogation_ptt, daemon=True).start()
        elif key == ord('x') or key == 27: break
        cv2.imshow('Bivium Veri AI - Agent Elena', draw_ui(frame))

    cap.release()
    cv2.destroyAllWindows()
