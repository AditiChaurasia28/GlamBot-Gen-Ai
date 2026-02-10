import os
import cv2
import numpy as np
import math
import base64
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from groq import Groq
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__)
app.secret_key = "glambot_pink_edition"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Configuration
GROQ_MODEL = "llama-3.3-70b-versatile"
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analyze_skin(img):
    img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    mask = cv2.inRange(img_ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
    if cv2.countNonZero(mask) < (img.shape[0] * img.shape[1] * 0.01):
        return None, None
    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    l, a, b = cv2.split(img_lab)
    ita = math.atan2((cv2.mean(l, mask=mask)[0] - 50), cv2.mean(b, mask=mask)[0]) * (180 / math.pi)
    if ita > 55: tone = "Fair"
    elif ita > 28: tone = "Medium"
    elif ita > 10: tone = "Olive"
    else: tone = "Deep"
    avg_bgr = cv2.mean(img, mask=mask)[:3]
    return tone, (int(avg_bgr[2]), int(avg_bgr[1]), int(avg_bgr[0]))

# --- CSS: Pink Aesthetic Theme ---
STYLE = """
<style>
    :root { 
        --bg-pink: #fdf2f8; 
        --deep-pink: #be185d; 
        --white: #ffffff; 
        --navy: #1e293b; 
        --text-muted: #64748b; 
    }
    body { margin: 0; font-family: 'Inter', sans-serif; background: var(--bg-pink); color: var(--navy); }
    .nav { padding: 25px; text-align: center; background: var(--white); border-bottom: 2px solid #fbcfe8; font-weight: 900; letter-spacing: 5px; color: var(--deep-pink); }
    .container { max-width: 1100px; margin: auto; padding: 60px 20px; text-align: center; }
    .card { background: var(--white); padding: 40px; border-radius: 12px; border: 1px solid #fbcfe8; text-align: left; max-width: 600px; margin: auto; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); }
    .btn { background: var(--deep-pink); color: white; padding: 18px 35px; border: none; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; border-radius: 8px; transition: 0.3s; }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(190, 24, 93, 0.3); }
    h1 { font-size: 5rem; margin: 0; text-transform: uppercase; color: var(--deep-pink); letter-spacing: -3px; }
    input, select { width: 100%; padding: 12px; margin-top: 8px; border: 1px solid #f9a8d4; border-radius: 6px; box-sizing: border-box; }
    video { width: 100%; border-radius: 12px; border: 4px solid var(--white); background: #000; margin-top: 15px; }
    .product-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 40px; }
    .product-card { background: var(--white); padding: 25px; border-radius: 12px; border: 1px solid #fbcfe8; text-align: left; position: relative; }
    .store-tag { font-size: 0.7rem; font-weight: 800; color: var(--deep-pink); text-transform: uppercase; }
</style>
"""

@app.route('/')
def landing():
    return render_template_string(f"""
    <!DOCTYPE html><html><head>{STYLE}</head><body>
    <div class="container" style="height: 80vh; display: flex; flex-direction: column; justify-content: center;">
        <p style="color: var(--deep-pink); font-weight: bold; letter-spacing: 2px;">THE FUTURE OF STYLE</p>
        <h1>GLAMBOT</h1>
        <p style="color: var(--text-muted); font-size: 1.2rem; margin: 20px 0 40px;">Your personal AI wardrobe, now in a blush palette.</p>
        <div><a href="/upload-page" class="btn">GET STARTED</a></div>
    </div></body></html>""")

@app.route('/upload-page')
def upload_page():
    return render_template_string(f"""
    <!DOCTYPE html><html><head>{STYLE}</head><body>
    <div class="nav">GLAMBOT</div>
    <div class="container">
        <div class="card">
            <form action="/process" method="post" enctype="multipart/form-data">
                <label><b>GENDER</b></label>
                <select name="gender"><option value="Male">Male</option><option value="Female">Female</option></select>
                
                <label style="display:block; margin-top:15px;"><b>CLOTHING ITEM</b></label>
                <select name="product_type">
                    <option value="Shirt">Shirt</option><option value="Pant">Pant</option>
                    <option value="Kurta">Kurta</option><option value="Dress">Dress</option>
                </select>

                <label style="display:block; margin-top:15px;"><b>SIZE</b></label>
                <select name="size"><option>S</option><option>M</option><option>L</option><option>XL</option></select>

                <label style="display:block; margin-top:15px;"><b>COLOUR PREFERENCE</b></label>
                <input type="text" name="pref_color" placeholder="e.g. Navy Blue" required>

                <label style="display:block; margin-top:15px;"><b>IMAGE SOURCE</b></label>
                <input type="file" name="file">
                <button type="button" id="openCam" class="btn" style="width:100%; margin-top:10px; background:var(--navy);">USE CAMERA</button>
                
                <div id="camArea" style="display:none; margin-top:15px;">
                    <video id="video" autoplay></video>
                    <button type="button" id="snap" class="btn" style="width:100%; margin-top:10px;">SNAP PHOTO</button>
                </div>
                <input type="hidden" name="cam_data" id="cam_data">

                <button type="submit" class="btn" style="width:100%; margin-top:30px;">ANALYZE PROFILE</button>
            </form>
        </div>
    </div>
    <script>
        const video = document.getElementById('video');
        document.getElementById('openCam').onclick = async () => {{
            const stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
            video.srcObject = stream;
            document.getElementById('camArea').style.display = 'block';
        }};
        document.getElementById('snap').onclick = () => {{
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            document.getElementById('cam_data').value = canvas.toDataURL('image/jpeg');
            video.srcObject.getTracks().forEach(t => t.stop());
            document.getElementById('camArea').innerHTML = "<p style='color:green; font-weight:bold;'>✓ PHOTO READY</p>";
        }};
    </script>
    </body></html>""")

@app.route('/process', methods=['POST'])
def process():
    cam_image = request.form.get('cam_data')
    file = request.files.get('file')
    
    if cam_image and len(cam_image) > 10:
        data = base64.b64decode(cam_image.split(",")[1])
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif file:
        nparr = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else: return "No image provided."

    tone, rgb = analyze_skin(img)
    if not tone: return "Detection failed."

    session['data'] = {
        'tone': tone, 'rgb': rgb, 'gender': request.form.get('gender'),
        'product': request.form.get('product_type'), 'size': request.form.get('size'),
        'color': request.form.get('pref_color')
    }

    prompt = f"Stylist GlamBot. Suggest tips for {session['data']['color']} {session['data']['product']} for {tone} skin. Plain text, no bolding."
    res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role":"user","content":prompt}])
    session['data']['advice'] = res.choices[0].message.content.replace("**", "")
    return redirect(url_for('recommendation'))

@app.route('/recommendation')
def recommendation():
    d = session.get('data')
    return render_template_string(f"""
    <!DOCTYPE html><html><head>{STYLE}</head><body>
    <div class="nav">GLAMBOT</div>
    <div class="container">
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:50px; text-align:left;">
            <div>
                <p style="color:var(--deep-pink); font-weight:bold;">DETECTION RESULTS</p>
                <h1>{d['tone']}</h1>
                <div style="height:20px; width:150px; background:rgb{d['rgb']}; border-radius:10px;"></div>
            </div>
            <div class="card">
                <h3>THE GLAMBOT DIRECTIVE</h3>
                <p style="line-height:1.8;">{d['advice']}</p>
                <a href="/shop" class="btn" style="width:100%; text-align:center;">OPEN SHOPPING MALL →</a>
            </div>
        </div>
    </div></body></html>""")

@app.route('/shop')
def shop():
    d = session.get('data')
    query = f"{d['color']} {d['product']} {d['gender']}".replace(" ", "+")
    
    # Store Link Logic
    links = {
        "Amazon": f"https://www.amazon.in/s?k={query}",
        "Myntra": f"https://www.myntra.com/{query.replace('+', '-')}",
        "Zara": f"https://www.zara.com/in/en/search?searchTerm={query}"
    }

    products_html = ""
    for i in range(1, 11):
        store_name = list(links.keys())[i % 3]
        products_html += f"""
        <div class="product-card">
            <span class="store-tag">{store_name} Selection</span>
            <h4 style="margin:10px 0 5px 0;">{d['color']} {d['product']} - Variation {i}</h4>
            <p style="font-size:0.9rem; color:var(--text-muted); margin-bottom:15px;">Size: {d['size']} | High Quality Fabric</p>
            <a href="{links[store_name]}" target="_blank" class="btn" style="padding:10px 20px; font-size:0.8rem;">SHOP NOW</a>
        </div>"""

    return render_template_string(f"""
    <!DOCTYPE html><html><head>{STYLE}</head><body>
    <div class="nav">GLAMBOT MALL</div>
    <div class="container">
        <h2>CURATED {d['product'].upper()}S</h2>
        <p style="color:var(--text-muted); margin-bottom:40px;">10 matches found for {d['color']} items in size {d['size']}</p>
        <div class="product-grid">{products_html}</div>
    </div></body></html>""")

if __name__ == '__main__':
    app.run(debug=True)