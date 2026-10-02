from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import httpx
from groq import Groq

load_dotenv()

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
    """Send complaint via Brevo HTTPS API (SMTP is blocked on Render free tier).
    Returns (success: bool, reason: str)."""
    api_key = os.getenv("BREVO_API_KEY")
    sender = os.getenv("SENDER_EMAIL")
    receiver = os.getenv("COMPLAINT_TO_EMAIL") or os.getenv("RECEIVER_EMAIL")

    missing = [n for n, v in [("BREVO_API_KEY", api_key),
                              ("SENDER_EMAIL", sender),
                              ("COMPLAINT_TO_EMAIL", receiver)] if not v]
    if missing:
        return False, "missing variables: " + ", ".join(missing)

    body = f"""Dear Hostel Office,

An anonymous complaint has been submitted through SAKHI Campus Assistant:

{complaint_text}

Please look into this matter at the earliest.

Regards,
SAKHI — SPMVV Campus Assistant
"""
    try:
        r = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
            json={
                "sender": {"name": "SAKHI", "email": sender},
                "to": [{"email": receiver}],
                "subject": "SAKHI — Anonymous Student Complaint",
                "textContent": body,
            },
            timeout=10,
        )
        if r.status_code in (200, 201):
            return True, ""
        return False, f"Brevo {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    is_complaint = request.json.get("is_complaint", False)

    try:
        if is_complaint:
            success, reason = send_complaint_email(user_message)
            if success:
                return jsonify({"reply": "✅ Your complaint has been submitted anonymously to the hostel office! They will look into it shortly. Stay strong! 🌸"})
            else:
                print("Complaint failed:", reason, flush=True)
                # DEBUG: reason shown in chat. Remove "(Reason: ...)" once it works.
                return jsonify({"reply": f"❌ Sorry, could not send complaint right now. (Reason: {reason})"})

        response = client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)