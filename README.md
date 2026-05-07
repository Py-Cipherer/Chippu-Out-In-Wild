markdown_content = """# Chippu: Out in Wild 🦅🌲

**Chippu: Out in Wild** is a high-performance, retro-style 2D arcade survival game that pushes the boundaries of traditional side-scrollers. Built with Python and Pygame, it features procedural level generation, a custom dynamic scaling engine, and an innovative cloud-integrated AI system that generates real-time, context-aware dialogue based on your specific playstyle.

## ✨ Key Features

* **🤖 Cloud-Integrated AI Taunt Engine:** The game analyzes your live metrics (flight altitude, flap frequency, and shield usage) and feeds them to an LLM (Groq/Llama 3 or Anthropic API) via background threads. The boss will dynamically mock your specific habits in real-time!
* **⚡ Asynchronous Multi-threading:** Network API calls are handled on secondary threads, ensuring the game maintains a buttery-smooth, locked 32 FPS without any network latency or frame drops.
* **📐 Dynamic Resolution Scaling:** A custom Virtual Surface Scaling Engine maps the internal 400x600 canvas to any physical monitor resolution or aspect ratio, preserving the retro look flawlessly on modern displays.
* **🚀 Engine Optimization & Physics:** Trigonometric calculations for hovering and rotations are pre-calculated using a bespoke `SinCache` module, reducing CPU load by up to 90%.
* **🎨 Advanced OOP Architecture:** Clean, modular code featuring a robust `ChippuAnimator` for complex sprite states, an optimized `ParticleSystem`, and per-pixel alpha transparency logic.
* **💾 Persistence:** High scores are automatically saved and loaded via local JSON storage.

## 🎮 Controls

Take control of Chippu using intuitive keyboard inputs:

| Action | Keybinding |
| :--- | :--- |
| **Fly / Flap** | `Spacebar`, `W`, or `Up Arrow` |
| **Move Left (Fly Back)** | `A` or `Left Arrow` |
| **Move Right (Fly Ahead)**| `D` or `Right Arrow` |
| **Quick Dash** | `Left Shift` or `Right Ctrl` |
| **Attack Boss** | `Left Shift` or `Right Ctrl` *(Only when the boss's core flashes green!)* |
| **Toggle Fullscreen** | `F11` |
| **Shop** | `B` |
| **Pause** | `Escape` |

## ⚙️ System Requirements

* **Operating System:** Windows 10+, macOS 12+, or Linux
* **Python Version:** Python 3.8 or higher
* **Dependencies:** `pygame`, `requests`
* **Internet Connection:** Required for the AI Taunt Engine to function dynamically (A local fallback is provided for offline play).
