🦾 Bivium Veri AI: Agent Elena
📂 Project Structure & Architecture
To help you navigate the codebase, here is the functional breakdown of the Bivium Veri AI system:

* main1.py — The Entry Point: Manages the main execution loop, threading, and global application state.

* core/ — The Nervous System:

    * ai_engine.py: Handles Multimodal LLM logic, prompt engineering for
      "Agent Elena," and the automated model fallback system.

    * config.py: Centralized configuration for environment variables and API management.

* engines/ — Functional Modules:

    * voice.py: Real-time Text-to-Speech (TTS) engine using pyttsx3.

* ui/ — The Visual Layer:

    * hud.py: OpenCV-based rendering engine for the custom high-tech HUD and visual feedback.

* backend-test/ — Diagnostic Suite: Tools used to verify API stability and hardware integration during  development.

🚀 Getting Started
🛠 Prerequisites
Python 3.10+

Hardware: Working webcam and microphone (required for multimodal analysis).

API Key: A valid Google AI Studio API Key (Vertex AI compatible).

⚡ Quick Setup
Clone the repo:

Bash
git clone https://github.com/EduardKremen/Bivium-Veri-AI.git
cd Bivium-Veri-AI
Install dependencies:

Bash
pip install google-genai opencv-python pyttsx3 pillow python-dotenv
Configure Environment:
Create a .env file in the root directory:

Фрагмент кода
GOOGLE_API_KEY=your_actual_api_key_here
Launch Agent Elena:

Bash
python main.py
