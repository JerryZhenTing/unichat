import re
import sympy
from sympy.parsing.sympy_parser import parse_expr
import numpy as np

class AnswerVerifier:
    def __init__(self):
        pass
    
    def extract_final_answers(self, responses):
        """Extract final answers from each model's response"""
        final_answers = {}
        
        for model, response in responses.items():
            if response is None or (isinstance(response, str) and response.startswith("Error")):
                final_answers[model] = None
                continue
                
            # Try various patterns to extract the final answer
            answer = self._extract_with_patterns(response)
            
            # Store the extracted answer
            final_answers[model] = answer
        
        return final_answers
    
    def _extract_with_patterns(self, response):
        """Extract final answer using various patterns"""
        # Try patterns like "final answer is X", "answer: X", "X is the answer", etc.
        patterns = [
            r"final answer[\s]*[:=][\s]*(.+?)[\.\n]",
            r"answer[\s]*[:=][\s]*(.+?)[\.\n]",
            r"result[\s]*[:=][\s]*(.+?)[\.\n]",
            r"solution[\s]*[:=][\s]*(.+?)[\.\n]",
            r"therefore,[\s]*(.+?)[\.\n]",
            r"thus,[\s]*(.+?)[\.\n]",
            r"=[\s]*(.+?)[\.\n]"  # Last resort: look for equals sign
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                # Take the last match, as it's more likely to be the final answer
                return matches[-1].strip()
        
        # If no matches found, return a portion of the last line
        lines = response.strip().split('\n')
        if lines:
            return lines[-1].strip()
        
        return None
    
    def normalize_answers(self, answers):
        """Normalize answers for comparison (handle different formats)"""
        normalized = {}
        
        for model, answer in answers.items():
            if answer is None:
                normalized[model] = None
                continue
                
            # Remove explanatory text, keep only the math part
            cleaned = self._clean_answer(answer)
            
            # Try to parse with sympy for symbolic comparison
            try:
                # Convert to sympy expression
                expr = parse_expr(cleaned)
                normalized[model] = expr
            except Exception:
                # If parsing fails, use the cleaned string
                normalized[model] = cleaned
        
        return normalized
    
    def _clean_answer(self, answer):
        """Clean up answer text for normalization"""
        # Remove phrases like "the answer is", "we get", etc.
        phrases_to_remove = [
            "the answer is", "we get", "we have", "equals", "equal to",
            "is equal to", "is", "the result is", "final answer", "=", ":"
        ]
        
        cleaned = answer.lower()
        for phrase in phrases_to_remove:
            cleaned = cleaned.replace(phrase, "")
        
        # Remove extra spaces, commas, etc.
        cleaned = re.sub(r'[,;]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def are_answers_equivalent(self, answer1, answer2):
        """Check if two normalized answers are mathematically equivalent"""
        if answer1 is None or answer2 is None:
            return False
            
        # If both are sympy expressions
        if isinstance(answer1, sympy.Expr) and isinstance(answer2, sympy.Expr):
            try:
                # Check if their difference simplifies to zero
                diff = sympy.simplify(answer1 - answer2)
                return diff == 0
            except Exception:
                pass
        
        # If they're strings, compare them directly
        if isinstance(answer1, str) and isinstance(answer2, str):
            return answer1 == answer2
        
        # Convert to strings as a last resort
        return str(answer1) == str(answer2)
    
    def find_consensus(self, normalized_answers):
        """Find consensus among answers or identify the majority answer"""
        models = list(normalized_answers.keys())
        num_models = len(models)
        
        # Handle case with no models or just one model
        if num_models == 0:
            return {
                "status": "no_models",
                "confidence": "low"
            }
        
        if num_models == 1:
            if normalized_answers[models[0]] is not None:
                return {
                    "status": "single_model",
                    "answer": normalized_answers[models[0]],
                    "model": models[0],
                    "confidence": "medium"  # Medium confidence for single model
                }
            else:
                return {
                    "status": "no_consensus",
                    "confidence": "low"
                }
        
        # For two or more models, check if all agree
        all_agree = True
        reference_model = None
        
        # Find the first model with a non-None answer to use as reference
        for model in models:
            if normalized_answers[model] is not None:
                reference_model = model
                break
        
        # If no model has a valid answer
        if reference_model is None:
            return {
                "status": "no_consensus",
                "confidence": "low"
            }
        
        # Check if all other models with non-None answers agree with the reference model
        for model in models:
            if model != reference_model and normalized_answers[model] is not None:
                if not self.are_answers_equivalent(normalized_answers[reference_model], normalized_answers[model]):
                    all_agree = False
                    break
        
        # If all models with valid answers agree
        if all_agree:
            return {
                "status": "full_consensus",
                "answer": normalized_answers[reference_model],
                "confidence": "high" if num_models > 1 else "medium"
            }
        
        # If not all agree, check for majority consensus (only relevant for 3+ models)
        if num_models >= 3:
            for i in range(num_models):
                if normalized_answers[models[i]] is None:
                    continue
                    
                # Count how many models agree with this one
                agreeing_models = [models[i]]
                for j in range(num_models):
                    if i != j and normalized_answers[models[j]] is not None:
                        if self.are_answers_equivalent(normalized_answers[models[i]], normalized_answers[models[j]]):
                            agreeing_models.append(models[j])
                
                # If we have a majority
                if len(agreeing_models) > num_models / 2:
                    return {
                        "status": "majority_consensus",
                        "answer": normalized_answers[models[i]],
                        "agreeing_models": agreeing_models,
                        "confidence": "medium"
                    }
        
        # No consensus found
        return {
            "status": "no_consensus",
            "answers": {model: str(answer) if hasattr(answer, '__str__') else answer 
                    for model, answer in normalized_answers.items()},
            "confidence": "low"
        }
    
    def select_best_explanation(self, responses, consensus_result):
        """Select the best explanation based on the consensus result"""
        if consensus_result["status"] == "full_consensus":
            # If all agree, select the most detailed explanation
            return self._select_most_detailed(responses)
        elif consensus_result["status"] == "majority_consensus":
            # If majority, select most detailed from agreeing models
            agreeing_models = consensus_result["agreeing_models"]
            filtered_responses = {model: resp for model, resp in responses.items() if model in agreeing_models}
            return self._select_most_detailed(filtered_responses)
        else:
            # If no consensus, return all explanations
            return responses
    
    def _select_most_detailed(self, responses):
        """Select the most detailed explanation based on length and structure"""
        # Simple heuristic: longer responses tend to be more detailed
        # (This could be improved with more sophisticated analysis)
        scores = {}
        
        for model, response in responses.items():
            if response is None or (isinstance(response, str) and response.startswith("Error")):
                scores[model] = 0
                continue
                
            # Base score: length of response
            score = len(response)
            
            # Bonus for step-by-step structure
            if "step" in response.lower():
                score += 200
            
            # Bonus for explanations
            if "because" in response.lower() or "since" in response.lower():
                score += 100
            
            # Bonus for mathematical symbols and equations
            math_symbols = sum(1 for c in response if c in "+-*/=^√∫∑π")
            score += math_symbols * 5
            
            scores[model] = score
        
        # Get the model with the highest score
        if not scores:
            return "No valid explanations available"
            
        best_model = max(scores, key=scores.get)
        return {
            "best_explanation": responses[best_model],
            "model": best_model
        }
    
    def verify_and_reconcile(self, responses):
        """Main function to verify and reconcile answers from different models"""
        # Extract final answers
        final_answers = self.extract_final_answers(responses)
        
        # Normalize answers for comparison
        normalized_answers = self.normalize_answers(final_answers)
        
        # Find consensus or majority
        consensus_result = self.find_consensus(normalized_answers)
        
        # Select best explanation
        explanation = self.select_best_explanation(responses, consensus_result)
        
        # Prepare the final result
        result = {
            "consensus": consensus_result,
            "explanation": explanation,
            "raw_answers": final_answers,
            "raw_responses": responses
        }
        
        return result
    # Add this method to the MathAIAnalyzer class to analyze problem complexity
    def analyze_problem_complexity(self):
        """Analyze how complexity affects model consensus"""
        if self.results_df is None:
            self.load_history()
            
        # Create a simple complexity metric based on problem length
        self.results_df['problem_complexity'] = self.results_df['problem_text'].apply(len)
        
        # Create complexity bins
        self.results_df['complexity_bin'] = pd.qcut(
            self.results_df['problem_complexity'], 
            4, 
            labels=["Simple", "Moderate", "Complex", "Very Complex"]
        )
        
        # Analyze success rate by complexity
        success_by_complexity = self.results_df.groupby('complexity_bin')['consensus_status'].apply(
            lambda x: (x == 'full_consensus').sum() / len(x) * 100
        )
        
        # Visualize
        plt.figure(figsize=(10, 6))
        success_by_complexity.plot(kind='bar', color='skyblue')
        plt.title('Success Rate by Problem Complexity')
        plt.xlabel('Problem Complexity')
        plt.ylabel('Full Consensus Rate (%)')
        plt.ylim(0, 100)
        plt.grid(axis='y')
        plt.tight_layout()
        plt.savefig('analysis_results/complexity_analysis.png')
        plt.close()
        
        return success_by_complexity