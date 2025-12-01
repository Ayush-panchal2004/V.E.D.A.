from flask import Flask, render_template, request, jsonify
import uuid
import os
# FIX: Import from the file you actually have (ultimate_agent)
from ultimate_agent import orchestrator_node, run_python

app = Flask(__name__)

# Ensure static folder exists for images
os.makedirs(os.path.join(app.root_path, 'static', 'generated'), exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message')
    
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Pass an empty history list for now (or manage it globally)
        response_text = orchestrator_node(user_msg, []) 
        return jsonify({"response": response_text})

    except Exception as e:
        print(f"SERVER ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/run_code', methods=['POST'])
def run_code_route():
    data = request.json
    code = data.get('code')
    # FIX: Use the function from ultimate_agent.py
    output = run_python(code)
    return jsonify({"output": output})

if __name__ == '__main__':
    app.run(debug=True, port=5000)