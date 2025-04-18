# unichat

A unified AI system that combines multiple language models to solve, verify, and reconcile math problems.

![Math AI Verifier](https://img.freepik.com/free-vector/chatbot-chat-message-vectorart_78370-4104.jpg?t=st=1744966663~exp=1744970263~hmac=8f708d4066f0f7a8c46755c6738e5dc9bcde1ad4e8c4910128616628de0dcc4f&w=1380)

## Overview

Unichat is a web application that leverages the power of multiple AI language models (ChatGPT, Claude, and DeepSeek) to solve mathematical problems with increased accuracy and confidence. By combining responses from multiple models and implementing a verification system, this application provides more reliable solutions than any single AI model could offer.

## Features

- **Multi-model verification**: Queries multiple AI models and reconciles their answers
- **Confidence levels**: Provides high, medium, or low confidence ratings based on model agreement
- **OCR for math problems**: Upload images of math problems for automatic processing
- **Step-by-step solutions**: Detailed explanations from each model
- **Solution history**: Save and review past problems and solutions
- **Automatic consensus finding**: Identifies when models agree on solutions
- **Math notation support**: Displays mathematical notation properly

## Installation

### Prerequisites

- Ubuntu 20.04 LTS or similar Linux distribution
- Python 3.8+
- API keys for the following services:
  - OpenAI (for ChatGPT)
  - Anthropic (for Claude)
  - DeepSeek (optional)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/math-ai-verifier.git
   cd math-ai-verifier
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv tesseract-ocr
   pip install openai anthropic requests flask python-dotenv pillow pytesseract sympy numpy matplotlib
   ```

4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter a math problem directly in the text field or upload an image containing a math problem
2. Click "Submit Problem" to send the problem to multiple AI models
3. Review the consolidated answer with confidence rating
4. Explore step-by-step solutions from each model
5. Access your solution history for previous problems

## Project Structure

```
math-ai-verifier/
├── app.py                # Main Flask application
├── ai_models.py          # AI model interface components
├── answer_verifier.py    # Verification and reconciliation logic
├── ocr_processor.py      # OCR processing for math images
├── templates/            # HTML templates
│   └── index.html        # Main application interface
├── static/               # Static assets
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── uploads/              # Temporary storage for uploaded images
└── history/              # Stored solutions and history
```

## Known Issues

1. **Math OCR Recognition**: The current OCR implementation has limitations with complex mathematical notation. Consider implementing a specialized math OCR service for better results.

2. **DeepSeek API Integration**: The DeepSeek API occasionally returns generic responses rather than solutions. Further refinement of prompts may improve results.

3. **Answer Extraction**: The pattern-matching approach to extract final answers may not handle all response formats correctly.

4. **Mobile Interface**: The current UI is not fully optimized for mobile devices.

## Future Improvements

1. **Enhanced Answer Verification**: Improve the verification process by having models check each other's solutions rather than relying on pattern matching.

2. **Symbolic Math Comparison**: Implement better symbolic math comparison to recognize equivalent expressions presented in different formats.

3. **Custom Math OCR**: Develop or integrate a specialized mathematical OCR system for better equation recognition.

4. **Model Weighting**: Implement a weighting system that learns which models perform better on certain types of problems.

5. **Solution Quality Metrics**: Add metrics to evaluate solution clarity and completeness.

6. **API Fallback Strategy**: Implement smarter fallback mechanisms when certain APIs are unavailable.

7. **User Feedback Loop**: Allow users to rate solutions and use this feedback to improve the system.

8. **Expanded Problem Types**: Add support for specialized math domains like statistics, linear algebra, and calculus.

9. **Export Options**: Allow exporting solutions in different formats (PDF, LaTeX, etc.).

10. **Explanation Generation**: Create a unified explanation that combines the best parts of each model's solution.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for the ChatGPT API
- Anthropic for the Claude API
- DeepSeek for their API
- The open-source community for various libraries used in this project

## Contact

Jerry Liu - zhentinl@andrew.cmu.edu

Project Link: [https://github.com/JerryZhenTing/unichat](https://github.com/JerryZhenTing/unichat)

---

*Note: This project is for educational purposes and is not intended to replace proper learning and understanding of mathematical concepts.*
