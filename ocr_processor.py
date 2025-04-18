import os
import pytesseract
from PIL import Image
import requests
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MathOCR:
    def __init__(self):
        # For Mathpix OCR (better for math equations)
        self.mathpix_app_id = os.getenv("MATHPIX_APP_ID")
        self.mathpix_app_key = os.getenv("MATHPIX_APP_KEY")
        
    def process_image(self, image_path):
        """Process math problem image using OCR"""
        # Try using Mathpix first (specialized for math notation)
        if self.mathpix_app_id and self.mathpix_app_key:
            try:
                return self._process_with_mathpix(image_path)
            except Exception as e:
                print(f"Mathpix OCR failed: {e}. Falling back to Tesseract.")
        
        # Fallback to Tesseract OCR
        return self._process_with_tesseract(image_path)
    
    def _process_with_tesseract(self, image_path):
        """Process image with Tesseract OCR"""
        image = Image.open(image_path)
        # Preprocess image for better OCR results
        # (you may need to adjust preprocessing based on your needs)
        text = pytesseract.image_to_string(image)
        return text
    
    def _process_with_mathpix(self, image_path):
        """Process image with Mathpix OCR (better for math)"""
        image_uri = self._encode_image(image_path)
        r = requests.post(
            "https://api.mathpix.com/v3/text",
            headers={
                "app_id": self.mathpix_app_id,
                "app_key": self.mathpix_app_key,
                "Content-type": "application/json"
            },
            data=json.dumps({
                "src": image_uri,
                "formats": ["text", "latex"],
                "data_options": {
                    "include_asciimath": True,
                    "include_latex": True
                }
            })
        )
        response = r.json()
        
        # Return both plain text and LaTeX format
        return {
            "text": response.get("text", ""),
            "latex": response.get("latex", "")
        }
    
    def _encode_image(self, image_path):
        """Encode image to base64 for API use"""
        with open(image_path, "rb") as image_file:
            return "data:image/jpeg;base64," + base64.b64encode(image_file.read()).decode()