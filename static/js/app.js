/**
 * SYNTECXHUB AI Assistant — Web Client Controller
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

    // Initialize Markdown parser
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

    // Function Selection Handler
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
            activeModeLabel.innerHTML = `<i class="fa-solid fa-robot"></i> ${funcNames[activeFunction]}`;
        });
    });

    // Style Selection Handler
    styleSelect.addEventListener("change", (e) => {
        activeStyle = e.target.value;
        const styleText = e.target.options[e.target.selectedIndex].text;
        activeStyleLabel.textContent = `Style: ${styleText.replace(/[^a-zA-Z0-9\s()]/g, '').trim()}`;
    });

    // Sample Prompt Pills Handler
    pillBtns.forEach(pill => {
        pill.addEventListener("click", () => {
            const query = pill.dataset.query;
            userInput.value = query;
            sendMessage();
        });
    });

    // Textarea Auto-resize & Char Counter
    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
        charCounter.textContent = `${userInput.value.length} chars`;
    });

    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    btnSend.addEventListener("click", sendMessage);

    // Clear Chat History
    btnClearChat.addEventListener("click", async () => {
        try {
            await fetch("/api/clear", { method: "POST" });
            chatMessages.innerHTML = "";
            if (welcomeCard) {
                welcomeCard.style.display = "block";
                chatMessages.appendChild(welcomeCard);
            }
        } catch (err) {
            console.error("Clear chat error:", err);
        }
    });

    // Send Message Logic
    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        if (welcomeCard && welcomeCard.style.display !== "none") {
            welcomeCard.style.display = "none";
        }

        // Render User Bubble
        appendMessageBubble("user", text);
        userInput.value = "";
        userInput.style.height = "auto";
        charCounter.textContent = "0 chars";

        // Render Typing Indicator Loading Bubble
        const typingId = "typing_" + Date.now();
        appendTypingIndicator(typingId);

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    function_type: activeFunction,
                    style_type: activeStyle
                })
            });

            const data = await res.json();
            removeMessageBubble(typingId);

            if (data.success) {
                appendMessageBubble("assistant", data.response);
            } else {
                appendMessageBubble("assistant", `⚠️ **Error**: ${data.error || "Failed to generate response."}`);
            }
        } catch (err) {
            removeMessageBubble(typingId);
            appendMessageBubble("assistant", "⚠️ **Network Error**: Unable to connect to the server. Please check your connection.");
        }
    }

    function appendMessageBubble(role, rawContent) {
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

        // Add Copy Code Buttons to code blocks
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
