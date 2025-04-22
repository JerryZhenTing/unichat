import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import re
from collections import Counter

class MathAIAnalyzer:
    def __init__(self, history_dir="history"):
        self.history_dir = history_dir
        self.results_df = None
        self.model_comparison_df = None
        
    def load_history(self):
        """Load all history files into a pandas DataFrame"""
        data = []
        
        for filename in os.listdir(self.history_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.history_dir, filename), 'r') as f:
                    try:
                        result = json.load(f)
                        
                        # Extract key information
                        entry = {
                            'id': filename,
                            'timestamp': result.get('timestamp'),
                            'problem_text': result.get('problem_text'),
                            'consensus_status': result.get('consensus', {}).get('status'),
                            'confidence': result.get('consensus', {}).get('confidence'),
                            'available_models': result.get('available_models', []),
                            'raw_responses': result.get('raw_responses', {}),
                            'raw_answers': result.get('raw_answers', {})
                        }
                        
                        # Add model-specific data
                        for model in entry['available_models']:
                            entry[f'{model}_answer'] = entry['raw_answers'].get(model)
                            entry[f'{model}_response_length'] = len(entry['raw_responses'].get(model, ''))
                            entry[f'{model}_error'] = entry['raw_responses'].get(model, '').startswith('Error')
                        
                        data.append(entry)
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error processing {filename}: {e}")
        
        # Convert to DataFrame
        self.results_df = pd.DataFrame(data)
        
        # Convert timestamp to datetime
        if 'timestamp' in self.results_df.columns:
            self.results_df['timestamp'] = pd.to_datetime(self.results_df['timestamp'])
        
        print(f"Loaded {len(self.results_df)} results")
        return self.results_df
    
    def calculate_metrics(self):
        """Calculate performance metrics from the results"""
        if self.results_df is None:
            self.load_history()
            
        if len(self.results_df) == 0:
            print("No data available for analysis")
            return {}
            
        metrics = {}
        
        # Consensus rates
        consensus_counts = self.results_df['consensus_status'].value_counts(normalize=True) * 100
        metrics['consensus_rates'] = consensus_counts.to_dict()
        
        # Confidence distribution
        confidence_counts = self.results_df['confidence'].value_counts(normalize=True) * 100
        metrics['confidence_distribution'] = confidence_counts.to_dict()
        
        # Model availability
        model_counts = {}
        for model in ['chatgpt', 'claude', 'deepseek']:
            model_counts[model] = (self.results_df['available_models'].apply(lambda x: model in x).sum() / len(self.results_df)) * 100
        metrics['model_availability'] = model_counts
        
        # Error rates per model
        error_rates = {}
        for model in ['chatgpt', 'claude', 'deepseek']:
            col = f'{model}_error'
            if col in self.results_df.columns:
                error_rates[model] = (self.results_df[col].sum() / self.results_df[col].count()) * 100
        metrics['error_rates'] = error_rates
        
        # Response length statistics
        length_stats = {}
        for model in ['chatgpt', 'claude', 'deepseek']:
            col = f'{model}_response_length'
            if col in self.results_df.columns:
                length_stats[model] = {
                    'mean': self.results_df[col].mean(),
                    'median': self.results_df[col].median(),
                    'min': self.results_df[col].min(),
                    'max': self.results_df[col].max()
                }
        metrics['response_length'] = length_stats
        
        # Calculate overall success rate
        metrics['overall_success_rate'] = (
            (self.results_df['consensus_status'] == 'full_consensus').sum() +
            (self.results_df['consensus_status'] == 'majority_consensus').sum()
        ) / len(self.results_df) * 100
        
        # Calculate model agreement rates
        self._calculate_model_agreement()
        metrics['model_agreement'] = self.model_comparison_df.to_dict() if self.model_comparison_df is not None else {}
        
        return metrics
    
    def _calculate_model_agreement(self):
        """Calculate agreement rates between models"""
        if self.results_df is None or len(self.results_df) == 0:
            return
            
        model_pairs = []
        
        # Identify which model pairs we can analyze
        models = ['chatgpt', 'claude', 'deepseek']
        for i, model1 in enumerate(models):
            for model2 in models[i+1:]:
                col1 = f'{model1}_answer'
                col2 = f'{model2}_answer'
                if col1 in self.results_df.columns and col2 in self.results_df.columns:
                    model_pairs.append((model1, model2))
        
        if not model_pairs:
            return
            
        # Create agreement matrix
        agreement_data = {}
        
        for model1 in models:
            agreement_data[model1] = {}
            for model2 in models:
                if model1 == model2:
                    # Model always agrees with itself
                    agreement_data[model1][model2] = 1.0
                elif (model1, model2) in model_pairs or (model2, model1) in model_pairs:
                    # Calculate agreement
                    col1 = f'{model1}_answer'
                    col2 = f'{model2}_answer'
                    
                    # Filter for rows where both models provided an answer
                    mask = (~self.results_df[col1].isna()) & (~self.results_df[col2].isna())
                    agreement = (self.results_df[mask][col1] == self.results_df[mask][col2]).mean()
                    
                    agreement_data[model1][model2] = agreement
                else:
                    # Not enough data to calculate
                    agreement_data[model1][model2] = None
        
        self.model_comparison_df = pd.DataFrame(agreement_data)
    
    def generate_visualizations(self, output_dir="analysis_results"):
        """Generate visualizations from the analysis"""
        if self.results_df is None:
            self.load_history()
            
        if len(self.results_df) == 0:
            print("No data available for visualization")
            return
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get metrics
        metrics = self.calculate_metrics()
        
        # Set style
        sns.set(style="whitegrid")
        plt.rcParams.update({'font.size': 12})
        
        # 1. Consensus Status Distribution
        plt.figure(figsize=(10, 6))
        ax = sns.countplot(x='consensus_status', data=self.results_df, palette='viridis')
        plt.title('Distribution of Consensus Status')
        plt.xlabel('Consensus Status')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        
        # Add percentage labels
        total = len(self.results_df)
        for p in ax.patches:
            percentage = f'{100 * p.get_height() / total:.1f}%'
            ax.annotate(percentage, (p.get_x() + p.get_width() / 2., p.get_height()),
                       ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'consensus_distribution.png'))
        plt.close()
        
        # 2. Confidence Levels
        plt.figure(figsize=(10, 6))
        ax = sns.countplot(x='confidence', data=self.results_df, 
                          order=['high', 'medium', 'low'],
                          palette={'high': 'green', 'medium': 'orange', 'low': 'red'})
        plt.title('Distribution of Confidence Levels')
        plt.xlabel('Confidence Level')
        plt.ylabel('Count')
        
        # Add percentage labels
        for p in ax.patches:
            percentage = f'{100 * p.get_height() / total:.1f}%'
            ax.annotate(percentage, (p.get_x() + p.get_width() / 2., p.get_height()),
                       ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'confidence_levels.png'))
        plt.close()
        
        # 3. Model Agreement Heatmap
        if self.model_comparison_df is not None:
            plt.figure(figsize=(8, 6))
            sns.heatmap(self.model_comparison_df, annot=True, cmap='YlGnBu', vmin=0, vmax=1, 
                       fmt='.2f', linewidths=.5)
            plt.title('Model Agreement Rates')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'model_agreement.png'))
            plt.close()
        
        # 4. Response Length Comparison
        length_cols = [col for col in self.results_df.columns if col.endswith('_response_length')]
        if length_cols:
            # Prepare data for plotting
            length_data = []
            for col in length_cols:
                model = col.split('_')[0]
                for length in self.results_df[col].dropna():
                    length_data.append({'Model': model, 'Response Length': length})
            
            length_df = pd.DataFrame(length_data)
            
            plt.figure(figsize=(10, 6))
            ax = sns.boxplot(x='Model', y='Response Length', data=length_df, palette='Set2')
            plt.title('Response Length by Model')
            plt.ylabel('Length (characters)')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'response_length.png'))
            plt.close()
        
        # 5. Success Rate Over Time
        if 'timestamp' in self.results_df.columns:
            # Sort by timestamp
            time_df = self.results_df.sort_values('timestamp')
            
            # Create success indicator (1 for consensus, 0 for no consensus)
            time_df['success'] = time_df['consensus_status'].apply(
                lambda x: 1 if x in ['full_consensus', 'majority_consensus'] else 0
            )
            
            # Calculate rolling success rate
            window_size = min(10, len(time_df))
            if window_size > 1:
                time_df['rolling_success'] = time_df['success'].rolling(window=window_size).mean() * 100
                
                plt.figure(figsize=(12, 6))
                plt.plot(time_df['timestamp'], time_df['rolling_success'], 'b-')
                plt.title(f'Success Rate Over Time ({window_size}-problem rolling window)')
                plt.xlabel('Time')
                plt.ylabel('Success Rate (%)')
                plt.ylim(0, 105)
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'success_over_time.png'))
                plt.close()
        
        # 6. Create a summary report
        self._generate_summary_report(metrics, output_dir)
        
        print(f"Visualizations and report saved to {output_dir}")
    
    def _generate_summary_report(self, metrics, output_dir):
        """Generate a summary report of the analysis"""
        with open(os.path.join(output_dir, 'summary_report.md'), 'w') as f:
            f.write("# Math AI Verifier Analysis Report\n\n")
            
            f.write(f"## Overview\n\n")
            f.write(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total problems analyzed: {len(self.results_df)}\n\n")
            
            f.write("## Performance Metrics\n\n")
            
            # Overall success rate
            f.write(f"### Overall Success Rate\n\n")
            f.write(f"Success rate: {metrics.get('overall_success_rate', 0):.1f}%\n\n")
            
            # Consensus breakdown
            f.write(f"### Consensus Distribution\n\n")
            f.write("| Consensus Type | Percentage |\n")
            f.write("|----------------|------------|\n")
            for status, pct in metrics.get('consensus_rates', {}).items():
                f.write(f"| {status} | {pct:.1f}% |\n")
            f.write("\n")
            
            # Confidence levels
            f.write(f"### Confidence Levels\n\n")
            f.write("| Confidence | Percentage |\n")
            f.write("|------------|------------|\n")
            for confidence, pct in metrics.get('confidence_distribution', {}).items():
                f.write(f"| {confidence} | {pct:.1f}% |\n")
            f.write("\n")
            
            # Model availability
            f.write(f"### Model Availability\n\n")
            f.write("| Model | Availability |\n")
            f.write("|-------|-------------|\n")
            for model, pct in metrics.get('model_availability', {}).items():
                f.write(f"| {model} | {pct:.1f}% |\n")
            f.write("\n")
            
            # Error rates
            f.write(f"### Error Rates by Model\n\n")
            f.write("| Model | Error Rate |\n")
            f.write("|-------|------------|\n")
            for model, pct in metrics.get('error_rates', {}).items():
                f.write(f"| {model} | {pct:.1f}% |\n")
            f.write("\n")
            
            # Response length statistics
            f.write(f"### Response Length Statistics\n\n")
            f.write("| Model | Mean Length | Median Length | Min | Max |\n")
            f.write("|-------|-------------|---------------|-----|-----|\n")
            for model, stats in metrics.get('response_length', {}).items():
                f.write(f"| {model} | {stats['mean']:.1f} | {stats['median']:.1f} | {stats['min']} | {stats['max']} |\n")
            f.write("\n")
            
            # Models agreement
            f.write(f"### Model Agreement Matrix\n\n")
            if self.model_comparison_df is not None:
                f.write("*Values show the proportion of cases where models provided the same answer*\n\n")
                f.write("| | " + " | ".join(self.model_comparison_df.columns) + " |\n")
                f.write("|" + "-|"*(len(self.model_comparison_df.columns)+1) + "\n")
                
                for idx, row in self.model_comparison_df.iterrows():
                    f.write(f"| {idx} |")
                    for col in self.model_comparison_df.columns:
                        val = row[col]
                        if val is None:
                            f.write(" N/A |")
                        else:
                            f.write(f" {val:.2f} |")
                    f.write("\n")
                f.write("\n")
            
            # Visualizations reference
            f.write("## Visualizations\n\n")
            f.write("The following visualizations have been generated:\n\n")
            f.write("1. Consensus Distribution (`consensus_distribution.png`)\n")
            f.write("2. Confidence Levels (`confidence_levels.png`)\n")
            f.write("3. Model Agreement Heatmap (`model_agreement.png`)\n")
            f.write("4. Response Length by Model (`response_length.png`)\n")
            f.write("5. Success Rate Over Time (`success_over_time.png`)\n")
            
            # Recommendations
            f.write("\n## Observations and Recommendations\n\n")
            
            # Add some automatic observations based on the metrics
            observations = []
            
            # Success rate observation
            success_rate = metrics.get('overall_success_rate', 0)
            if success_rate < 50:
                observations.append("- The overall success rate is quite low. Consider improving prompt engineering or evaluating why models are providing inconsistent answers.")
            elif success_rate > 80:
                observations.append("- The system shows a high success rate, indicating good consensus among models.")
            
            # Model agreement observations
            if self.model_comparison_df is not None:
                for model1 in self.model_comparison_df.columns:
                    for model2 in self.model_comparison_df.columns:
                        if model1 != model2 and model1 < model2:  # Avoid duplicates
                            agreement = self.model_comparison_df.loc[model1, model2]
                            if agreement is not None:
                                if agreement < 0.5:
                                    observations.append(f"- {model1} and {model2} have low agreement ({agreement:.2f}). This may indicate different approaches to solving problems.")
                                elif agreement > 0.8:
                                    observations.append(f"- {model1} and {model2} have high agreement ({agreement:.2f}), suggesting consistent methodology.")
            
            # Add error rate observations
            for model, rate in metrics.get('error_rates', {}).items():
                if rate > 10:
                    observations.append(f"- {model} has a relatively high error rate ({rate:.1f}%). Check API configuration and error handling.")
            
            # Add the observations to the report
            if observations:
                for obs in observations:
                    f.write(f"{obs}\n")
            else:
                f.write("No automated observations generated. Please review the metrics and visualizations for insights.\n")
            
            # Final recommendations
            f.write("\n### Recommendations for Improvement\n\n")
            f.write("1. Consider enhancing the prompt engineering for models with lower agreement rates.\n")
            f.write("2. Implement more robust error handling for models with higher error rates.\n")
            f.write("3. Review patterns in problems with 'no_consensus' status to identify potential improvement areas.\n")
            f.write("4. Evaluate the balance between different models - consider if all models are providing unique value.\n")
            f.write("5. Periodically review and update this analysis to track system improvements over time.\n")

# Usage example
if __name__ == "__main__":
    analyzer = MathAIAnalyzer()
    analyzer.load_history()
    metrics = analyzer.calculate_metrics()
    analyzer.generate_visualizations()
    
    print("\nAnalysis Summary:")
    print(f"Total problems analyzed: {len(analyzer.results_df)}")
    print(f"Overall success rate: {metrics.get('overall_success_rate', 0):.1f}%")
    print("\nTo see detailed results, check the 'analysis_results' directory.")