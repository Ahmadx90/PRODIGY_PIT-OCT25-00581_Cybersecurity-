# __define-ocg__: Flask Image Encryption Tool (XOR + Pixel Shuffle)
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from PIL import Image
import os, uuid, random

app = Flask(__name__)
UPLOAD = "uploads"
os.makedirs(UPLOAD, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD

def process_image(image_path, key, mode):
    """
    Encrypt: XOR each pixel by key, then shuffle pixels using RNG(key).
    Decrypt: Reverse the shuffle and XOR using the same RNG(key).
    """
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    n = width * height

    # read pixels in row-major order
    pixels = list(img.getdata())  # [(r,g,b), ...] length n

    # create deterministic shuffled index array
    indices = list(range(n))
    rng = random.Random(key)
    shuffled = indices.copy()
    rng.shuffle(shuffled)

    if mode == "encrypt":
        # XOR each pixel with key then place into shuffled positions
        xor_pixels = [ (r ^ key, g ^ key, b ^ key) for (r,g,b) in pixels ]
        new_pixels = [None] * n
        for i in range(n):
            dest = shuffled[i]       # where this pixel will go
            new_pixels[dest] = xor_pixels[i]
    else:  # decrypt
        # encrypted pixels are in 'pixels' with shuffled positions and XOR applied.
        # To reconstruct original: original[i] = XOR( encrypted[ shuffled[i] ] )
        new_pixels = [None] * n
        for i in range(n):
            src = shuffled[i]       # where encrypted holds the XORed original[i]
            r,g,b = pixels[src]
            new_pixels[i] = (r ^ key, g ^ key, b ^ key)

    # write back to image and save
    out = Image.new("RGB", (width, height))
    out.putdata(new_pixels)
    out_filename = f"{mode}_{uuid.uuid4().hex}.png"
    out_path = os.path.join(app.config["UPLOAD_FOLDER"], out_filename)
    out.save(out_path)
    return out_filename

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # validate upload & key & action
        file = request.files.get("image")
        key = request.form.get("key", "").strip()
        action = request.form.get("action")

        if not file or file.filename == "":
            return render_template("index.html", error="Please upload an image.")
        if not key:
            return render_template("index.html", error="Please enter a numeric key.")
        # numeric key required for RNG and xor — limit key to 0..255 for XOR sensibility
        try:
            key_int = int(key)
        except:
            return render_template("index.html", error="Key must be a number.")
        # normalize key into byte range for XOR, but keep integer for RNG
        key_byte = key_int & 0xFF

        # save original file
        orig_name = f"orig_{uuid.uuid4().hex}_{file.filename}"
        orig_path = os.path.join(app.config["UPLOAD_FOLDER"], orig_name)
        file.save(orig_path)

        # process and produce output file
        processed_name = process_image(orig_path, key_int, action)
        message = f"Image {action}ed successfully."

        return render_template("index.html",
                               message=message,
                               original_image=orig_name,
                               processed_image=processed_name,
                               key_masked=True)
    # GET
    return render_template("index.html")

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True)
