import os
import json
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv()
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")


def load_dataset(path):
  """
  Load the dataset from a JSON file.
  Expected format: list of dicts, each having at least 'title', 'text', 'concepts', and optional 'image_prompt'.
  """
  with open(path, 'r') as f:
    return json.load(f)


def filter_docs(docs, clicked_nodes):
  """
  Filter documents whose 'concepts' field intersects with clicked_nodes.
  """
  lowered_clicked = [c.lower() for c in clicked_nodes]
  return [
    doc for doc in docs
    if any(concept.lower() in lowered_clicked for concept in doc.get("concepts", []))
  ]


def build_context(clicked_nodes, docs):
  """
  Build a text context summary given clicked nodes and related docs.
  """
  context = f"Key concepts: {', '.join(clicked_nodes)}.\n\nRelated information:\n"
  for doc in docs:
    title = doc.get("title", "")
    snippet = doc.get("text", "").replace("\n", " ")[:200]
    context += f"- {title}: {snippet}...\n"
  return context


def call_ollama(model, prompt, temperature=0.9, max_tokens=512):
  """
  Call local Ollama server with the given model and prompt.
  """
  payload = {
  "model": model,
  "prompt": prompt,
  "temperature": temperature,
  "max_tokens": max_tokens
  }
  resp = requests.post(f"{OLLAMA_API_URL}/api/generate", json=payload)
  resp.raise_for_status()
  return resp.json().get("text", "")


def generate_conspiracy(context, model="llama2"):
  """
  Generate a conspiracy narrative based on the context.
  """
  prompt = (
    "You are a conspiracy theorist. Generate a dramatic, fake conspiracy theory "
    "that ties together the following concepts and information:\n\n"
    f"{context}\n\nConspiracy theory:"
  )
  return call_ollama(model, prompt)


def generate_headlines(context, model="llama2"):
  """
  Generate three fake news headlines supporting the conspiracy.
  """
  prompt = (
    "Generate three short, sensational fake news headlines that support the conspiracy "
    "implied by the context below:\n\n"
    f"{context}\n\nHeadlines:"
  )
  return call_ollama(model, prompt, temperature=0.8, max_tokens=128)


# Image generation: Stable Diffusion via diffusers
from diffusers import StableDiffusionPipeline
import torch

def generate_images(image_prompts, output_dir="images", model_id="CompVis/stable-diffusion-v1-4"):
  """
  Generate images for each prompt using Stable Diffusion (diffusers).
  Returns list of file paths.
  """
  pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
  pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

  os.makedirs(output_dir, exist_ok=True)
  image_paths = []
  for i, prompt in enumerate(image_prompts):
    image = pipe(prompt).images[0]
    path = os.path.join(output_dir, f"image_{i}.png")
    image.save(path)
    image_paths.append(path)
  return image_paths


# Example usage block
if __name__ == "__main__":
  dataset = load_dataset("dataset.json")
  clicked = ["deep state", "elon musk", "5G"]
  docs = filter_docs(dataset, clicked)
  context = build_context(clicked, docs)
  story = generate_conspiracy(context)
  headlines = generate_headlines(context)
  image_prompts = [doc.get("image_prompt") for doc in docs if doc.get("image_prompt")]
  images = generate_images(image_prompts[:3])
  print("Story:\n", story)
  print("\nHeadlines:\n", headlines)
  print("\nSaved images:", images)