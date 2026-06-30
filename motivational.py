"""
Generates motivational stories and job tips using Groq
when no new jobs are found during night hours.
"""
import os
import requests
import json
import random

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TOPICS = [
    "a poor farmer's son who cracked UPSC after 3 failed attempts",
    "a girl from a small village who became an IAS officer",
    "a person who left a private job to prepare for SSC and succeeded",
    "someone who studied while working a part-time job and cleared Railway exam",
    "a candidate who failed 5 times but never gave up and finally cleared the exam"
]


def generate_motivational_story():
    topic = random.choice(TOPICS)
    prompt = f"""Write a short, inspiring motivational story (150-200 words) in Hinglish about {topic}.
Make it relatable for Indian government job aspirants. End with an encouraging message.
Do not use real names — keep it general/inspirational.
Format as a Telegram post with emojis, ready to post directly."""

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 500
            },
            timeout=20
        )
        if resp.ok:
            text = resp.json()["choices"][0]["message"]["content"].strip()
            return text
    except Exception as e:
        print(f"Motivational story generation failed: {e}")

    return "🌟 Mehnat kabhi bekar nahi jaati. Aaj nahi toh kal, success zaroor milegi. Apna best do, baaki Allah/God pe chhod do! 💪\n\n#Motivation #SarkariNaukri #DeshNaukri"


def generate_job_stats():
    prompt = """Write a short interesting fact/statistic about Indian government job recruitment 
(SSC, UPSC, Railway, Banking) in Hinglish for a Telegram post. Make it engaging with emojis.
Keep it under 100 words. Format ready to post directly."""

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 300
            },
            timeout=20
        )
        if resp.ok:
            text = resp.json()["choices"][0]["message"]["content"].strip()
            return text
    except Exception as e:
        print(f"Job stats generation failed: {e}")

    return "📊 Did you know? Har saal lakhon students SSC CGL ke liye apply karte hain, lekin sirf top performers select hote hain. Consistency hi key hai! 🔑\n\n#SarkariNaukri #DeshNaukri"
