from fastapi import FastAPI
import requests
import openai
import os
import json
from datetime import datetime

# ----------------------------------
# Setup
# ----------------------------------

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

DATA_FILE = "data.json"


# ----------------------------------
# Get Comments from Internet
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
# AI Analysis
# ----------------------------------

def analyze(text):

    try:

        prompt = f"""
Analyze this in 2 sentences and classify sentiment
(enthusiastic, critical, objective):

{text}
"""

        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return res.choices[0].message.content

    except Exception as e:

        return "AI Error: " + str(e)


# ----------------------------------
# Save Data
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
# Fake Email Notification
# ----------------------------------

def send_email(email):

    print("Notification sent to:", email)

    return True


# ----------------------------------
# Main Pipeline API
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

            ai_result = analyze(text)

            record = {
                "original": text,
                "analysis": ai_result,
                "source": source,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            saved = save_data(record)

            results.append({
                "original": text,
                "analysis": ai_result,
                "sentiment": "auto",
                "stored": saved,
                "timestamp": record["timestamp"]
            })

        except Exception as e:

            errors.append(str(e))
            continue


    notify = send_email(email)


    return {
        "items": results,
        "notificationSent": notify,
        "processedAt": datetime.utcnow().isoformat() + "Z",
        "errors": errors
    }


# ----------------------------------
# Test Home
# ----------------------------------

@app.get("/")
def home():

    return {"message": "AI Pipeline is running"}
