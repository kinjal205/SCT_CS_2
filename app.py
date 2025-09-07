from flask import Flask, request, send_file, abort, send_from_directory
from PIL import Image
import io, hashlib, random

app = Flask(__name__, static_folder=".", static_url_path="")

def key_bytes_from_string(key: str, length: int = 16) -> bytes:
    """Convert key string into fixed-length byte sequence"""
    h = hashlib.md5(key.encode('utf-8')).digest()
    if length <= len(h):
        return h[:length]
    out = bytearray(h)
    while len(out) < length:
        out.extend(hashlib.md5(out).digest())
    return bytes(out[:length])

def xor_image(img: Image.Image, key_str: str):
    """XOR each pixel value with derived key bytes"""
    kb = key_bytes_from_string(key_str, 256)
    pixels = img.load()
    w, h = img.size
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA')
        pixels = img.load()
    for y in range(h):
        for x in range(w):
            px = list(pixels[x, y])
            for i in range(len(px)):
                px[i] = px[i] ^ kb[(x + y + i) % len(kb)]
            pixels[x, y] = tuple(px)
    return img

def swap_image(img: Image.Image, key_str: str, reverse=False):
    """Shuffle or unshuffle pixels deterministically using key"""
    w, h = img.size
    pixels = list(img.getdata())
    n = len(pixels)
    rng = random.Random()
    seed = int.from_bytes(hashlib.sha256(key_str.encode('utf-8')).digest()[:8], 'big')
    rng.seed(seed)

    indices = list(range(n))
    rng.shuffle(indices)

    out = [None] * n
    if not reverse:
        # Encrypt: original[i] -> shuffled position
        for i, newpos in enumerate(indices):
            out[newpos] = pixels[i]
    else:
        # Decrypt: shuffled -> back to original
        for i, newpos in enumerate(indices):
            out[i] = pixels[newpos]

    new_img = Image.new(img.mode, img.size)
    new_img.putdata(out)
    return new_img

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    """Serve CSS, JS, etc."""
    return send_from_directory(".", filename)

@app.route("/process", methods=["POST"])
def process_image():
    if "image" not in request.files:
        return abort(400, "No image file")

    f = request.files["image"]
    key = request.form.get("key", "")
    operation = request.form.get("operation", "xor")
    mode = request.form.get("mode", "encrypt")

    try:
        img = Image.open(f.stream).convert("RGBA")
    except Exception:
        return abort(400, "Invalid image")

    try:
        if operation == "xor":
            img = xor_image(img, key)
        elif operation == "swap":
            reverse = (mode == "decrypt")
            img = swap_image(img, key, reverse=reverse)
        elif operation == "xor+swap":
            if mode == "encrypt":
                img = xor_image(img, key)
                img = swap_image(img, key, reverse=False)
            else:  # decrypt
                img = swap_image(img, key, reverse=True)
                img = xor_image(img, key)
        else:
            return abort(400, "Unknown operation")
    except Exception as e:
        return abort(500, "Processing error: " + str(e))

    out_io = io.BytesIO()
    img.save(out_io, format="PNG")
    out_io.seek(0)
    return send_file(out_io, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
