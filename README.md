# 📸 AI Image Captioner with Instagram Uploader

This project is an **AI-powered image captioning pipeline** that:

1. Generates captions from images using **BLIP (Bootstrapped Language Image Pretraining)**.
2. Lets users **refine or regenerate captions** via **LangGraph + GPT-4**.
3. Automates image **upload to Instagram** using **Selenium**.

---

## ✨ Features

* 🔍 **BLIP-based captioning** for high-quality initial descriptions.
* 🧠 **GPT-4 refinement loop** with human-in-the-loop (via CLI).
* ♻️ Regenerate or edit captions interactively.
* 📤 **Selenium-powered Instagram upload**.
* 💬 Emoji support and user feedback integration.

---

## 💠 Tech Stack

| Component                                                 | Description                                      |
| --------------------------------------------------------- | ------------------------------------------------ |
| 🧠 [BLIP](https://github.com/salesforce/BLIP)             | Vision-language model for caption generation     |
| 🗮 [LangGraph](https://github.com/langchain-ai/langgraph) | Flow orchestration and refinement loop           |
| 🤖 GPT-4                                                  | Caption refinement and user input interpretation |
| 🔸 Selenium                                               | Web automation for Instagram posting             |

---

## 🖼️ How It Works

1. **Input Image → BLIP** generates an initial caption.
2. **LangGraph + GPT-4** proposes 5 alternative captions.
3. You choose to:

   * Upload one directly.
   * Edit a caption manually.
   * Regenerate captions based on custom feedback.
4. The selected caption + image is uploaded to your **Instagram** account using **Selenium automation**.

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/ai-image-captioner
cd ai-image-captioner
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> Ensure you also have:

* Chrome installed
* ChromeDriver compatible with your Chrome version
* `.env` file with any required keys for GPT-4 (Mistral here)

### 3. Run the app

```bash
python main.py
```

You’ll be prompted for your Instagram login credentials and shown caption options.

---

## 🔐 Security Note

* Instagram credentials are entered via the terminal and **not stored**.
* Use a burner/test account for development if needed.

---

## 🖼️ Example Output

```
BLIP caption: A dog playing in the snow.

GPT-4 suggestions:
[0] Pure snowy joy 🐶❄️
[1] Winter zoomies activated!
[2] Snow much fun with my pup!
[3] Frosty adventures begin 🐾
[4] Tail wags and snow drags.

💬 Your response: 2
✅ Uploaded "Snow much fun with my pup!" to Instagram.
```

---

## 📚 Future Improvements

* Add a GUI or web frontend
* Support Instagram Reels
* Add hashtags based on image content
* Store past captions and analytics

---

## 🧠 Credits

* [Salesforce BLIP](https://github.com/salesforce/BLIP)
* [LangGraph](https://github.com/langchain-ai/langgraph)
* [OpenAI GPT-4](https://platform.openai.com/)
* [Selenium](https://www.selenium.dev/)

---
