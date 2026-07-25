/**
 * VaultofCodes AI Assistant — Frontend Client Controller
 * Developer: Chhotelal Kushwaha
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    let activeFunction = "qa";
    let activeStyle = "default";

    // DOM Elements
    const funcBtns = document.querySelectorAll(".preset-btn");
    const styleSelect = document.getElementById("style-select");
    const activeModeLabel = document.getElementById("active-mode-label");
    const activeStyleLabel = document.getElementById("active-style-label");
    const chatMessages = document.getElementById("chat-messages");
    const welcomeCard = document.getElementById("welcome-card");
    const userInput = document.getElementById("user-input");
    const btnSend = document.getElementById("btn-send");
    const btnClearChat = document.getElementById("btn-clear-chat");
    const charCounter = document.getElementById("char-counter");
    const pillBtns = document.querySelectorAll(".pill-btn");

    // Configure Marked.js
    if (typeof marked !== "undefined") {
        marked.setOptions({
            highlight: function(code, lang) {
                if (typeof hljs !== "undefined") {
                    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                    return hljs.highlight(code, { language }).value;
                }
                return code;
            },
            breaks: true
        });
    }

    // 1. AI Function Button Click Listener
    funcBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            funcBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeFunction = btn.dataset.func;
            
            const funcNames = {
                qa: "Factual Q&A",
                summarize: "Text Summarization",
                creative: "Creative Writing",
                advice: "Suggestions & Advice"
            };
            if (activeModeLabel) {
                activeModeLabel.innerHTML = `<i class="fa-solid fa-robot"></i> ${funcNames[activeFunction] || 'Factual Q&A'}`;
            }
        });
    });

    // 2. Style Selector Listener
    if (styleSelect) {
        styleSelect.addEventListener("change", (e) => {
            activeStyle = e.target.value;
            const styleText = e.target.options[e.target.selectedIndex].text;
            if (activeStyleLabel) {
                activeStyleLabel.textContent = `Style: ${styleText.replace(/[^a-zA-Z0-9\s()]/g, '').trim()}`;
            }
        });
    }

    // 3. Sample Prompt Pills Click Listener
    pillBtns.forEach(pill => {
        pill.addEventListener("click", () => {
            const query = pill.dataset.query;
            if (userInput) {
                userInput.value = query;
                sendMessage();
            }
        });
    });

    // 4. Textarea Input Listener
    if (userInput) {
        userInput.addEventListener("input", () => {
            userInput.style.height = "auto";
            userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
            if (charCounter) {
                charCounter.textContent = `${userInput.value.length} chars`;
            }
        });

        userInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // 5. Send Button Click Listener
    if (btnSend) {
        btnSend.addEventListener("click", sendMessage);
    }

    // 6. Clear Chat Button Listener
    if (btnClearChat) {
        btnClearChat.addEventListener("click", () => {
            if (chatMessages) {
                chatMessages.innerHTML = "";
                if (welcomeCard) {
                    welcomeCard.style.display = "block";
                    chatMessages.appendChild(welcomeCard);
                }
            }
        });
    }

    // Send Message Core Logic
    async function sendMessage() {
        if (!userInput) return;
        const text = userInput.value.trim();
        if (!text) return;

        if (welcomeCard) {
            welcomeCard.style.display = "none";
        }

        // Render User Bubble
        appendMessageBubble("user", text);
        userInput.value = "";
        userInput.style.height = "auto";
        if (charCounter) charCounter.textContent = "0 chars";

        // Render Typing Indicator Loading Bubble
        const typingId = "typing_" + Date.now();
        appendTypingIndicator(typingId);

        try {
            // Call AI Generation Engine
            const aiRes = await generateAIResponse(activeFunction, 'qa_concise', text);
            removeMessageBubble(typingId);

            if (aiRes && aiRes.text) {
                appendMessageBubble("assistant", aiRes.text);
            } else {
                appendMessageBubble("assistant", "⚠️ Could not generate a response. Please try again.");
            }
        } catch (err) {
            removeMessageBubble(typingId);
            appendMessageBubble("assistant", "⚠️ **Network Error**: Could not connect to Google Gemini AI. Please check your internet connection.");
        }
    }

    function appendMessageBubble(role, rawContent) {
        if (!chatMessages) return;
        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-message ${role}`;

        const avatarIcon = role === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
        
        let parsedHTML = rawContent;
        if (typeof marked !== "undefined") {
            parsedHTML = marked.parse(rawContent);
        }

        msgDiv.innerHTML = `
            <div class="msg-avatar">${avatarIcon}</div>
            <div class="msg-body">
                <div class="msg-bubble">${parsedHTML}</div>
            </div>
        `;

        // Add 1-Click Copy Code Button to code blocks
        msgDiv.querySelectorAll("pre").forEach(pre => {
            const copyBtn = document.createElement("button");
            copyBtn.className = "copy-code-btn";
            copyBtn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy';
            copyBtn.addEventListener("click", () => {
                const codeText = pre.querySelector("code") ? pre.querySelector("code").innerText : pre.innerText;
                navigator.clipboard.writeText(codeText);
                copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy';
                }, 2000);
            });
            pre.appendChild(copyBtn);
        });

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendTypingIndicator(id) {
        if (!chatMessages) return;
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-message assistant";
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-body">
                <div class="msg-bubble typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeMessageBubble(id) {
        const elem = document.getElementById(id);
        if (elem) elem.remove();
    }
});
