document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('problem-form');
    const loading = document.getElementById('loading');
    const resultArea = document.getElementById('result-area');
    const viewHistoryBtn = document.getElementById('view-history');
    const historyModal = new bootstrap.Modal(document.getElementById('historyModal'));
    
    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const problemImage = document.getElementById('problem-image').files[0];
        const problemText = document.getElementById('problem-text').value;
        
        // Validate input
        if (!problemImage && !problemText.trim()) {
            alert('Please upload an image or enter the problem text.');
            return;
        }
        
        // Show loading, hide results
        loading.style.display = 'block';
        resultArea.style.display = 'none';
        
        try {
            const response = await fetch('/api/submit', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            
            const data = await response.json();
            
            // Hide loading, show results
            loading.style.display = 'none';
            resultArea.style.display = 'block';
            
            // Display results
            displayResults(data);
            
            // Render any math with MathJax
            if (window.MathJax) {
                MathJax.typesetPromise();
            }
            
        } catch (error) {
            console.error('Error:', error);
            loading.style.display = 'none';
            alert('An error occurred: ' + error.message);
        }
    });
    
    // Handle view history button
    viewHistoryBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/history');
            
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            
            const data = await response.json();
            
            // Display history items
            displayHistory(data);
            
            // Show the modal
            historyModal.show();
            
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load history: ' + error.message);
        }
    });
    
    function displayResults(data) {
        // Display problem
        document.getElementById('problem-display').textContent = data.problem_text;
        
        // Set confidence badge
        const confidenceBadge = document.getElementById('confidence-badge');
        const confidence = data.consensus.confidence;
        confidenceBadge.textContent = `Confidence: ${confidence.toUpperCase()}`;
        
        if (confidence === 'high') {
            confidenceBadge.className = 'badge bg-success';
        } else if (confidence === 'medium') {
            confidenceBadge.className = 'badge bg-warning text-dark';
        } else {
            confidenceBadge.className = 'badge bg-danger';
        }
        
        // Display verified answer
        const verifiedAnswer = document.getElementById('verified-answer');
        
        if (data.consensus.status === 'full_consensus') {
            verifiedAnswer.innerHTML = `<p><strong>All models agree:</strong> ${displayAnswer(data.consensus.answer)}</p>`;
        } else if (data.consensus.status === 'majority_consensus') {
            const agreeingModels = data.consensus.agreeing_models.join(' and ');
            verifiedAnswer.innerHTML = `<p><strong>${agreeingModels} agree:</strong> ${displayAnswer(data.consensus.answer)}</p>`;
        } else {
            verifiedAnswer.innerHTML = `<p><strong>No consensus reached.</strong> The models provided different answers:</p>`;
            for (const [model, answer] of Object.entries(data.raw_answers)) {
                if (answer) {
                    verifiedAnswer.innerHTML += `<p>${model}: ${answer}</p>`;
                }
            }
        }
        
        // Display best explanation
        const bestExplanation = document.getElementById('best-explanation');
        if (typeof data.explanation === 'object' && data.explanation.best_explanation) {
            bestExplanation.innerHTML = `<p><strong>Best explanation (from ${data.explanation.model}):</strong></p>`;
            bestExplanation.innerHTML += `<div class="model-response">${formatExplanation(data.explanation.best_explanation)}</div>`;
        } else {
            bestExplanation.innerHTML = '<p>No consensus on best explanation. Check individual model responses below.</p>';
        }
        
        // Display individual model responses
        document.getElementById('chatgpt-content').innerHTML = formatExplanation(data.raw_responses.chatgpt);
        document.getElementById('claude-content').innerHTML = formatExplanation(data.raw_responses.claude);
        document.getElementById('deepseek-content').innerHTML = formatExplanation(data.raw_responses.deepseek);
    }
    
    function displayAnswer(answer) {
        if (answer === null || answer === undefined) {
            return 'No answer provided';
        }
        
        // If it's an object, convert to string (for simplified display)
        if (typeof answer === 'object') {
            return JSON.stringify(answer);
        }
        
        return answer;
    }
    
    function formatExplanation(explanation) {
        if (!explanation) {
            return '<p>No explanation available</p>';
        }
        
        if (explanation.startsWith('Error:')) {
            return `<p class="text-danger">${explanation}</p>`;
        }
        
        // Convert line breaks to HTML and format math expressions
        let formatted = explanation.replace(/\n/g, '<br>');
        
        // Highlight math expressions with $ signs (for MathJax)
        // This is a simplified approach - might need refinement
        formatted = formatted.replace(/\$(.+?)\$/g, '<span class="text-primary">$$$1$$</span>');
        
        return formatted;
    }
    
    function displayHistory(historyItems) {
        const tableBody = document.getElementById('history-table-body');
        tableBody.innerHTML = '';
        
        if (historyItems.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No history items found</td></tr>';
            return;
        }
        
        for (const item of historyItems) {
            const row = document.createElement('tr');
            
            // Format timestamp
            const date = new Date(item.timestamp);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            
            // Create table cells
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>${truncateText(item.problem_text, 30)}</td>
                <td><span class="badge bg-${getConfidenceColor(item.confidence)}">${item.confidence.toUpperCase()}</span></td>
                <td><button class="btn btn-sm btn-outline-primary view-item" data-id="${item.id}">View</button></td>
            `;
            
            tableBody.appendChild(row);
        }
        
        // Add event listeners to view buttons
        document.querySelectorAll('.view-item').forEach(button => {
            button.addEventListener('click', async function() {
                const id = this.getAttribute('data-id');
                try {
                    const response = await fetch(`/api/history/${id}`);
                    
                    if (!response.ok) {
                        throw new Error('Server error: ' + response.status);
                    }
                    
                    const data = await response.json();
                    
                    // Hide modal
                    historyModal.hide();
                    
                    // Display results
                    displayResults(data);
                    resultArea.style.display = 'block';
                    
                    // Render any math with MathJax
                    if (window.MathJax) {
                        MathJax.typesetPromise();
                    }
                    
                } catch (error) {
                    console.error('Error:', error);
                    alert('Failed to load history item: ' + error.message);
                }
            });
        });
    }
    
    function truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    function getConfidenceColor(confidence) {
        switch(confidence) {
            case 'high': return 'success';
            case 'medium': return 'warning';
            case 'low': return 'danger';
            default: return 'secondary';
        }
    }
});