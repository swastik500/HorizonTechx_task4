import ast
import operator
import random
import re
import time
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Nova Chatbot API")
# -------------------- PROJECT PATHS --------------------
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "chat_history.txt"
STATIC_DIR = BASE_DIR / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# -------------------- TERMINAL COLORS --------------------
class Color:
    RESET = "\033[0m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"

def paint(text, color):
    return f"{color}{text}{Color.RESET}"

# -------------------- CHATBOT DATA --------------------
GREETINGS = [
    "Hey there! What can I help you with?",
    "Hello! Nova is online. What's on your mind?",
    "Hi! Ready when you are.",
    "Hey! Nice to see you here."
]

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "Why did the computer go to the doctor? It had a virus.",
    "There are 10 kinds of people: those who understand binary and those who don't.",
    "Why was the Python developer calm? They knew how to handle exceptions."
]

HAPPY_REPLIES = [
    "That's great! Tell me what made your day.",
    "Love that energy! What's the good news?",
    "Nice! Keep that good vibe going."
]

SAD_REPLIES = [
    "I'm sorry you're having a rough time. Want to talk about what happened?",
    "That sounds difficult. I'm here to listen.",
    "Sometimes getting it off your chest can help. What's going on?"
]

ANGRY_REPLIES = [
    "Sounds like something really frustrated you. What happened?",
    "I hear you. Want to tell me what's making you angry?",
    "Take a breath. Let's unpack what's going on."
]

BORED_REPLIES = [
    "Want a joke, a random fact, or a mini challenge?",
    "Let's change that. Type 'joke' or 'fact'!",
    "Boredom alert! I can give you a riddle if you want."
]

FACTS = [
    "Octopuses have three hearts.",
    "A day on Venus is longer than its year.",
    "Honey can remain edible for a very long time when stored properly.",
    "The Python programming language is named after Monty Python, not the snake.",
    "The first computer bug was famously a real moth found in a computer."
]

HELP_TEXT = """
╭────────────────────── NOVA COMMANDS ──────────────────────╮
│ hello / hi / hey      - Start a greeting                │
│ my name is [name]     - Tell Nova your name             │
│ what is my name        - Ask Nova to recall your name    │
│ how are you            - Ask how Nova is doing          │
│ time / date            - Show current time or date      │
│ calculate 12 * 4       - Calculate a math expression     │
│ joke                   - Tell a random joke             │
│ fact                   - Share a random fact            │
│ help                   - Show this command list         │
│ clear                  - Clear the terminal             │
│ bye / exit / quit      - End the conversation           │
╰──────────────────────────────────────────────────────────╯
"""

# -------------------- SAFE CALCULATOR --------------------
# Only these mathematical operators are allowed.
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def evaluate_math(node):
    """Evaluate a limited arithmetic AST without using eval()."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = evaluate_math(node.left)
        right = evaluate_math(node.right)

        # Prevent excessively large exponent calculations.
        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("Exponent is too large. Try a power of 8 or less.")

        result = OPERATORS[type(node.op)](left, right)

        if abs(result) > 1e100:
            raise ValueError("That result is too large.")

        return result

    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate_math(node.operand))

    raise ValueError("I can only calculate basic arithmetic: + - * / // % ** and parentheses.")

def calculate(expression):
    expression = expression.strip()
    # Permit digits, whitespace, decimal points and basic math symbols only.
    if not re.fullmatch(r"[0-9+\-*/().%\s]+", expression):
        raise ValueError("Use numbers and basic math operators only.")

    tree = ast.parse(expression, mode="eval")
    return evaluate_math(tree.body)

# -------------------- CHAT LOGGING --------------------
def save_message(speaker, message):
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {speaker}: {message}\n")

# -------------------- RESPONSE ENGINE --------------------
class Nova:
    def __init__(self):
        self.user_name = None
        self.turn_count = 0

    def respond(self, user_text):
        text = user_text.strip()
        normalized = text.lower()
        self.turn_count += 1

        # Name recognition
        name_match = re.search(
            r"\bmy name is\s+([A-Za-z][A-Za-z0-9_-]{0,24})\b",
            text,
            re.IGNORECASE
        )
        if name_match:
            self.user_name = name_match.group(1).capitalize()
            return f"Nice to meet you, {self.user_name}! I'll remember your name while we're chatting."

        if normalized in {"what is my name", "do you know my name", "who am i"}:
            if self.user_name:
                return f"You're {self.user_name}!"
            return "You haven't told me your name yet. Try: my name is Alex"

        # Greetings
        if re.search(r"\b(hello|hi|hey|hiya|yo)\b", normalized):
            greeting = random.choice(GREETINGS)
            if self.user_name:
                greeting = greeting.replace("there", self.user_name)
            return greeting

        if re.search(r"\bgood morning\b", normalized):
            return "Good morning! Hope your day is off to a good start."

        if re.search(r"\bgood afternoon\b", normalized):
            return "Good afternoon! What are we working on today?"

        if re.search(r"\bgood evening\b", normalized):
            return "Good evening! How has your day been?"

        # Mood detection
        if re.search(r"\b(happy|great|awesome|excited|amazing|fantastic)\b", normalized):
            return random.choice(HAPPY_REPLIES)

        if re.search(r"\b(sad|upset|depressed|lonely|down)\b", normalized):
            return random.choice(SAD_REPLIES)

        if re.search(r"\b(angry|mad|furious|annoyed)\b", normalized):
            return random.choice(ANGRY_REPLIES)

        if re.search(r"\b(bored|boring)\b", normalized):
            return random.choice(BORED_REPLIES)

        # How are you?
        if re.search(r"\bhow are you\b", normalized):
            return random.choice([
                "I'm doing well, thanks for asking!",
                "All systems are running smoothly. How about you?",
                "I'm good! Ready to chat."
            ])

        # Name/purpose
        if re.search(r"\b(who are you|what are you)\b", normalized):
            return "I'm Nova, a Python rule-based chatbot. I use programmed rules to recognize messages and respond."

        if re.search(r"\bwhat can you do\b", normalized):
            return "I can chat, remember your name during this session, detect moods, calculate basic math, tell jokes and facts, and show the time. Type 'help' for commands."

        # Time and date
        if re.search(r"\b(time|what time is it)\b", normalized):
            return "The current time is " + datetime.now().strftime("%I:%M %p") + "."

        if re.search(r"\b(date|what is today's date|what day is it)\b", normalized):
            return "Today is " + datetime.now().strftime("%A, %B %d, %Y") + "."

        # Calculator command
        math_match = re.match(r"^(?:calculate|calc|what is)\s+(.+?)\??$", normalized)
        if math_match:
            expression = math_match.group(1)
            try:
                result = calculate(expression)
                return f"The answer is {result}."
            except (ValueError, SyntaxError, ZeroDivisionError) as error:
                return f"I couldn't calculate that: {error}"

        # Joke and fact
        if re.search(r"\b(joke|make me laugh|tell me something funny)\b", normalized):
            return random.choice(JOKES)

        if re.search(r"\b(fact|random fact|tell me something interesting)\b", normalized):
            return random.choice(FACTS)

        # Thanks
        if re.search(r"\b(thanks|thank you|thx)\b", normalized):
            return random.choice([
                "You're welcome!",
                "Anytime!",
                "Happy to help."
            ])

        # Help
        if normalized in {"help", "commands", "menu"}:
            return HELP_TEXT

        # Clear screen
        if normalized == "clear":
            print("\033[2J\033[H", end="")
            return "Terminal cleared. Nova is still here!"

        # Exit handled by main loop
        if normalized in {"bye", "goodbye", "exit", "quit"}:
            return "Goodbye! Thanks for chatting with Nova."

        # Basic follow-up prompts
        if normalized in {"yes", "yeah", "yep", "sure"}:
            return "Okay! Tell me a little more."

        if normalized in {"no", "nope", "nah"}:
            return "No problem. What would you like to talk about instead?"

        # Default fallback
        return random.choice([
            "I'm not sure I understand. Try rephrasing that.",
            "I don't know that one yet. Type 'help' to see what I can do.",
            "Interesting! I don't have a rule for that message yet.",
            "Could you tell me a bit more?"
        ])

# -------------------- FASTAPI API --------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ResetRequest(BaseModel):
    message: str | None = ""
    session_id: str | None = None


# Store bot instances per session
sessions = {}
bot_instance = Nova()


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


@app.get("/help")
def help_endpoint():
    return {"help": HELP_TEXT}


@app.post("/chat")
def chat(req: ChatRequest):
    user_text = req.message
    save_message("You", user_text)
    reply = bot_instance.respond(user_text)
    save_message("Nova", reply)
    return {"reply": reply, "session_id": req.session_id or "default"}


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    user_text = req.message
    save_message("You", user_text)
    # Use global bot instance (UI handles session in memory)
    reply = bot_instance.respond(user_text)
    save_message("Nova", reply)
    session_id = req.session_id or f"session_{id(bot_instance)}"
    return {"reply": reply, "session_id": session_id}


@app.post("/api/reset")
def api_reset(req: ResetRequest):
    # Reset bot instance state
    global bot_instance
    bot_instance = Nova()
    return {"status": "reset"}

    try:
        print(paint(r"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   ███╗   ██╗ ██████╗ ██╗   ██╗ █████╗                     ║
║   ████╗  ██║██╔═══██╗██║   ██║██╔══██╗                    ║
║   ██╔██╗ ██║██║   ██║██║   ██║███████║                    ║
║   ██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║                    ║
║   ██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║                    ║
║   ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝                    ║
║                                                            ║
║           RULE-BASED CHATBOT  |  PYTHON                   ║
╚════════════════════════════════════════════════════════════╝
""", Color.CYAN))
    except UnicodeError:
        print(paint("NOVA - RULE-BASED CHATBOT | PYTHON", Color.CYAN))
    print(paint("Nova: Hey! I'm Nova. Type 'help' to see what I can do.\n", Color.GREEN))

def main():
    bot = Nova()
    show_banner()

    while True:
        try:
            user_text = input(paint("You > ", Color.BLUE)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + paint("Nova > Chat ended. See you next time!", Color.GREEN))
            break

        if not user_text:
            print(paint("Nova > Type something so I can respond!", Color.YELLOW))
            continue

        save_message("You", user_text)

        if user_text.lower() in {"bye", "goodbye", "exit", "quit"}:
            reply = bot.respond(user_text)
            print(paint(f"Nova > {reply}", Color.GREEN))
            save_message("Nova", reply)
            break

        reply = bot.respond(user_text)
        print(paint(f"Nova > {reply}", Color.GREEN))
        save_message("Nova", reply)

if __name__ == "__main__":
    main()
