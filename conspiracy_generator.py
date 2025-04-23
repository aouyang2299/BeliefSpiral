"""
conspiracy_generator.py

This module provides functions to generate a concise, persuasive conspiracy theory summary
based on user-clicked concepts using a LLaMA model, and to create a single themed "fake evidence"
image (no text) that visually encapsulates the conspiracy.

Expected JSON schema per document:
- title: str
- summary OR concept: str    # textual description
- concepts_spacy: List[str]  # spaCy-extracted concepts for filtering

Requirements:
- Python 3.8+
- requests
- Ollama CLI with LLaMA model pulled:
      ollama pull llama2
  then run:
      ollama serve
  serving at http://localhost:11434/api/generate
- diffusers, transformers, torch for Stable Diffusion image generation

Usage:
    from conspiracy_generator import (
        load_dataset, filter_docs, build_context,
        generate_conspiracy, generate_evidence_image
    )

    dataset = load_dataset("dataset.json")
    clicked = ["deep state", "elon musk", "5G"]
    docs = filter_docs(dataset, clicked)
    context = build_context(clicked, docs)
    summary = generate_conspiracy(context)
    image_path = generate_evidence_image(summary)
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import json
import requests
from typing import List
import torch
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler

# Ollama serve endpoint (default)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")


def load_dataset(path: str) -> List[dict]:
    """Load the dataset from a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_docs(docs: List[dict], clicked_nodes: List[str]) -> List[dict]:
    """Filter docs whose 'concepts_spacy' intersects with clicked_nodes."""
    lowered = {c.lower() for c in clicked_nodes}
    return [doc for doc in docs if any(c.lower() in lowered for c in doc.get('concepts_spacy', []))]


def build_context(clicked_nodes: List[str], docs: List[dict]) -> str:
    """Build text context summary for the model."""
    lines = [f"Key concepts: {', '.join(clicked_nodes)}.", "", "Related information:"]
    for doc in docs:
        title = doc.get('title', '')
        text = doc.get('summary') or doc.get('concept', '')
        snippet = text.replace('\n', ' ')[:200]
        lines.append(f"- {title}: {snippet}...")
    return '\n'.join(lines)


def call_ollama(model: str, prompt: str, temperature: float=0.8, max_tokens: int=250) -> str:
    """Invoke local Ollama and return full generated text."""
    payload = {"model": model, "prompt": prompt, "temperature": temperature, "max_tokens": max_tokens}
    resp = requests.post(OLLAMA_API_URL, json=payload)
    resp.raise_for_status()
    parts = []
    for line in resp.text.splitlines():
        try:
            data = json.loads(line)
            if 'response' in data:
                parts.append(data['response'])
            if data.get('done'):
                break
        except json.JSONDecodeError:
            continue
    return ''.join(parts).strip()


def generate_conspiracy(context: str) -> str:
    """
    Generate a concise 3-4 sentence persuasive summary with no headers.
    Use definitive language and avoid qualifiers like 'if true'.
    """
    prompt = (
        "You are a world-renowned investigative journalist known for uncovering shocking truths."
        " After reading the context below, craft an attention-grabbing headline followed by a juicy, persuasive summary."
        " The headline should be sensational but believable, using words like 'Revealed', 'Shocking', 'Exposed', or 'Undeniable Proof'."
        " The summary should be 3-4 sentences, dramatic, confident, and designed to captivate readers."
        " Use powerful language, imply urgency, and avoid any qualifiers like 'might' or 'allegedly'."
        f"\n\nContext:\n{context}\n\nHeadline and Summary:"
    )
    return call_ollama('llama2', prompt)


# Setup Stable Diffusion pipeline with optimizations
_SD_PIPE = None

def _get_sd_pipe(model_id: str="runwayml/stable-diffusion-v1-5"):
    global _SD_PIPE
    if _SD_PIPE is None:
        device = 'cpu' #'cuda' if torch.cuda.is_available() else 'cpu'
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            safety_checker=None
        )
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        _SD_PIPE = pipe.to(device)
    return _SD_PIPE

def detect_theme(clicked_nodes: list, summary: str) -> str:
    # Seed keywords per category
    THEMES = {
        'political': ['government', 'election', 'mayor', 'law', 'congress', 'senate', 'campaign', 'justice', 'president'],
        'scientific': ['lab', 'experiment', 'research', 'scientist', 'virus', '5g', 'climate', 'dna', 'biology', 'physics'],
        'tech': ['data', 'server', 'ai', 'algorithm', 'cctv', 'surveillance', 'hack', 'blockchain', 'software', 'chip'],
        'space': ['ufo', 'nasa', 'satellite', 'space', 'alien', 'cosmos', 'orbit', 'astronaut', 'extraterrestrial']
    }

    text_blob = ' '.join(clicked_nodes).lower() + ' ' + summary.lower()

    for theme, keywords in THEMES.items():
        for word in keywords:
            if word in text_blob:
                return theme
    return 'generic'

def build_visual_prompt(theme: str, summary_short: str) -> str:
    PROMPTS = {
        'political': f"Leaked confidential government file, hidden seals, courtroom sketch style, {summary_short}, no text",
        'scientific': f"Fake laboratory photo, mysterious device, forged research diagram, {summary_short}, no text",
        'tech': f"Blurry CCTV screenshot, hacked data servers, digital breach aesthetics, {summary_short}, no text",
        'space': f"Classified satellite image, unidentified object, space agency confidential photo, {summary_short}, no text",
        'generic': f"Mysterious photographic evidence linked to conspiracy, dark atmosphere, {summary_short}, no text"
    }
    return PROMPTS.get(theme, PROMPTS['generic'])

def generate_evidence_image(summary: str, output_dir: str="images", steps: int=20, scale: float=8.0) -> str:
    """
    Generate a single "fake evidence" image (no words) representing the conspiracy.
    Uses a very short prompt to avoid CLIP token limits and a single call to reduce multiprocessing overhead.
    """
    # Truncate summary to 15 words for brevity
    words = summary.split()
    summary_short = " ".join(words[:20]) + ("..." if len(words) > 20 else "")

    theme = detect_theme(clicked, summary)
    prompt = build_visual_prompt(theme, summary_short)

    pipe = _get_sd_pipe()
    os.makedirs(output_dir, exist_ok=True)
    with torch.inference_mode():
        image = pipe(prompt, num_inference_steps=steps, guidance_scale=scale).images[0]
    path = os.path.join(output_dir, "evidence2.png")
    image.save(path)
    return path

# from PIL import Image, ImageDraw, ImageFont

# def add_fake_evidence_overlay(image_path: str) -> str:
#     img = Image.open(image_path).convert("RGBA")
#     draw = ImageDraw.Draw(img)

#     # Example: Add black "redacted" bars
#     width, height = img.size
#     bar_height = height // 20
#     for i in range(3):  # Add 3 bars
#         y = (i + 2) * bar_height
#         draw.rectangle([20, y, width - 20, y + bar_height], fill="black")

#     # Example: Add "CONFIDENTIAL" stamp
#     try:
#         font = ImageFont.truetype("arial.ttf", size=bar_height)
#     except:
#         font = ImageFont.load_default()
#     draw.text((width // 4, height // 10), "CONFIDENTIAL", fill=(255,0,0,128), font=font)

#     # Save new image
#     output_path = image_path.replace(".png", "_overlay.png")
#     img.save(output_path)
#     return output_path

if __name__ == "__main__":
    dataset = load_dataset("raw_data/final_data/all_spacy_concepts_final.json")
    clicked = ["Mr. Trump", "the nation’s post-Watergate campaign finance laws", "Eric Adams case"]
    docs = filter_docs(dataset, clicked)
    context = build_context(clicked, docs)
    summary = generate_conspiracy(context)
    print("Summary:\n", summary)
    image_path = generate_evidence_image(summary)
    print("Generated evidence image at", image_path)
