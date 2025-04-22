import os
import openai
from anthropic import Anthropic
import requests
import json
import time
from dotenv import load_dotenv
import concurrent.futures

# Load environment variables
load_dotenv()


class AIModelInterface:
    def __init__(self):
        # Initialize API clients

        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

    def query_chatgpt(self, problem_text):
        """Query OpenAI's ChatGPT model with the math problem"""
        if not self.openai_client:
            return "Error: OpenAI API key not configured"

        try:
            # Format the problem to ensure direct solving
            formatted_problem = f"""
            Please solve this math problem step by step. Show all your work and clearly state the final answer.
            
            PROBLEM:
            {problem_text}
            
            Begin solving immediately. No introductions needed.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use gpt-3.5-turbo which is more widely available
                messages=[
                    {
                        "role": "system",
                        "content": "You are a math expert. Your task is to solve math problems step-by-step, show all work, and clearly state the final answer. Do not include any introductory text. Go straight to solving the problem.",
                    },
                    {"role": "user", "content": formatted_problem},
                ],
                temperature=0.1,  # Low temperature for more deterministic results
            )
            return self._post_process_response(response.choices[0].message.content)
        except Exception as e:
            print(f"ChatGPT query failed: {e}")
            return f"Error: {str(e)}"

    def query_claude(self, problem_text):
        """Query Anthropic's Claude model with the math problem"""
        if not self.anthropic_client:
            return "Error: Anthropic API key not configured"

        try:
            # Format the problem to ensure direct solving
            formatted_problem = f"""
            Please solve this math problem step by step. Show all your work and clearly state the final answer.
            
            PROBLEM:
            {problem_text}
            
            Begin solving immediately. No introductions needed.
            """

            response = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",  # Use the most capable model for math
                max_tokens=2000,
                temperature=0.1,
                system="You are a math expert. Your task is to solve math problems step-by-step, show all work, and clearly state the final answer. Do not include any introductory text. Go straight to solving the problem.",
                messages=[{"role": "user", "content": formatted_problem}],
            )
            return response.content[0].text
        except Exception as e:
            print(f"Claude query failed: {e}")
            return f"Error: {str(e)}"

    def query_deepseek(self, problem_text):
        """Query DeepSeek's model with the math problem"""
        if not self.deepseek_api_key or self.deepseek_api_key.startswith("your_"):
            return "Error: DeepSeek API key not configured"

        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json",
            }

            # Make the problem text more explicit
            formatted_problem = f"""
            Please solve this math problem step by step. Show all your work and clearly state the final answer.
            DO NOT respond with "I'm happy to help" or ask for more information.
            
            PROBLEM:
            {problem_text}
            
            Solve this problem directly. Do not wait for further instructions.
            """

            # Format according to DeepSeek API documentation
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a math expert. Your task is to solve math problems step-by-step, show all work, and clearly state the final answer. Do not ask for clarification.",
                    },
                    {"role": "user", "content": formatted_problem},
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
            }

            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                response_json = response.json()
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    return response_json["choices"][0]["message"]["content"]
                else:
                    return (
                        f"Error: Unexpected response format: {response.text[:100]}..."
                    )
            else:
                error_message = (
                    f"Error: API returned status code {response.status_code}"
                )
                try:
                    error_detail = response.json()
                    error_message += f" - {error_detail}"
                except:
                    pass
                return error_message

        except Exception as e:
            print(f"DeepSeek query failed: {e}")
            return f"Error: {str(e)}"

    def query_all_models(self, problem_text):
        """Query all three models in parallel and return their responses"""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks to the executor
            chatgpt_future = executor.submit(self.query_chatgpt, problem_text)
            claude_future = executor.submit(self.query_claude, problem_text)
            deepseek_future = executor.submit(self.query_deepseek, problem_text)

            # Wait for all tasks to complete with a timeout
            timeout = 60  # seconds

            # Collect results
            try:
                chatgpt_response = chatgpt_future.result(timeout=timeout)
            except (concurrent.futures.TimeoutError, Exception) as e:
                chatgpt_response = f"Error: {str(e)}"

            try:
                claude_response = claude_future.result(timeout=timeout)
            except (concurrent.futures.TimeoutError, Exception) as e:
                claude_response = f"Error: {str(e)}"

            try:
                deepseek_response = deepseek_future.result(timeout=timeout)
            except (concurrent.futures.TimeoutError, Exception) as e:
                deepseek_response = f"Error: {str(e)}"

        # Return a dictionary with all responses
        return {
            "chatgpt": chatgpt_response,
            "claude": claude_response,
            "deepseek": deepseek_response,
        }

