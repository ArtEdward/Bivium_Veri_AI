from google import genai
from google.genai import types
import cv2
from core.config import GEMINI_KEY

client = genai.Client(api_key=GEMINI_KEY)

def analyze_with_gemini(images):
    prompt = "Ти Агент Олена. Проаналізуй 3 кадри. Оціни стрес % та дай вердикт УКРАЇНСЬКОЮ."
    parts = [prompt]
    for img in images:
        _, b = cv2.imencode('.jpg', img)
        parts.append(types.Part.from_bytes(data=b.tobytes(), mime_type="image/jpeg"))
    
    try:
        res = client.models.generate_content(model="models/gemini-2.0-flash", contents=parts)
        return res.text
    except Exception as e:
        return f"Помилка ШІ: {str(e)}"