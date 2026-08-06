import os
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Single-file HTML, CSS, and JS frontend with embedded WebLLM engine
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ZPlus Technologies - In-Browser AI Engine</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111726;
      --border: #1f293d;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --text: #f3f4f6;
      --muted: #9ca3af;
      --code-bg: #050811;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

    header {
      padding: 16px 24px;
      border-bottom: 1px solid var(--border);
      background: var(--card-bg);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .brand { display: flex; align-items: center; gap: 12px; }
    .brand h1 { font-size: 1.1rem; font-weight: 700; }
    .badge { font-size: 0.75rem; padding: 3px 8px; border-radius: 12px; background: rgba(59, 130, 246, 0.15); color: var(--accent); border: 1px solid rgba(59, 130, 246, 0.3); }

    main { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px; overflow: hidden; }
    .panel { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; }
    .panel-header { padding: 12px 16px; background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid var(--border); font-size: 0.85rem; font-weight: 600; color: var(--muted); text-transform: uppercase; }

    textarea { flex: 1; background: var(--code-bg); color: var(--text); border: none; padding: 16px; font-family: monospace; font-size: 0.9rem; line-height: 1.5; resize: none; outline: none; }
    .controls { padding: 12px 16px; border-top: 1px solid var(--border); display: flex; gap: 12px; justify-content: flex-end; }
    
    button { background: var(--accent); color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: background 0.2s; }
    button:hover:not(:disabled) { background: var(--accent-hover); }
    button:disabled { opacity: 0.5; cursor: not-allowed; }

    #output-container { flex: 1; background: var(--code-bg); padding: 16px; overflow-y: auto; font-family: monospace; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; }
    
    #progress-container { padding: 12px 16px; background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid var(--border); display: flex; flex-direction: column; gap: 6px; }
    .progress-bar-bg { width: 100%; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
    .progress-bar-fill { height: 100%; width: 0%; background: var(--accent); transition: width 0.2s ease; }
    .progress-text { font-size: 0.75rem; color: var(--muted); }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <h1>ZPlus Technologies</h1>
      <span class="badge">Python Server + In-Browser AI</span>
    </div>
    <span class="badge" id="gpu-status">Checking WebGPU...</span>
  </header>

  <main>
    <div class="panel">
      <div class="panel-header">1. Source Code / Prompt</div>
      <textarea id="user-input" placeholder="Type your prompt or request API docs here...&#10;&#10;Examples:&#10;- Write an async Python function to read a JSON file.&#10;- Show JS fetch API request syntax with try/catch."></textarea>
      <div class="controls">
        <button id="init-btn">Initialize Local Model (~200MB)</button>
        <button id="generate-btn" disabled>Generate Solution</button>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">2. Output Console</div>
      <div id="progress-container" style="display: none;">
        <div class="progress-bar-bg"><div class="progress-bar-fill" id="progress-fill"></div></div>
        <div class="progress-text" id="progress-text">Ready to initialize</div>
      </div>
      <div id="output-container">// Click initialize to load SmolLM2-360M directly into your browser VRAM...</div>
    </div>
  </main>

  <script type="module">
    import * as webllm from "https://esm.run/@mlc-ai/web-llm";

    const gpuStatus = document.getElementById("gpu-status");
    const initBtn = document.getElementById("init-btn");
    const generateBtn = document.getElementById("generate-btn");
    const userInput = document.getElementById("user-input");
    const outputContainer = document.getElementById("output-container");
    const progressContainer = document.getElementById("progress-container");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");

    const MODEL_NAME = "SmolLM2-360M-Instruct-q4f16_1-MLC";
    let engine = null;

    if ("gpu" in navigator) {
      navigator.gpu.requestAdapter().then(adapter => {
        if (adapter) {
          gpuStatus.textContent = "WebGPU Ready";
          gpuStatus.style.color = "#10b981";
        } else {
          gpuStatus.textContent = "WebGPU Unsupported";
          gpuStatus.style.color = "#ef4444";
          initBtn.disabled = true;
        }
      });
    } else {
      gpuStatus.textContent = "WebGPU Disabled";
      gpuStatus.style.color = "#ef4444";
      initBtn.disabled = true;
    }

    initBtn.addEventListener("click", async () => {
      initBtn.disabled = true;
      progressContainer.style.display = "flex";
      outputContainer.textContent = "// Downloading model weights to browser cache... (~200MB)";

      try {
        engine = await webllm.CreateMLCEngine(MODEL_NAME, {
          initProgressCallback: (progress) => {
            const percent = Math.floor(progress.progress * 100);
            progressFill.style.width = `${percent}%`;
            progressText.textContent = `${progress.text} (${percent}%)`;
          }
        });

        progressText.textContent = "Model active in local GPU memory!";
        outputContainer.textContent = "// Model loaded! Enter your prompt and click 'Generate Solution'.";
        generateBtn.disabled = false;
        initBtn.style.display = "none";
      } catch (err) {
        outputContainer.textContent = `// Error loading model: ${err.message}`;
        initBtn.disabled = false;
      }
    });

    generateBtn.addEventListener("click", async () => {
      const prompt = userInput.value.trim();
      if (!prompt || !engine) return;

      generateBtn.disabled = true;
      outputContainer.textContent = "";

      try {
        const completion = await engine.chat.completions.create({
          messages: [
            { role: "system", content: "You are a fast API and code generator built by ZPlus Technologies." },
            { role: "user", content: prompt }
          ],
          stream: true,
          temperature: 0.2
        });

        for await (const chunk of completion) {
          const delta = chunk.choices[0]?.delta?.content || "";
          outputContainer.textContent += delta;
          outputContainer.scrollTop = outputContainer.scrollHeight;
        }
      } catch (err) {
        outputContainer.textContent += `\\n\\n// Execution error: ${err.message}`;
      } finally {
        generateBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""

# Frontend route
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

# Python backend API endpoints
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "organization": "ZPlus Technologies",
        "ai_engine": "Client-Side WebGPU (SmolLM2-360M)"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
