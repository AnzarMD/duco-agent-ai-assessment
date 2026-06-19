"""
Generates a plain-language audio briefing using TTS.
Uses gTTS (Google Text-to-Speech) for Indian English accent.
"""

from gtts import gTTS
import anthropic
import os

client = anthropic.Anthropic()


def generate_audio_script(cob_results: dict) -> str:
    """Use Claude to write a simple, patient-friendly audio summary"""
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
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def generate_audio(script: str, output_path: str = "outputs/audio_briefing.mp3"):
    """Convert script text to speech and save as MP3"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tts = gTTS(text=script, lang="en", tld="co.in")  # Indian English accent
    tts.save(output_path)
    print(f"   Audio briefing saved to {output_path}")
