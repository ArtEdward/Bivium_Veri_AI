
import os, cv2, time, threading, pyttsx3, numpy as np, queue
import sounddevice as sd
import speech_recognition as sr
import random
from core.ai_engine import analyze_with_gemini
from core.config import VOICE_ID, VOICE_RATE
from PIL import Image, ImageDraw, ImageFont
from google import genai
from dotenv import load_dotenv

# --- НАЛАШТУВАННЯ ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# --- 1. СПОЧАТКУ СТВОРЮЄМО ЧЕРГУ ---
speech_queue = queue.Queue()
engine_main = pyttsx3.init()
voices = engine_main.getProperty('voices')
# Пріоритетний список моделей
MODEL_PRIORITY = [
    "gemini-2.0-flash", 
    "gemini-1.5-flash", 
    "gemini-2.0-flash-lite",
    "gemini-flash-latest","gemini-2.0-flash-exp", 
    "gemini-2.0-flash-lite-preview-02-05", 
    "gemini-1.5-flash"
]
# НАВЧАННЯ: Змінна має вказувати на конкретний рядок, а не на назву списку
CURRENT_MODEL = MODEL_PRIORITY[0] 
ELENA_RESPONSE_TEXT = "" # Тут ми будемо зберігати останню фразу Олени
PHASE = "ОЧІКУВАННЯ"
USER_SPEECH = ""
mic_volume = 0
mic_monitor_active = True
audio_history = [0] * 50
# Тепер ми використовуємо змінні з config.py
engine_main.setProperty('voice', voices[VOICE_ID].id if len(voices) > VOICE_ID else voices[0].id)
engine_main.setProperty('rate', VOICE_RATE)
# --- ПОТІМ ІНІЦІАЛІЗУЄМО ДВИГУН ГОЛОСУ ---

voices = engine_main.getProperty('voices')
# Голос зазвичай український на Win10/11, якщо ні — залиш 0 або 1
engine_main.setProperty('voice', voices[7].id if len(voices) > 7 else voices[0].id)
engine_main.setProperty('rate', 240)


# --- ГОЛОСОВИЙ МОДУЛЬ ---
def speak_worker():
    """Потік, який використовує вже ініціалізований двигун"""
    while True:
        text = speech_queue.get()
        if text is None: break
        try:
            # Важливо: runAndWait() має бути всередині обробки черги
            engine_main.say(text)
            engine_main.runAndWait()
        except Exception as e:
            print(f"Помилка голосу: {e}")
        finally:
            speech_queue.task_done()

# Запускаємо потік ОДИН РАЗ
threading.Thread(target=speak_worker, daemon=True).start()

def speak(text):
    if text:
        speech_queue.put(text)

# --- ДОДАТКОВА ФУНКЦІЯ (ЯКУ ТИ ЗАБУВ ДОДАТИ У ФАЙЛ) ---
def get_elena_response(prompt):
    global CURRENT_MODEL
    for model_name in MODEL_PRIORITY:
        try:
            CURRENT_MODEL = model_name
            res = client.models.generate_content(model=model_name, contents=prompt)
            # Якщо Gemini повернула порожню відповідь через фільтри
            if not res.text:
                print(f"Модель {model_name} повернула порожній текст (можливо фільтр)")
                continue
            return res.text
        except Exception as e:
            print(f"Помилка моделі {model_name}: {e}") # ТУТ ТИ ПОБАЧИШ ПРИЧИНУ
            continue
    return None

# --- АУДІО МОНІТОР ---
def audio_volume_monitor():
    global mic_volume, audio_history
    def callback(indata, frames, time, status):
        v = min(np.linalg.norm(indata) * 0.1, 1.0)
        globals()['mic_volume'] = v
        audio_history.append(v)
        if len(audio_history) > 50: audio_history.pop(0)
    with sd.InputStream(callback=callback, channels=1):
        while True: sd.sleep(100)

# --- HUD ---
def draw_ui(frame):
    global PHASE, USER_SPEECH, mic_volume, audio_history, CURRENT_MODEL
    h_f, w_f, _ = frame.shape
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    # Параметри осцилограми
    osc_x = w_f - 250  # позиція X (відступ від правого краю)
    osc_width = 200    # ширина області осцилограми
    try: font = ImageFont.truetype("arial.ttf", 24)
    except: font = ImageFont.load_default()

    # Статус та Модель
    draw.text((10, 40), f"STATUS: {PHASE}", font=font, fill=(0, 255, 0))
    draw.text((10, 10), f"CORE: {CURRENT_MODEL}", font=font, fill=(0, 255, 255))
    draw.text((50, h_f - 100), f"YOU: {USER_SPEECH}", font=font, fill=(255, 255, 255))
    
    # Підказка по центру (з виправленим textbbox)
    if PHASE == "ОЧІКУВАННЯ":
        prompt_text = "HOLD 'S' TO TALK"
        bbox = draw.textbbox((0, 0), prompt_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((w_f - tw) // 2, h_f - 100), prompt_text, font=font, fill=(0, 255, 255))

    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    # Малюємо осцилограму (OpenCV частина)
    cv2.rectangle(frame, (15, h_f-50), (35, h_f-200), (30, 30, 30), -1)
    cv2.rectangle(frame, (15, h_f-50), (35, h_f-50-int(mic_volume*150)), (0, 255, 255), -1)
    for i in range(1, len(audio_history)):
             cv2.line(frame, 
             (osc_x+30+(i-1)*3, int(h_f-125-(audio_history[i-1]*40))), 
             (osc_x+30+i*3, int(h_f-125-(audio_history[i]*40))), 
             (0, 255, 255), 1)
    return frame

def listen():
    global USER_SPEECH, mic_monitor_active
    r = sr.Recognizer()
    with sr.Microphone() as source:
        mic_monitor_active = False
        r.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            text = r.recognize_google(audio, language="uk-UA").lower()
            globals()['USER_SPEECH'] = text
            return text
        except: return ""
        finally: mic_monitor_active = True

# --- ЛОГІКА РАЦІЇ ---
ELENA_REACTIONS = [
    "Хм-м... Дай подумати.",
    "Цікаво, але чи правда це?",
    "Добре, я обробляю твою відповідь.",
    "Проаналізую твої слова...",
    "Чекай, мої алгоритми працюють.",
    "Ось мій вердикт..."
]
def interrogation_ptt():
    global PHASE, USER_SPEECH
    PHASE = "СЛУХАЮ..."
    ans = listen()
    
    if len(ans) > 1:
        PHASE = "LOADING..."
        # Олена каже випадкову фразу відразу, поки Gemini обробляє запит
        filler = random.choice(ELENA_REACTIONS)
        speak(filler)
        try:
            system_instruction = (
                "Ти — Агент Олена, саркастичний профайлер. Використовуй НЛП. "
                "Ціль: виявити нестиковки. ОДНЕ коротке питання."
            )
            PHASE = filler # Виводимо фразу на екран як статус
            full_prompt = f"{system_instruction}\n\nВідповідь об'єкта: '{ans}'"
            
            response_text = get_elena_response(full_prompt)
            
            if response_text:
                global ELENA_RESPONSE_TEXT
                ELENA_RESPONSE_TEXT = response_text # ЗАПИСУЄМО ДЛЯ HUD
                PHASE = "ВЕРДИКТ"
                speak(response_text)
                time.sleep(5)
            else:
                PHASE = "ПЕРЕГРІВ"
                speak("Всі канали зв'язку заблоковано.")
                time.sleep(5)
        except Exception as e:
            print(f"Помилка: {e}")
            speak("Помилка зв'язку.")
    PHASE = "ОЧІКУВАННЯ"
    USER_SPEECH = ""

# --- СТАРТ ---
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
threading.Thread(target=audio_volume_monitor, daemon=True).start()
speak("Бівіум Вері АІ активована. Олена готова.")

while True:
    ret, frame = cap.read()
    if not ret: break
    h, w, _ = frame.shape
    frame = cv2.flip(frame, 1)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'): 
        threading.Thread(target=interrogation_ptt, daemon=True).start()
    elif key == ord('c'):
        cap.release(); cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    elif key == ord('x') or key == 27: break

    frame = draw_ui(frame)
    if PHASE == "ОЧІКУВАННЯ":
        pass  # Ця команда каже Python "нічого не роби", і помилка зникне
    cv2.imshow('Bivium Veri AI - Agent Elena', frame)

cap.release()
cv2.destroyAllWindows()

