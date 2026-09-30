// MODIFIED script.js

// Initialize Lucide icons and start the application once the DOM is fully loaded.
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    initializeApp();
});

// Theme Management
function initializeTheme() {
    // Determine the theme: saved, preference, or default to light.
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    // Apply the initial theme class to the body.
    document.body.classList.toggle('dark', initialTheme === 'dark');
    
    const themeToggle = document.getElementById('theme-toggle');
    // Event listener for theme switching.
    themeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

// Toast Notification System
function showToast(title, description, variant = 'default') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${variant}`;
    
    toast.innerHTML = `
        <div class="toast-title">${title}</div>
        <div class="toast-description">${description}</div>
    `;
    
    container.appendChild(toast);
    
    // Auto remove the toast after a delay.
    setTimeout(() => {
        toast.style.animation = 'fadeIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Compiler Logic
let isLoading = false;
// --- *** MODIFICATION 1: Set correct backend URL *** ---
const API_URL = 'http://127.0.0.1:8000/compile';

function initializeApp() {
    initializeTheme();
    
    const queryInput = document.getElementById('query-input');
    const compileBtn = document.getElementById('compile-btn');
    const charCount = document.getElementById('char-count');
    
    // Update character count on input change.
    queryInput.addEventListener('input', () => {
        charCount.textContent = `${queryInput.value.length} characters`;
        updateCompileButton();
    });
    
    // Bind compilation handler to the button.
    compileBtn.addEventListener('click', handleCompile);
    
    // Enable keyboard shortcut (Ctrl+Enter or Cmd+Enter) for compilation.
    queryInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            handleCompile();
        }
    });
    
    updateCompileButton();
}

// Updates the disabled state of the compile button based on input and loading status.
function updateCompileButton() {
    const queryInput = document.getElementById('query-input');
    const compileBtn = document.getElementById('compile-btn');
    const isEmpty = !queryInput.value.trim();
    
    compileBtn.disabled = isEmpty || isLoading;
}

// Handles the asynchronous compilation request to the backend.
async function handleCompile() {
    const queryInput = document.getElementById('query-input');
    const query = queryInput.value.trim();
    
    if (!query || isLoading) return;
    
    // Set loading state and clear previous output.
    isLoading = true;
    updateCompileButton();
    setLoadingState(true);
    clearOutput();
    
    try {
        const response = await fetch(API_URL, { // --- MODIFICATION 2: Use API_URL ---
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // --- MODIFICATION 3: Send "english_query" to match backend ---
            body: JSON.stringify({ english_query: query }), 
        });
        
        const data = await response.json();

        // Check for HTTP errors or application-level errors from the backend.
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Compilation failed');
        }
        
        displayOutput(data);
        showToast('Compilation Successful', 'SQL query generated successfully', 'success');

    } catch (error) {
        // --- *** MODIFICATION 4: Show REAL errors, not demo data *** ---
        console.error('Fetch Error:', error);
        displayOutput({ error: error.message }); // Display the actual error message
        showToast('Error', error.message, 'error');
    } finally {
        // Reset loading state regardless of success or failure.
        isLoading = false;
        updateCompileButton();
        setLoadingState(false);
    }
}

// Visually toggles the compile button to indicate loading.
function setLoadingState(loading) {
    const compileBtn = document.getElementById('compile-btn');
    const btnIcon = compileBtn.querySelector('[data-lucide]');
    const btnText = compileBtn.querySelector('.btn-text');
    
    if (loading) {
        btnIcon.setAttribute('data-lucide', 'loader-2');
        btnIcon.classList.add('btn-loading');
        btnText.textContent = 'Compiling...';
    } else {
        btnIcon.setAttribute('data-lucide', 'play');
        btnIcon.classList.remove('btn-loading');
        btnText.textContent = 'Compile Query';
    }
    
    // Re-create icons to render the new Lucide icon.
    lucide.createIcons();
}

// Clears all output sections and hides the error card.
function clearOutput() {
    document.getElementById('error-card').style.display = 'none';
    document.getElementById('tokens-output').innerHTML = '<p class="empty-state">No output yet</p>';
    document.getElementById('tree-output').innerHTML = '<p class="empty-state">No output yet</p>';
    document.getElementById('sql-output').innerHTML = '<p class="empty-state">No output yet</p>';
    document.getElementById('result-output').innerHTML = '<p class="empty-state">No output yet</p>';
}

// Renders the compilation results (tokens, AST, SQL, execution data).
// Renders the compilation results (tokens, AST, SQL, execution data).
// Renders the compilation results (tokens, AST, SQL, execution data).
// Renders the compilation results (tokens, AST, SQL, execution data).
// Renders the compilation results (tokens, AST, SQL, execution data).
function displayOutput(data) {
    // ... (Error, Tokens, Parse Tree, SQL display logic remain the same) ...

    // Display Generated SQL.
    if (data.sql) {
        const sqlOutput = document.getElementById('sql-output');
        sqlOutput.innerHTML = `<pre class="code-block">${escapeHtml(data.sql)}</pre>`;
    }
    
    // 3. *** FINAL EXECUTION RESULT RENDERING FIX ***
    const resultOutput = document.getElementById('result-output');
    
    // Clear the card's inner content first (removing the 'No output yet' tag)
    resultOutput.innerHTML = '';

    if (data.data) {
        let outputData = data.data; 
        let outputContent = '';

        // Handle empty array (SELECT query returned 0 rows)
        if (Array.isArray(outputData) && outputData.length === 0 && !data.message) {
            outputContent = '<p class="empty-state" style="font-weight: 600; color: #ff8c00;">Query successful, 0 rows returned.</p>';
        } 
        // Handle DML (UPDATE/DELETE) with Status Message
        else if (data.message) {
            showToast('DML Status', data.message.replace(/\*\*/g, ''), 'success');
            outputContent = `
                <p class="empty-state">Status: ${data.message}</p>
                ${data.data.length > 0 ? `<p class="empty-state" style="margin-top: 10px;">Showing table: ${data.table_shown}</p>` : ''}
                <pre class="code-block">${escapeHtml(JSON.stringify(outputData, null, 2))}</pre>
            `;
        } 
        // Standard SELECT query result (Array with content)
        else {
            // CRITICALLY: Just force the data into the pre block.
            outputContent = `<pre class="code-block">${escapeHtml(JSON.stringify(outputData, null, 2))}</pre>`;
        }
        
        // ** Final action: Use appendChild for reliability **
        // Create a temporary div to hold the content and append it.
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = outputContent;
        resultOutput.appendChild(tempDiv.firstChild);

    } else {
         // If data.data is explicitly null (shouldn't happen on success), show error.
         resultOutput.innerHTML = '<p class="empty-state" style="color: red;">Error: Backend returned success but no data field.</p>';
    }
}

// Sanitizes HTML input to prevent XSS attacks when displaying code/text.
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}