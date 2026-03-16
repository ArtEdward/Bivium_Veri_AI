# Bivium Veri AI - Agent Elena 👁️⚖️

## How to run:
1. Install dependencies: `pip install opencv-python sounddevice speechrecognition pyttsx3 pillow google-genai python-dotenv`
2. Create a `.env` file and add: `GEMINI_API_KEY=your_key_here`
3. Run: `python main.py

🏗️ Bivium Veri AI: System Architecture
🧩 Компоненти системи:
Input Layer (Локальні сенсори):

Vision: OpenCV захоплює відеопотік 720p/1080p.

Audio: sounddevice моніторить рівень шуму, а SpeechRecognition перетворює твій голос на текст (STT).

Processing Core (Python 3.12):

Multithreading: Окремі потоки для камери, мікрофона та голосового двигуна (щоб інтерфейс не "гальмував").

UI/HUD: Динамічне малювання осцилограми та статусів поверх кадру за допомогою Pillow та NumPy.

Intelligence Layer (Google Cloud Platform):

Gemini 2.0 Flash: Основний "мозок" профайлера.

Fallback Logic: Твоя унікальна система перемикання моделей (2.5 -> 2.0 -> Lite) для забезпечення 100% аптайму під час пікових навантажень.

Output Layer (Зворотний зв'язок):

Voice (TTS): Двигун pyttsx3 з фіксом COMError для стабільної роботи на Windows.

Visual HUD: Миттєве відображення результатів аналізу на екрані.
`
## Concept:
A multimodal AI Profiler that uses a camera and microphone to engage in "interrogation" mode. Agent Elena analyzes your responses and uses NLP to find inconsistencies.
**Bivium Veri AI** (Latin for "The Fork of Truth") is a high-performance, real-time digital profiler built for the **Gemini Live Agent Challenge**. It leverages multimodal AI to analyze the cognitive stress and non-verbal cues involved when a human chooses between truth and deception.

## 🚀 Overview
Traditional chatbots are blind to human emotion. **Bivium Veri AI** sees beyond words. By utilizing the **Gemini Multimodal Live API**, the agent monitors eye-accessing patterns, micro-expressions, and vocal biomarkers to evaluate the authenticity of an interaction in real-time.

## ✨ Key Features
- **NLP Eye-Tracking:** Detects "Visual Construction" vs "Visual Recall" patterns.
- **Biometric Analysis:** Real-time monitoring of respiration and pupil dilation.
- **Multimodal Feedback:** A futuristic HUD dashboard providing a live "Confidence Score".
- **Interruption Handling:** Naturally reacts to user interruptions using Gemini's native Live capabilities.

## 🛠️ Tech Stack
- **AI Model:** Gemini 2.0 Flash (via Multimodal Live API)
- **Framework:** Google GenAI SDK (Python)
- **Cloud:** Google Cloud Run (Backend) & Vertex AI
- **Frontend:** React.js with Tailwind CSS (Glassmorphism UI)

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Google Cloud Project with Vertex AI API enabled
- Service Account Key (JSON)

### Backend Setup
1. Clone the repo:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Bivium-Veri-AI.git](https://github.com/YOUR_USERNAME/Bivium-Veri-AI.git)
   cd Bivium-Veri-AI/backend
