"""
Generates a plain-language audio briefing using TTS.
Uses Mistral AI for script generation and gTTS (Google Text-to-Speech) for Indian English voice.
"""

import os
from gtts import gTTS
from mistralai.client import Mistral

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))


def generate_audio_script(cob_results: dict) -> str:
    """Use Mistral AI to write a simple, patient-friendly audio summary"""
    aarav_oop = cob_results["aarav_surgery"].patient_oop
    priya_oop = cob_results["priya_pt"].patient_oop

    prompt = f"""
    Write a 150-word audio briefing for Aarav and Priya Sen explaining their insurance coordination results.
    Use simple, friendly language like you're talking to a family — avoid jargon.
    Key facts:
    - Aarav's ACL surgery costs 4,50,000. After both insurance plans coordinate, he only pays Rs {aarav_oop:,}.
    - Priya's physical therapy bill is 30,000. After coordination, she pays Rs {priya_oop:,}.
    - Plan B (Insurer2) is primary for Aarav; Plan A (Insurer1) is primary for Priya.
    - Pre-authorization letters have been generated for both insurers.
    - Start with "Hello Aarav and Priya," and end with next steps.
    """
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    return response.choices[0].message.content


def generate_audio(script: str, output_path: str = "outputs/audio_briefing.mp3"):
    """Convert script text to speech and save as MP3 using gTTS"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tts = gTTS(text=script, lang="en", tld="co.in")  # Indian English accent
    tts.save(output_path)
    print(f"   Audio briefing saved to {output_path}")
