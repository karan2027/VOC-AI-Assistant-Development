// JS Logic for Sketch-based Visual Voice Assistant UI with Code Block Formatting

document.addEventListener('DOMContentLoaded', () => {
    const promptForm = document.getElementById('promptForm');
    const userInput = document.getElementById('userInput');
    const chatContainer = document.getElementById('chatContainer');
    const welcomeBanner = document.getElementById('welcomeBanner');
    const statusBadge = document.getElementById('statusBadge');
    const statusText = document.getElementById('statusText');
    const botAvatarBtn = document.getElementById('botAvatarBtn');
    const voiceCardBox = document.getElementById('voiceCardBox');
    const newChatBtn = document.getElementById('newChatBtn');

    let isListening = false;

    // Configure Marked JS with Highlight.js
    if (window.marked && window.hljs) {
        marked.setOptions({
            highlight: function(code, lang) {
                const language = (lang && hljs.getLanguage(lang)) ? lang : 'plaintext';
                return hljs.highlight(code, { language }).value;
            },
            langPrefix: 'hljs language-',
            breaks: true
        });
    }

    // Focus text box on load
    if (userInput) userInput.focus();

    // 1. Text Form Submission Handler
    if (promptForm) {
        promptForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = userInput.value.trim();
            if (!text) return;

            // Hide welcome card if present
            if (welcomeBanner) welcomeBanner.style.display = 'none';

            // Append User Message to Left Chat History
            appendChatEntry('USER', text);
            userInput.value = '';

            // Set state to Thinking
            setStatus('thinking', 'Thinking...');

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });

                const data = await response.json();

                if (data.status === 'success' && data.response) {
                    setStatus('speaking', 'Speaking...');
                    appendChatEntry('AI', data.response);
                    setTimeout(() => setStatus('idle', 'System Ready'), 2000);
                } else {
                    appendChatEntry('AI', 'Sorry, I could not process your request.');
                    setStatus('idle', 'System Ready');
                }
            } catch (err) {
                console.error('API Error:', err);
                appendChatEntry('AI', 'Error communicating with server.');
                setStatus('idle', 'System Ready');
            }
        });
    }

    // Allow Enter key to submit text area, Shift+Enter for new line
    if (userInput) {
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                promptForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    // 2. Click Bot Photo / Avatar to Start Voice Recording
    if (botAvatarBtn) {
        botAvatarBtn.addEventListener('click', async () => {
            if (isListening) return;

            isListening = true;
            botAvatarBtn.classList.add('active');
            voiceCardBox.classList.add('listening');
            setStatus('listening', 'Listening...');

            try {
                const response = await fetch('/api/listen', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                const data = await response.json();

                // Stop visual listening state
                botAvatarBtn.classList.remove('active');
                voiceCardBox.classList.remove('listening');
                isListening = false;

                if (data.status === 'success' && data.user_text) {
                    if (welcomeBanner) welcomeBanner.style.display = 'none';

                    appendChatEntry('USER', data.user_text);

                    if (data.response) {
                        setStatus('speaking', 'Speaking...');
                        appendChatEntry('AI', data.response);
                        setTimeout(() => setStatus('idle', 'System Ready'), 2000);
                    } else {
                        setStatus('idle', 'System Ready');
                    }
                } else {
                    setStatus('idle', 'System Ready');
                }
            } catch (err) {
                console.error('Speech Listening Error:', err);
                botAvatarBtn.classList.remove('active');
                voiceCardBox.classList.remove('listening');
                isListening = false;
                setStatus('idle', 'System Ready');
            }
        });
    }

    // 3. Clear Session Handler
    if (newChatBtn) {
        newChatBtn.addEventListener('click', async () => {
            chatContainer.innerHTML = `
                <div class="welcome-card" id="welcomeBanner">
                    <div class="bot-icon-small"><i class="fa-solid fa-robot"></i></div>
                    <h3>Assistant of Karan</h3>
                    <p>Welcome! Click the <b>VOICE</b> Bot Photo on the right to start speaking, or type your message in the <b>TEXT</b> box below!</p>
                </div>
            `;
            try {
                await fetch('/api/clear', { method: 'POST' });
            } catch (e) {}
        });
    }

    // 4. Stop Voice / Mute Speech Handler
    const stopSpeechBtn = document.getElementById('stopSpeechBtn');
    if (stopSpeechBtn) {
        stopSpeechBtn.addEventListener('click', async () => {
            try {
                setStatus('idle', 'Voice Stopped');
                await fetch('/api/stop_speech', { method: 'POST' });
            } catch (e) {
                console.error('Stop speech error:', e);
            }
        });
    }

    // Helper: Append Chat Entry to Left Stream (AI: ... / USER: ...)
    function appendChatEntry(speaker, text) {
        const entry = document.createElement('div');
        entry.className = `chat-entry ${speaker.toLowerCase()}`;

        const tag = document.createElement('div');
        tag.className = 'chat-tag';
        tag.textContent = speaker === 'USER' ? 'USER:' : 'AI:';

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';

        if (speaker === 'USER') {
            bubble.textContent = text;
        } else {
            // Render AI Markdown & Formatted Code Blocks
            if (window.marked) {
                bubble.innerHTML = marked.parse(text);
                formatCodeBlocks(bubble);
            } else {
                bubble.textContent = text;
            }
        }

        entry.appendChild(tag);
        entry.appendChild(bubble);
        chatContainer.appendChild(entry);

        // Auto scroll left stream
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Helper: Post-process Code Blocks with Header & Copy Button
    function formatCodeBlocks(container) {
        const preElements = container.querySelectorAll('pre');
        preElements.forEach((pre) => {
            const codeEl = pre.querySelector('code');
            if (!codeEl) return;

            // Determine language class
            let lang = 'code';
            codeEl.classList.forEach(cls => {
                if (cls.startsWith('language-')) {
                    lang = cls.replace('language-', '').toUpperCase();
                } else if (cls.startsWith('hljs') && cls.includes('language-')) {
                    const match = cls.match(/language-([a-zA-Z0-9_\-]+)/);
                    if (match) lang = match[1].toUpperCase();
                }
            });

            // Wrap in styled IDE container
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-container';

            const header = document.createElement('div');
            header.className = 'code-header';
            header.innerHTML = `
                <span class="code-lang-label"><i class="fa-solid fa-code"></i> ${lang}</span>
                <button class="copy-code-btn" type="button" onclick="copyCode(this)">
                    <i class="fa-regular fa-copy"></i> Copy
                </button>
            `;

            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(header);
            wrapper.appendChild(pre);
        });

        // Trigger syntax highlighting
        if (window.hljs) {
            container.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    }

    // Helper: Set System Status Pill
    function setStatus(state, text) {
        if (statusBadge) statusBadge.className = `status-pill ${state}`;
        if (statusText) statusText.textContent = text;
    }

    // Global Copy Code Helper
    window.copyCode = function(btn) {
        const wrapper = btn.closest('.code-block-container');
        if (!wrapper) return;
        const codeEl = wrapper.querySelector('code');
        if (!codeEl) return;

        const codeText = codeEl.innerText;
        navigator.clipboard.writeText(codeText).then(() => {
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                btn.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Copy failed:', err);
        });
    };

    // Global Quick Command Helper
    window.sendQuickCommand = function(cmd) {
        if (userInput) {
            userInput.value = cmd;
            promptForm.dispatchEvent(new Event('submit'));
        }
    };
});
