from flask import Flask, render_template, request
import cv2
import numpy as np
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# -------- Skin Tone Detection --------
def detect_skin_tone(image_path):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    avg_color = np.mean(img, axis=(0, 1))

    if avg_color[0] > 180:
        return "Fair"
    elif avg_color[0] > 130:
        return "Medium"
    else:
        return "Dark"

# -------- Groq API Call --------
def get_styling_recommendation(skin_tone):
    prompt = f"Give fashion and skincare tips for {skin_tone} skin tone"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data
    )

    return response.json()["choices"][0]["message"]["content"]

# -------- Routes --------
@app.route("/", methods=["GET", "POST"])
def index():
    recommendation = ""
    skin_tone = ""

    if request.method == "POST":
        file = request.files["image"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        skin_tone = detect_skin_tone(path)
        recommendation = get_styling_recommendation(skin_tone)

    return render_template("index.html",
                           skin_tone=skin_tone,
                           recommendation=recommendation)

if __name__ == "__main__":
    app.run(debug=True)
