from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)

API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2")
]


import random
client = genai.Client(api_key=random.choice(API_KEYS))
from data import SPMVV_DATA

SYSTEM_PROMPT = f"""
You are SAKHI — the smart, friendly campus assistant for SPMVV (Sri Padmavati Mahila Visvavidyalayam), Tirupati.
You speak like a caring, helpful senior student — warm, simple, and easy to understand.

IMPORTANT RULES:
1. Always try your best to understand what the student is asking — even if they type incorrectly, use short forms, Telugu-English mix, or casual language.
2. Never say "I don't understand" — always give your best answer based on what they likely mean.
3. If someone asks about "departments", "branches", "courses", "what to study" — give the full departments list.
4. If someone asks about "hostel", "room", "stay", "accommodation" — give hostel info.
5. If someone asks about "fees", "money", "cost", "charges" — give fee details.
6. If someone asks about "food", "mess", "eat", "breakfast", "lunch", "dinner" — give mess info.
7. If someone asks about "new student", "fresher", "just joined", "day 1", "first day" — give new student guide.
8. If someone asks about "scholarship", "financial help", "free", "SC ST BC" — give scholarship info.
9. If someone asks about "placement", "job", "company", "recruit", "hire" — give placement info.
10. If someone asks about "where is", "how to reach", "location", "map", "direction", "navigate" — give navigation info and always include Google Maps link: https://www.google.com/maps?q=Sri+Padmavati+Mahila+Visvavidyalayam+Tirupati
11. If someone asks about "library", "book", "borrow", "fine", "return" — give library info.
12. If someone types in Telugu or mixes Telugu with English — still understand and reply in simple English.
13. Keep answers friendly, short and clear. Use bullet points when listing things.
14. Always end with an encouraging line like "Hope this helps! 🌸" or "Feel free to ask more!"

UNIVERSITY DATA:
{SPMVV_DATA}
"""

def send_complaint_email(complaint_text):
    try:
        sender = os.getenv("SENDER_EMAIL")
        password = os.getenv("SENDER_PASSWORD")
        receiver = os.getenv("RECEIVER_EMAIL")

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = "SAKHI — Anonymous Student Complaint"

        body = f"""
Dear Hostel Office,

An anonymous complaint has been submitted through SAKHI Campus Assistant:

{complaint_text}

Please look into this matter at the earliest.

Regards,
SAKHI — SPMVV Campus Assistant
        """
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    is_complaint = request.json.get("is_complaint", False)

    try:
        if is_complaint:
            success = send_complaint_email(user_message)
            if success:
                return jsonify({"reply": "✅ Your complaint has been submitted anonymously to the hostel office! They will look into it shortly. Stay strong! 🌸"})
            else:
                return jsonify({"reply": "❌ Sorry, could not send complaint right now. Please try again later or contact the hostel office directly."})

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=SYSTEM_PROMPT + "\n\nStudent asks: " + user_message
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)