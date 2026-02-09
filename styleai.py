from flask import Flask, request
from dotenv import load_dotenv
from groq import Groq
from PIL import Image
import numpy as np
import os

load_dotenv()
app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>StyleAI</title>
<style>
body {{ font-family: Arial; background:#111827; color:white; margin:0 }}
.container {{ max-width:900px; margin:auto; padding:30px }}
.card {{ background:#1f2933; padding:20px; border-radius:15px; margin-bottom:20px }}
input,select,button {{ width:100%; padding:10px; margin-top:10px; border-radius:8px; border:none }}
button {{ background:#6366f1; color:white; font-size:16px; cursor:pointer }}
button:hover {{ background:#4f46e5 }}
a {{ color:#93c5fd; text-decoration:none }}
.tag {{ background:#374151; padding:5px 10px; border-radius:20px; margin-right:5px }}
</style>
</head>
<body>
<div class="container">
<div class="card">
<h2>StyleAI – AI Fashion Advisor</h2>
<form method="POST" enctype="multipart/form-data">
<input type="file" name="photo" required>
<select name="gender">
<option value="male">Male</option>
<option value="female">Female</option>
</select>
<input type="text" name="shirt" placeholder="What shirt are you wearing? (black, blue...)">
<button type="submit">Analyze</button>
</form>
</div>
{output}
</div>
</body>
</html>
"""

def detect_skin(img):
    arr = np.array(img)
    avg = arr.mean(axis=(0,1))
    if avg[0] > 200:
        return "Fair"
    elif avg[0] > 150:
        return "Medium"
    elif avg[0] > 100:
        return "Olive"
    else:
        return "Deep"

def get_products(skin, gender):
    skin = skin.capitalize()
    gender = gender.lower()

    data = {
        "male": {
            "Fair": [("White Shirt","https://www.myntra.com/shirts"),
                     ("Navy Blazer","https://www.amazon.in/s?k=navy+blazer+men")],
            "Medium": [("Olive T-shirt","https://www.amazon.in/s?k=olive+tshirt+men"),
                       ("Denim Jacket","https://www.myntra.com/jackets")],
            "Olive": [("Beige Kurta","https://www.amazon.in/s?k=beige+kurta"),
                      ("Black Jeans","https://www.myntra.com/jeans")],
            "Deep": [("Mustard Shirt","https://www.amazon.in/s?k=mustard+shirt"),
                     ("Charcoal Pants","https://www.myntra.com/trousers")]
        },
        "female": {
            "Fair": [("Pastel Dress","https://www.myntra.com/dresses"),
                     ("Silver Earrings","https://www.amazon.in/s?k=silver+earrings")],
            "Medium": [("Coral Top","https://www.amazon.in/s?k=coral+top"),
                       ("Blue Jeans","https://www.myntra.com/jeans")],
            "Olive": [("Emerald Saree","https://www.amazon.in/s?k=emerald+saree"),
                      ("Gold Bangles","https://www.myntra.com/jewellery")],
            "Deep": [("Yellow Anarkali","https://www.amazon.in/s?k=yellow+anarkali"),
                     ("Statement Necklace","https://www.myntra.com/necklace")]
        }
    }

    # Fallback if something unexpected happens
    return data.get(gender, data["male"]).get(skin, data["male"]["Medium"])


@app.route("/", methods=["GET","POST"])
def index():
    output = ""
    if request.method == "POST":
        file = request.files["photo"]
        gender = request.form["gender"]
        shirt = request.form["shirt"]

        img = Image.open(file)
        skin = detect_skin(img)

        prompt = f"""
        Give fashion recommendations for a {gender} with {skin} skin tone.
        """

        if shirt:
            prompt += f"""
            Also suggest best pant colors if I am wearing a {shirt} shirt.
            """

        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            max_tokens=300
        )

        text = chat.choices[0].message.content
        products = get_products(skin, gender)

        links = ""
        for name, link in products:
            links += f"<li><a href='{link}' target='_blank'>{name}</a></li>"

        output = f"""
        <div class="card">
            <h3>Your Profile</h3>
            <span class="tag">Skin: {skin}</span>
            <span class="tag">Gender: {gender}</span>
        </div>

        <div class="card">
            <h3>AI Style Advice</h3>
            <p>{text}</p>
        </div>

        <div class="card">
            <h3>Recommended Shopping</h3>
            <ul class="products">{links}</ul>
        </div>
        """

    return HTML.format(output=output)

if __name__ == "__main__":
    app.run(debug=True)
