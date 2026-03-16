# Використовуємо офіційний образ Python
FROM python:3.11-slim

# Встановлюємо системні залежності для OpenCV та звуку
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо файл залежностей
COPY requirements.txt .

# Встановлюємо бібліотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проекту
COPY . .

# Команда для запуску (хоча для локального GUI потрібен монітор, 
# Docker показує готовність до хмарного розгортання)
CMD ["python", "main1.py"]
