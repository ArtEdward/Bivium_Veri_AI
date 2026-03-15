import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
from core.config import FONT_PATH

def draw_text_ua(img, text, position, font_size, color):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try: font = ImageFont.truetype(FONT_PATH, font_size)
    except: font = ImageFont.load_default()
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

def draw_mic_wave(frame, history, x, y, w, h, color):
    cv2.rectangle(frame, (x, y), (x+w, y+h), (20, 20, 20), -1)
    if not history: return
    bar_w = max(1, w // len(history))
    for i, vol in enumerate(history[-w//bar_w:]):
        bar_h = int(vol * h * 0.8)
        cv2.line(frame, (x+i*bar_w, y+h//2-bar_h//2), (x+i*bar_w, y+h//2+bar_h//2), color, 2)