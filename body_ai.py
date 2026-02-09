import cv2
import mediapipe as mp
import numpy as np
from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True)

def extract_body_landmarks(image_path):
    img = cv2.imread(image_path)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    if not result.pose_landmarks:
        return None

    landmarks = result.pose_landmarks.landmark
    return landmarks, img.shape



def estimate_body_measurements(image_path):
    data = extract_body_landmarks(image_path)
    if not data:
        return None

    landmarks, shape = data
    h, w, _ = shape

    def dist(a, b):
        return abs(a.x - b.x) * w

    shoulders = dist(landmarks[11], landmarks[12])
    waist = dist(landmarks[23], landmarks[24]) * 0.9
    hips = dist(landmarks[23], landmarks[24])
    height_ratio = landmarks[0].y - landmarks[27].y

    return {
        "shoulders": round(shoulders, 2),
        "waist": round(waist, 2),
        "hips": round(hips, 2),
        "height_ratio": round(abs(height_ratio), 2)
    }

def detect_body_type(measurements):
    s = measurements["shoulders"]
    w = measurements["waist"]
    h = measurements["hips"]

    if s > h and w < s:
        base_type = "Inverted Triangle"
    elif h > s and w < h:
        base_type = "Pear"
    elif abs(s - h) < 15 and abs(w - s) < 15:
        base_type = "Rectangle"
    elif w > s and w > h:
        base_type = "Apple"
    else:
        base_type = "Hourglass"

    # Gen-AI refinement
    prompt = f"""
    Based on these body measurements:
    Shoulders: {s}
    Waist: {w}
    Hips: {h}

    Determine the most accurate body type:
    Hourglass, Pear, Apple, Rectangle, Inverted Triangle.

    Respond with only one type.
    """

    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20
    )

    ai_type = chat.choices[0].message.content.strip()

    return ai_type if ai_type else base_type
