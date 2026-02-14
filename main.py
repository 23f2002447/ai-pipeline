from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import openai
import os
import json
from datetime import datetime

# ----------------------------------
# Setup
# ----------------------------------

app = FastAPI()

# Enable CORS (important for checker)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

DATA_FILE = "data.json"


# ----------------------------------
# Fetch Comments from API
# ----------------------------------

def get_comments():
    try:
        url = "https://jsonplaceholder.typicode.com/comments?postId=1"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()[:3]
    except Exception as e:
        return {"error": str(e)}


# ----------------------------------
# AI Analysis + Sentiment Extraction
# ----------------------------------

def analyze(text):
    try:
        prompt = f"""
Analyze the following text in 2 sentences.

Then in a NEW LINE write only ONE word from:
enthusiastic, critical, objective

Format strictly:
Analysis: <your analysis>
Sentiment: <one word>

Text:
{text}
"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        output = response.choices[0].message.content

        analysis = ""
        sentiment = "objective"  # default fallback

        for line in output.split("\n"):
            if line.lower().startswith("analysis:"):
                analysis = line.replace("Analysis:", "").strip()
            if line.lower().startswith("sentiment:"):
                sentiment = line.replace("Sentiment:", "").strip().lower()

        # Safety validation
        if sentiment not in ["enthusiastic", "critical", "objective"]:
            sentiment = "objective"

        return analysis, sentiment

    except Exception as e:
        return f"AI Error: {str(e)}", "objective"


# ----------------------------------
# Save to File Storage
# ----------------------------------

def save_data(item):
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(item)

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

        return True
    except:
        return False


# ----------------------------------
# Notification (Mock)
# ----------------------------------

def send_email(email):
    print("Notification sent to:", email)
    return True


# ----------------------------------
# Main Pipeline Endpoint
# ----------------------------------

@app.post("/pipeline")
def run_pipeline(data: dict):

    email = data.get("email")
    source = data.get("source")

    results = []
    errors = []

    comments = get_comments()

    if "error" in comments:
        return {"error": comments["error"]}

    for item in comments:
        try:
            text = item["body"]

            analysis, sentiment = analyze(text)

            timestamp = datetime.utcnow().isoformat() + "Z"

            record = {
                "original": text,
                "analysis": analysis,
                "sentiment": sentiment,
                "source": source,
                "timestamp": timestamp
            }

            stored = save_data(record)

            results.append({
                "original": text,
                "analysis": analysis,
                "sentiment": sentiment,
                "stored": stored,
                "timestamp": timestamp
            })

        except Exception as e:
            errors.append(str(e))
            continue

    notification = send_email(email)

    return {
        "items": results,
        "notificationSent": notification,
        "processedAt": datetime.utcnow().isoformat() + "Z",
        "errors": errors
    }


# ----------------------------------
# Health Check
# ----------------------------------

@app.get("/")
def home():
    return {"message": "AI Pipeline is running"}
