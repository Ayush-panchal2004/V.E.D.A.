// 1. Session Management (Critical for Profiling "The Soul")
let sessionId = localStorage.getItem('sid') || Math.random().toString(36).substr(2);
localStorage.setItem('sid', sessionId);

let editor;

// 2. Initialize Monaco Editor
require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' } });
require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(document.getElementById('monaco-container'), {
        value: '# Code will appear here',
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true
    });
});

// 3. Send Message Logic
async function sendMessage() {
    const input = document.getElementById('user-input');
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, 'user');
    input.value = '';

    // Show "Thinking..." bubble
    const tempId = addMessage("Thinking...", 'ai', true);

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // We send session_id so the backend knows who you are
            body: JSON.stringify({ message: msg, session_id: sessionId })
        });
        const data = await res.json();

        // Remove "Thinking..."
        const tempElement = document.getElementById(tempId);
        if (tempElement) tempElement.remove();

        processResponse(data.response);
    } catch (e) {
        if (document.getElementById(tempId)) {
            document.getElementById(tempId).innerText = "Error: " + e;
        }
    }
}

// 4. Process Response & Magic Signals
function processResponse(text) {
    let cleanText = text;

    // A. Detect Image Signal
    const imgMatch = text.match(/IMAGE_GENERATED: (.*)/);
    if (imgMatch) {
        openLab('visual');
        const imgUrl = imgMatch[1].trim();
        document.getElementById('visual-container').innerHTML = `<img src="${imgUrl}">`;
        cleanText = cleanText.replace(imgMatch[0], "*(Visual Generated)*");
    }

    // B. Detect Code Signal (Improved Regex)
    // Catches ```python, ``` python, or just ``` code blocks
    const codeMatch = text.match(/```(python)?\s*([\s\S]*?)```/i);

    if (codeMatch) {
        // codeMatch[2] contains the actual code content
        const codeContent = codeMatch[2].trim();

        openLab('code');
        if (editor) editor.setValue(codeContent);

        // We keep the code in chat but ALSO open the lab (Better for UX)
        // cleanText = cleanText.replace(codeMatch[0], "*(Code sent to Lab)*");
    }

    addMessage(cleanText, 'ai');
}

// 5. Lab Controls (Slide Open/Close/Switch)
function openLab(type) {
    const app = document.querySelector('.app-container');
    const visLab = document.getElementById('visual-lab');
    const codeLab = document.getElementById('code-lab');

    // Slide Open Animation
    app.classList.add('active');

    // Switch Visible Tab
    if (type === 'visual') {
        visLab.style.display = 'flex';
        codeLab.style.display = 'none';
    } else {
        visLab.style.display = 'none';
        codeLab.style.display = 'flex';
    }
}

// Called by the "X" button
function closeLab() {
    const app = document.querySelector('.app-container');
    app.classList.remove('active'); // Slide Closed
}

// 6. Add Message (With Markdown Parsing!)
function addMessage(text, role, isTemp = false) {
    const div = document.createElement('div');
    div.className = `message ${role}-message`;

    if (isTemp) {
        div.id = 'temp-' + Date.now();
        div.innerText = text;
    } else {
        // Use Marked.js to render bold/italics/lists nicely
        if (typeof marked !== 'undefined') {
            div.innerHTML = marked.parse(text);
        } else {
            div.innerText = text; // Fallback if marked.js isn't loaded
        }
    }

    const history = document.getElementById('chat-history');
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
    return div.id;
}

// 7. Run Code Function
async function runCode() {
    if (!editor) return;
    const code = editor.getValue();
    const consoleOutput = document.getElementById('console-output');

    consoleOutput.innerText = "Running...";

    try {
        const res = await fetch('/run_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });
        const data = await res.json();
        consoleOutput.innerText = data.output;
    } catch (e) {
        consoleOutput.innerText = "Error: " + e;
    }
}