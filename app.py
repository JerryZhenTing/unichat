import os
import json
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import traceback

# Import our custom modules
from ocr_processor import MathOCR
from ai_models import AIModelInterface
from answer_verifier import AnswerVerifier
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create directories for uploads and history if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('history', exist_ok=True)

# Initialize our components
ocr = MathOCR()
ai_interface = AIModelInterface()
verifier = AnswerVerifier()

def get_available_models():
    """Check which AI models are available based on API keys"""
    available_models = []
    
    if os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY").startswith("your_"):
        available_models.append("chatgpt")
        
    if os.getenv("ANTHROPIC_API_KEY") and not os.getenv("ANTHROPIC_API_KEY").startswith("your_"):
        available_models.append("claude")
        
    if os.getenv("DEEPSEEK_API_KEY") and not os.getenv("DEEPSEEK_API_KEY").startswith("your_"):
        available_models.append("deepseek")
        
    return available_models

def preprocess_text(text):
    """Preprocess problem text to handle special characters"""
    if not text:
        return ""
    
    # Replace any problematic characters
    text = text.replace('\n', ' ')
    # Keep mathematical symbols intact but clean up spacing
    text = ' '.join(text.split())
    
    return text

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/submit', methods=['POST'])
def submit_problem():
    """Handle problem submission"""
    try:
        # Debug output to see what's in the request
        print("Form data keys:", list(request.form.keys()))
        print("Files keys:", list(request.files.keys()))
        
        # Get available models
        available_models = get_available_models()
        
        if not available_models:
            return jsonify({"error": "No AI models available. Please configure at least one API key in the .env file."}), 400
        
        # Get problem text with better handling
        problem_text = ""
        
        # Check if text input is provided and non-empty
        if 'problem_text' in request.form and request.form['problem_text'].strip():
            problem_text = request.form['problem_text'].strip()
            print(f"Using text input: {problem_text}")
        # Check if image upload is provided and has a filename
        elif 'problem_image' in request.files and request.files['problem_image'].filename:
            # Process image upload
            file = request.files['problem_image']
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the image with OCR
            ocr_result = ocr.process_image(filepath)
            
            # If OCR result is a dict (from Mathpix), use the LaTeX format
            if isinstance(ocr_result, dict):
                problem_text = ocr_result.get("latex", ocr_result.get("text", ""))
            else:
                problem_text = ocr_result
                
            print(f"Using OCR text: {problem_text}")
        else:
            error_msg = "No problem provided. Please upload an image or enter text."
            print(f"Error: {error_msg}")
            return jsonify({"error": error_msg}), 400
        
        # Preprocess and check if we have valid problem text
        problem_text = preprocess_text(problem_text)
        if not problem_text.strip():
            error_msg = "Empty problem text extracted. Please try again with clearer input."
            print(f"Error: {error_msg}")
            return jsonify({"error": error_msg}), 400
            
        # Format the problem text for the models
        formatted_problem = f"""
        MATH PROBLEM:
        {problem_text}
        
        INSTRUCTIONS:
        1. Solve this step-by-step
        2. Show all your work and calculations
        3. Clearly indicate the final answer
        """
        
        print(f"Formatted problem: {formatted_problem}")
        
        # Query available AI models
        responses = {}
        if "chatgpt" in available_models:
            responses["chatgpt"] = ai_interface.query_chatgpt(formatted_problem)
        if "claude" in available_models:
            responses["claude"] = ai_interface.query_claude(formatted_problem)
        if "deepseek" in available_models:
            responses["deepseek"] = ai_interface.query_deepseek(formatted_problem)
        
        # Only proceed if we have at least one valid response
        if not responses:
            return jsonify({"error": "Failed to get responses from any AI models."}), 500
        
        # Verify and reconcile the answers
        result = verifier.verify_and_reconcile(responses)
        
        # Add timestamp and problem text to the result
        result["timestamp"] = datetime.now().isoformat()
        result["problem_text"] = problem_text
        result["available_models"] = available_models
        
        # Save result to history
        save_to_history(result)
        
        return jsonify(result)
    
    except Exception as e:
        # Log the error with full stack trace
        print(f"Error processing submission: {str(e)}")
        traceback.print_exc()
        
        # Return error message
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get submission history"""
    history = []
    history_dir = "history"
    
    for filename in os.listdir(history_dir):
        if filename.endswith('.json'):
            with open(os.path.join(history_dir, filename), 'r') as f:
                try:
                    data = json.load(f)
                    # Add a simplified version to the list
                    history.append({
                        "id": filename,
                        "timestamp": data.get("timestamp", ""),
                        "problem_text": data.get("problem_text", ""),
                        "confidence": data.get("consensus", {}).get("confidence", "unknown")
                    })
                except json.JSONDecodeError:
                    continue
    
    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return jsonify(history)

@app.route('/api/history/<history_id>', methods=['GET'])
def get_history_item(history_id):
    """Get a specific history item"""
    history_file = os.path.join("history", history_id)
    
    if not os.path.exists(history_file):
        return jsonify({"error": "History item not found"}), 404
    
    with open(history_file, 'r') as f:
        try:
            data = json.load(f)
            return jsonify(data)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid history file"}), 500

def save_to_history(result):
    """Save result to history file"""
    history_dir = "history"
    
    # Create unique filename with timestamp
    filename = f"{history_dir}/result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

if __name__ == '__main__':
    # Check if at least one model is available
    available_models = get_available_models()
    if not available_models:
        print("WARNING: No AI models available. Please configure at least one API key in the .env file.")
    else:
        print(f"Available models: {', '.join(available_models)}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)