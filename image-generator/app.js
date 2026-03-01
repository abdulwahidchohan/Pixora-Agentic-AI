document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const promptInput = document.getElementById('prompt-input');
    const generateBtn = document.getElementById('generate-btn');
    const themeSelect = document.getElementById('theme-select');
    const resultContainer = document.getElementById('result-container');
    const emptyState = document.querySelector('.empty-state');
    const loadingState = document.querySelector('.loading-state');
    const systemPromptHint = document.getElementById('system-prompt-hint');
    const imageWrapper = document.querySelector('.image-wrapper');
    const generatedImage = document.getElementById('generated-image');
    const downloadBtn = document.getElementById('download-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');

    // System constraints / "Hidden System Prompt"
    const SYSTEM_PROMPT = "Masterpiece, best quality, ultra detailed, highly aesthetic, 8k resolution";

    // Theme dictionary to map dropdown values to specific prompt additions
    const themes = {
        'cinematic': "cinematic lighting, dramatic shadows, volumetric light, highly detailed, movie still, film grain",
        'anime': "anime style, Studio Ghibli style, vibrant colors, cel shaded, beautiful detailed eyes",
        'photorealistic': "photorealistic, hyperrealistic, photography, 35mm lens, depth of field, sharp focus",
        'cyberpunk': "cyberpunk style, neon lights, dark alleyway, dystopian, sci-fi, reflective wet streets",
        'fantasy': "high fantasy illustration, magical, dnd art style, epic scale, intricate details, ethereal lighting",
        'watercolor': "watercolor painting, soft edges, pastel colors, artistic, wet on wet technique, brush strokes",
        'none': ""
    };

    // Auto-resize textarea
    promptInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Enable/disable button based on input
        if (this.value.trim().length > 0) {
            generateBtn.removeAttribute('disabled');
        } else {
            generateBtn.setAttribute('disabled', 'true');
        }
    });

    // Handle initial state
    generateBtn.setAttribute('disabled', 'true');

    // Enter key to submit (Shift+Enter for new line)
    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!generateBtn.hasAttribute('disabled')) {
                generateImage();
            }
        }
    });

    // Generate button click
    generateBtn.addEventListener('click', generateImage);

    function generateImage() {
        const userPrompt = promptInput.value.trim();
        if (!userPrompt) return;

        const selectedTheme = themeSelect.value;
        const themePrompt = themes[selectedTheme];

        // Construct the final prompt:
        // [System Prompt] + [User Prompt] + [Theme Prompt]
        const finalPromptParts = [SYSTEM_PROMPT, userPrompt];
        if (themePrompt) {
            finalPromptParts.push(themePrompt);
        }

        const finalPrompt = finalPromptParts.join(", ");
        
        // Update UI state to loading
        emptyState.classList.add('hidden');
        imageWrapper.classList.add('hidden');
        loadingState.classList.remove('hidden');
        
        // Also show the user the secret system prompt being used behind the scenes
        systemPromptHint.textContent = `Prompting with: "${finalPrompt}"`;

        // Pollinations URL construction
        // Adding a seed to avoid caching identical prompts during testing
        const encodedPrompt = encodeURIComponent(finalPrompt);
        const seed = Math.floor(Math.random() * 10000000);
        const width = 1024;
        const height = 1024;
        const imageURL = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=${width}&height=${height}&seed=${seed}&nologo=true`;

        // We use an actual Image object to preload the image so we don't show a broken image while loading
        const img = new Image();
        img.onload = () => {
            // Image finished loading
            generatedImage.src = imageURL;
            loadingState.classList.add('hidden');
            imageWrapper.classList.remove('hidden');
            generateBtn.innerHTML = '<span>Generate Another</span><i class="fa-solid fa-rotate-right"></i>';
        };
        
        img.onerror = () => {
            // Error handling
            loadingState.classList.add('hidden');
            emptyState.classList.remove('hidden');
            emptyState.innerHTML = '<i class="fa-solid fa-triangle-exclamation" style="color: var(--accent);"></i><p>Failed to generate image. Please try again.</p>';
            generateBtn.innerHTML = '<span>Try Again</span><i class="fa-solid fa-arrow-rotate-right"></i>';
        };

        // Start loading
        img.src = imageURL;
    }

    // Download button
    downloadBtn.addEventListener('click', async () => {
        if (!generatedImage.src) return;
        
        try {
            // We need to fetch it as a blob to trigger correct download
            // instead of just opening the image URL in a new tab
            const response = await fetch(generatedImage.src);
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = blobUrl;
            
            // Clean up prompt for filename
            let filenameSnippet = promptInput.value.trim().substring(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase();
            a.download = `lumina_${filenameSnippet || 'artwork'}_${themeSelect.value}.jpg`;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            window.URL.revokeObjectURL(blobUrl);
            
            // Show feedback
            const originalIcon = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
            setTimeout(() => {
                downloadBtn.innerHTML = originalIcon;
            }, 2000);
            
        } catch (e) {
            console.error("Download failed:", e);
            // Fallback
            window.open(generatedImage.src, '_blank');
        }
    });

    // Fullscreen button
    fullscreenBtn.addEventListener('click', () => {
        if (!generatedImage.src) return;
        
        if (imageWrapper.requestFullscreen) {
            imageWrapper.requestFullscreen();
        } else if (imageWrapper.webkitRequestFullscreen) { /* Safari */
            imageWrapper.webkitRequestFullscreen();
        } else if (imageWrapper.msRequestFullscreen) { /* IE11 */
            imageWrapper.msRequestFullscreen();
        }
    });
});
