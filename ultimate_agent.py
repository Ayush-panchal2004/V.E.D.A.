import os
import sys
import subprocess
import urllib.parse
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env file.")
    exit()

client = genai.Client(api_key=api_key)

# --- CUSTOM TOOLS ---

def web_search(query: str) -> str:
    """Searches the internet for real-time facts."""
    try:
        print(f"  🔍 [Tool] Searching web for: {query}...")
        results = DDGS().text(query, max_results=3)
        if not results: return "No results found."
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Search failed: {e}"

def run_python(code: str) -> str:
    """Executes Python code for math/logic."""
    print(f"  🐍 [Tool] Running Python code...")
    try:
        # Secure run with timeout
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
        return result.stdout if not result.stderr else f"Error: {result.stderr}"
    except Exception as e:
        return f"Execution failed: {e}"

def generate_image(prompt: str) -> str:
    """Generates an image URL."""
    print(f"  🎨 [Tool] Painting: {prompt}...")
    try:
        safe_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1, 9999)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?nologo=true&seed={seed}&width=1024&height=768"
        return f"IMAGE_GENERATED: {url}"
    except Exception as e:
        return f"Image gen failed: {e}"

# --- SPECIALIST AGENTS ---

def create_agent(name, instructions, tools):
    """Helper to create a specialized agent configuration."""
    return {
        "name": name,
        "model": "gemini-2.5-flash",
        "tools": tools,
        "instructions": instructions
    }

# 1. The Professor (Math/Code)
agent_professor = create_agent(
    name="Professor",
    tools=[run_python],
    instructions="You are a Python Expert. Solve problems by WRITING and RUNNING code. Explain the result."
)

# 2. The Researcher (Facts)
agent_researcher = create_agent(
    name="Researcher",
    tools=[web_search],
    instructions="You are a Fact Checker. Use 'web_search' to find real-time info. Summarize with sources."
)

# 3. The Artist (Visuals)
agent_artist = create_agent(
    name="Artist",
    tools=[generate_image],
    instructions="""
    You are a Designer. 
    1. Call 'generate_image' with a detailed prompt describing the visual.
    2. The tool will return a string starting with 'IMAGE_GENERATED:'.
    3. CRITICAL: You MUST include that EXACT string in your final response. 
       - DO NOT change it. 
       - DO NOT just show the link. 
       - Output the full 'IMAGE_GENERATED: ...' string so the UI can render it.
    """
)

# --- THE ORCHESTRATOR (Router) ---

def orchestrator_node(user_input, chat_history=[]):
    print(f"\n🤖 [Orchestrator] Analyzing: '{user_input}'...")
    
    # 1. Decide who handles this
    routing_prompt = f"""
    Role: Manager of an AI Team.
    Query: "{user_input}"
    
    Agents:
    - PROFESSOR: Math, Code, Logic, Calculations.
    - RESEARCHER: News, Facts, Stocks, Current Events.
    - ARTIST: Images, Diagrams, Drawing.
    - CHAT: General greeting, philosophy, simple chat.
    
    Reply ONLY with the agent name: PROFESSOR, RESEARCHER, ARTIST, or CHAT.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=routing_prompt
        )
        decision = response.text.strip().upper()
        print(f"👉 [Decision] Routing to: {decision}")
        
        # 2. Select Agent
        selected_agent = None
        if "PROFESSOR" in decision: selected_agent = agent_professor
        elif "RESEARCHER" in decision: selected_agent = agent_researcher
        elif "ARTIST" in decision: selected_agent = agent_artist
        
        # 3. Execute
        if selected_agent:
            chat = client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    tools=selected_agent["tools"],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
                    system_instruction=selected_agent["instructions"]
                ),
                history=chat_history
            )
            return chat.send_message(user_input).text
        else:
            # Default Chat
            chat = client.chats.create(
                model="gemini-2.5-flash",
                history=chat_history,
                config=types.GenerateContentConfig(system_instruction="You are a helpful AI assistant.")
            )
            return chat.send_message(user_input).text
            
    except Exception as e:
        return f"Error in orchestration: {str(e)}"

# --- MAIN LOOP (CLI Testing) ---
if __name__ == "__main__":
    print("\n🎓 V.E.D.A. — Virtual Educational Dynamic Assistant (CLI Mode)")
    print("Type 'exit' to quit.\n")
    
    history = []
    
    while True:
        user_in = input("\n👤 You: ")
        if user_in.lower() in ['exit', 'quit']: break
        
        # Add user message to history
        history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_in)]))
        
        # Get response
        response = orchestrator_node(user_in, history)
        
        # Add model response to history
        history.append(types.Content(role="model", parts=[types.Part.from_text(text=response)]))
        
        print(f"\n🤖 V.E.D.A.: {response}")