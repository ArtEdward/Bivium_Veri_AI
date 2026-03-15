import os
import cv2
import time
import threading
import pyttsx3
import numpy as np
import re
import io
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- ІНІЦІАЛІЗАЦІЯ ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "models/gemini-2.0-flash"

# --- ГЛОБАЛЬНІ СТАТУСИ ---
STRESS_LEVEL = 0
PHASE = "ОЧІКУВАННЯ"
USER_SPEECH = ""
mic_volume = 0
mic_monitor_active = True
is_active = False
captured_images = []
voice_wave_history = []
last_mic_update = time.time()
speech_lock = threading.Lock()

# --- СИСТЕМА ГОЛОСУ ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
# Індекс 7 - Маріанна (UA), якщо немає - беремо перший доступний
engine.setProperty('voice', voices[7].id if len(voices) > 7 else voices[0].id)
engine.setProperty('rate', 175)

def speak(text):
    def run_tts():
        # Блокуємо потік, щоб тільки одна фраза вимовлялася за раз
        with speech_lock:
            try:
                # Перевіряємо, чи ініціалізований двигун
                if engine._inLoop:
                    engine.endLoop()
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"Помилка голосу: {e}")
    threading.Thread(target=run_tts, daemon=True).start()

# --- ВІЗУАЛІЗАЦІЯ (HUD) ---
def draw_ui(frame):
    global STRESS_LEVEL, PHASE, USER_SPEECH, voice_wave_history
    h, w, _ = frame.shape
    color = (0, 0, 255) if STRESS_LEVEL > 60 else (0, 255, 0)
    
    # --- БАР ГУЧНОСТІ (Зліва) ---
    cv2.rectangle(frame, (10, h-50), (30, h-250), (30, 30, 30), -1) # Фон
    vol_h = int(mic_volume * 200) # mic_volume має бути від 0 до 1
    cv2.rectangle(frame, (10, h-50), (30, h-50-vol_h), (255, 255, 0), -1) # Жовтий бар
    
    # Головна рамка
    cv2.rectangle(frame, (10, 10), (w-10, h-10), color, 1)
    
    # Скануюча лінія
    line_y = int((time.time() * 150) % (h - 40) + 20)
    cv2.line(frame, (20, line_y), (w-20, line_y), color, 1)
    
    # Шкала стресу (вертикальна)
    cv2.rectangle(frame, (w-40, h-50), (w-20, h-250), (30, 30, 30), -1)
    bar_h = int((STRESS_LEVEL / 100) * 200)
    cv2.rectangle(frame, (w-40, h-50), (w-20, h-50-bar_h), color, -1)
    
    # Текст через Pillow (для підтримки кирилиці)
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try: font = ImageFont.truetype("arial.ttf", 24)
    except: font = ImageFont.load_default()
    
    draw.text((30, 30), f"СТАТУС: {PHASE}", font=font, fill=(color[2], color[1], color[0]))
    draw.text((30, h-60), f"ВИ: {USER_SPEECH}", font=font, fill=(255, 255, 255))
    
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    # Вивід твоєї мови (з автоматичним переносом)
    import textwrap
    lines = textwrap.wrap(f"ВИ: {USER_SPEECH}", width=40)
    for i, line in enumerate(lines):
        draw.text((50, h-100 + (i*25)), line, font=font, fill=(255, 255, 255))
    # Мікрофонна хвиля (динамічна)
    cv2.rectangle(frame, (30, h-150), (230, h-70), (20, 20, 20), -1)
    if voice_wave_history:
        for i, v in enumerate(voice_wave_history[-50:]):
            vh = int(v * 60)
            cv2.line(frame, (35+i*4, h-110-vh//2), (35+i*4, h-110+vh//2), color, 2)
            
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return frame

# --- ЛОГІКА СЛУХАННЯ ---
def listen():
    global USER_SPEECH, voice_wave_history, mic_monitor_active
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # Симуляція руху хвилі під час слухання
            voice_wave_history = [np.random.uniform(0.1, 0.8) for _ in range(50)]
            audio = r.listen(source, timeout=5, phrase_time_limit=4)
            text = r.recognize_google(audio, language="uk-UA").lower()
            USER_SPEECH = text
            return text
        except:
            voice_wave_history = [0.01] * 50
            return ""

# --- СЦЕНАРІЙ ---
def interrogation():
    # Всі глобальні змінні оголошуємо в ОДНОМУ рядку на самому початку
    global PHASE, STRESS_LEVEL, captured_images, USER_SPEECH, mic_monitor_active
    
    # 0.1 Вимикаємо монітор гучності, щоб звільнити мікрофон для Олени
    mic_monitor_active = False 
    time.sleep(0.1) # Даємо залізу "перепочити"
    
    # 1. Етап привітання
    PHASE = "ПРИВІТАННЯ"
    speak("Агент Олена готова до знайомства. Почнемо?")
    trigger_words = ["так", "готов", "давай", "старт", "да", "хочу", "погнали"]
    
    # 2. Перехід до слухання
    PHASE = "ГОЛОСОВА АКТИВАЦІЯ" 
    # Використовуємо voice.speak або просто speak (залежно від того, як названа функція)
    speak("Слухаю вас")
    PHASE = "СЛУХАЮ..."
    ans = listen()
    USER_SPEECH = ans # Оновлюємо текст на екрані
    
    # Секретний код
    if "код олена" in ans:
        speak("Я пам'ятаю, що кохаю тебе, Едька!")
        PHASE = "LOVE MODE"
        return

    # Логіка активації
    if any(w in ans for w in ["так", "готов", "давай", "старт"]):
        speak("Як вас зовуть ?")
        PHASE = "ВІДПОВІДЬ (ЗАПИС)"
        speak("Де ви народились")
        PHASE = "ВІДПОВІДЬ (ЗАПИС)"
        speak("Який номер вашої школи ?")
        PHASE = "ВІДПОВІДЬ (ЗАПИС)"
        captured_images = []
        time.sleep(5) # Час на відповідь та збір кадрів
        # 3. Повертаємо бар гучності в роботу
        mic_monitor_active = True     
        
        PHASE = "АНАЛІЗ ШІ..."
        try:
            parts = ["Проаналізуй кадри. Оціни стрес % та дай вердикт УКРАЇНСЬКОЮ."]
            for img in captured_images[:3]:
                _, b = cv2.imencode('.jpg', img)
                parts.append(types.Part.from_bytes(data=b.tobytes(), mime_type="image/jpeg"))
            
            res = client.models.generate_content(model=MODEL_ID, contents=parts)
            speak(res.text)
            
            nums = re.findall(r'\d+', res.text)
            if nums: STRESS_LEVEL = int(nums[0])
        except: 
            speak("Помилка зв'язку з ядром.")
    elif ans != "": # Якщо вона щось почула, але це не "так"
        speak(f"Ви сказали: {ans}. Але для початку обстеження мені потрібна ваша згода. Скажіть ТАК.")
        PHASE = "ОЧІКУВАННЯ"        
        
        PHASE = "ЗАВЕРШЕНО"
    else:
        PHASE = "ОЧІКУВАННЯ"
       

# --- ГОЛОВНИЙ ЦИКЛ ---
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    
    if PHASE == "ВІДПОВІДЬ (ЗАПИС)" and len(captured_images) < 10:
        captured_images.append(frame.copy())
    
    frame = draw_ui(frame)
    cv2.imshow('Agent Elena - Bivium Veri', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord(' '):
        threading.Thread(target=interrogation, daemon=True).start()
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
