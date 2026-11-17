# Nova FastAPI Chatbot

A rule-based chatbot served through FastAPI, with a responsive browser UI.

## Features
- Rule-based replies, greetings, mood detection, jokes and facts
- Session memory for user's name
- Safe arithmetic calculator
- Date/time responses
- Chat log saved in `logs/chat_history.txt`
- Responsive dark web interface
- Quick prompt buttons and reset chat
- FastAPI endpoints: `/`, `/api/chat`, `/api/reset`, `/api/health`

## Run on Windows
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Run on Linux / macOS / WSL
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 in your browser.
API documentation is available at http://127.0.0.1:8000/docs.

Note: this is a rule-based chatbot, not a generative AI model. Session data is stored in memory and is reset when the server restarts.
