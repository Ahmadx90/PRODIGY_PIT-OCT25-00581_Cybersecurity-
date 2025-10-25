from flask import Flask, render_template, request

app = Flask(__name__)

# Caesar Cipher functions
def encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char
    return result

def decrypt(text, shift):
    return encrypt(text, -shift)

@app.route("/", methods=["GET", "POST"])
def index():
    result_text = ""
    message = ""
    shift = 3
    action = ""
    result_title = "Output (Encrypted)"

    if request.method == "POST":
        message = request.form.get("message")
        shift = int(request.form.get("shift", 3))
        action = request.form.get("action")

        if action == "encrypt":
            result_text = encrypt(message, shift)
            result_title = "Output (Encrypted)"
        elif action == "decrypt":
            result_text = decrypt(message, shift)
            result_title = "Output (Decrypted)"

    return render_template("index.html", result=result_text, message=message, shift=shift, result_title=result_title)

if __name__ == "__main__":
    app.run(debug=True)