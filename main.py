import os, cv2, time, threading, pyttsx3, numpy as np, queue
import sounddevice as sd
import speech_recognition as sr
from PIL import Image, ImageDraw, ImageFont
from google import genai
from dotenv import load_dotenv

# --- НАЛАШТУВАННЯ ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Пріоритетний список моделей
MODEL_PRIORITY = [
    "gemini-2.0-flash", 
    "gemini-1.5-flash", 
    "gemini-2.0-flash-lite",
    "gemini-flash-latest"
]
# НАВЧАННЯ: Змінна має вказувати на конкретний рядок, а не на назву списку
CURRENT_MODEL = MODEL_PRIORITY[0] 

PHASE = "ОЧІКУВАННЯ"
USER_SPEECH = ""
mic_volume = 0
mic_monitor_active = True
audio_history = [0] * 50
speech_queue = queue.Queue()

# --- ГОЛОСОВИЙ МОДУЛЬ ---
engine_main = pyttsx3.init()
voices = engine_main.getProperty('voices')
engine_main.setProperty('voice', voices[7].id if len(voices) > 7 else voices[0].id)
engine_main.setProperty('rate', 240)

def speak_worker():
    while True:
        text = speech_queue.get()
        if text is None: break
        try:
            engine_main.say(text)
            engine_main.runAndWait()
        except: pass
        finally: speech_queue.task_done()

threading.Thread(target=speak_worker, daemon=True).start()

def speak(text):
    if text: speech_queue.put(text)

# --- ДОДАТКОВА ФУНКЦІЯ (ЯКУ ТИ ЗАБУВ ДОДАТИ У ФАЙЛ) ---
def get_elena_response(prompt):
    global CURRENT_MODEL
    for model_name in MODEL_PRIORITY:
        try:
            CURRENT_MODEL = model_name # Оновлюємо для відображення в HUD
            res = client.models.generate_content(model=model_name, contents=prompt)
            return res.text
        except Exception as e:
            if "429" in str(e): continue
            return None
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
    
    # НАВЧАННЯ: Шрифт треба завантажувати ДО того, як малювати текст
    try: font = ImageFont.truetype("arial.ttf", 24)
    except: font = ImageFont.load_default()

    # Малюємо статус та модель
    draw.text((30, 30), f"STATUS: {PHASE}", font=font, fill=(0, 255, 0))
    draw.text((w_f - 400, 30), f"CORE: {CURRENT_MODEL}", font=font, fill=(0, 200, 255))
    draw.text((30, h_f - 60), f"YOU: {USER_SPEECH}", font=font, fill=(255, 255, 255))
    
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.rectangle(frame, (15, h_f-50), (35, h_f-200), (30, 30, 30), -1)
    cv2.rectangle(frame, (15, h_f-50), (35, h_f-50-int(mic_volume*150)), (0, 255, 255), -1)
    for i in range(1, len(audio_history)):
        cv2.line(frame, (45+(i-1)*3, int(h_f-125-(audio_history[i-1]*40))), 
                 (45+i*3, int(h_f-125-(audio_history[i]*40))), (0, 255, 255), 1)
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
def interrogation_ptt():
    global PHASE, USER_SPEECH
    PHASE = "СЛУХАЮ..."
    ans = listen()
    
    if len(ans) > 1:
        PHASE = "ПРОФАЙЛІНГ..."
        try:
            system_instruction = (
                "Ти — Агент Олена, саркастичний профайлер. Використовуй НЛП. "
                "Ціль: виявити нестиковки. ОДНЕ коротке питання."
            )
            full_prompt = f"{system_instruction}\n\nВідповідь об'єкта: '{ans}'"
            
            response_text = get_elena_response(full_prompt)
            
            if response_text:
                PHASE = "ВЕРДИКТ"
                speak(response_text)
                print(f"Олена: {response_text}")
                time.sleep(5)
            else:
                PHASE = "ПЕРЕГРІВ"
                speak("Всі канали зв'язку заблоковано.")
                time.sleep(5)
        except Exception as e:
            print(f"Помилка: {e}")
    
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
        cv2.putText(frame, "HOLD 'S' TO TALK", (w//2-120, h-30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    
    cv2.imshow('Bivium Veri AI - Agent Elena', frame)

cap.release()
cv2.destroyAllWindows()

