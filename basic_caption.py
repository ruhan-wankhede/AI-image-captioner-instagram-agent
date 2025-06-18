from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

# Load model & processor
model_id = "Salesforce/blip-image-captioning-large"
processor = BlipProcessor.from_pretrained(model_id)
model = BlipForConditionalGeneration.from_pretrained(model_id)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def generate_caption(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)

    output_ids = model.generate(**inputs, max_length=64, num_beams=3)
    caption = processor.decode(output_ids[0], skip_special_tokens=True)
    return caption.strip()

