/**
 * VaultofCodes / Assistant High-Reasoning AI Engine
 * Powered by Google Gemini AI, Pollinations AI (Free) & Wikipedia REST API
 * Creator: Chhotelal Kushwaha
 */

const AI_FUNCTIONS = {
    qa: {
        id: 'qa',
        name: 'Factual Q&A',
        icon: 'fa-brain',
        description: 'Answers factual questions in real-time using Google Gemini AI & Live Real AI Models.',
        prompts: [{ id: 'qa_concise', name: 'Direct & Concise', tag: 'Short & Precise', tone: 'Objective, Brief', complexity: 'Low', description: 'Delivers immediate, direct answers.',
            systemPrompt: `You are Assistant, a smart and accurate AI assistant created by Chhotelal Kushwaha. Answer all questions correctly, clearly, and in a well-formatted Markdown style. For list questions, give proper numbered or bulleted lists. For factual questions, give concise, accurate, up-to-date answers.` }]
    },
    summarize: {
        id: 'summarize',
        name: 'Text Summarization',
        icon: 'fa-compress-alt',
        description: 'Distills long articles and text into bullet highlights.',
        prompts: [{ id: 'sum_bullets', name: 'Executive Bullet Points', tag: 'Key Takeaways', tone: 'Professional', complexity: 'Medium', description: 'Extracts key bullet points.',
            systemPrompt: `You are Assistant, an executive summary specialist created by Chhotelal Kushwaha. Summarize provided text clearly using bullet points.` }]
    },
    creative: {
        id: 'creative',
        name: 'Creative Content Generation',
        icon: 'fa-wand-magic-sparkles',
        description: 'Crafts engaging stories, poems, sci-fi plots, speeches, and artistic writing.',
        prompts: [{ id: 'cr_narrative', name: 'Immersive Storyteller', tag: 'Rich & Vivid', tone: 'Atmospheric', complexity: 'High', description: 'Generates vivid creative content.',
            systemPrompt: `You are Assistant, an award-winning creative writer created by Chhotelal Kushwaha. Craft imaginative stories, poems, essays, and creative content based on user requests.` }]
    },
    advice: {
        id: 'advice',
        name: 'Advice & Coaching',
        icon: 'fa-compass',
        description: 'Offers structured guidance, study strategies, and productivity hacks.',
        prompts: [{ id: 'adv_actionable', name: 'Actionable Step-by-Step', tag: 'Practical Steps', tone: 'Practical', complexity: 'Medium', description: 'Breaks advice into numbered steps.',
            systemPrompt: `You are Assistant, a practical productivity coach created by Chhotelal Kushwaha. Provide actionable advice and step-by-step guidance.` }]
    }
};

/* =====================================================================
   PROVIDER 1: Google Gemini REST API — X-goog-api-key header method
   ===================================================================== */
async function callGoogleGeminiAPI(systemPrompt, userQuery, apiKey) {
    // Collect all available keys to try
    const keysToTry = [];
    const saved = localStorage.getItem('gemini_api_key');
    if (saved && saved.trim().length > 5) keysToTry.push(saved.trim());
    if (apiKey && apiKey.trim().length > 5 && !keysToTry.includes(apiKey.trim())) keysToTry.push(apiKey.trim());
    if (typeof APP_CONFIG !== 'undefined') {
        if (APP_CONFIG.GEMINI_API_KEY && !keysToTry.includes(APP_CONFIG.GEMINI_API_KEY)) keysToTry.push(APP_CONFIG.GEMINI_API_KEY);
        if (APP_CONFIG.GEMINI_API_KEY_2 && !keysToTry.includes(APP_CONFIG.GEMINI_API_KEY_2)) keysToTry.push(APP_CONFIG.GEMINI_API_KEY_2);
        if (APP_CONFIG.GEMINI_API_KEY_3 && !keysToTry.includes(APP_CONFIG.GEMINI_API_KEY_3)) keysToTry.push(APP_CONFIG.GEMINI_API_KEY_3);
    }

    // Models to try in order (gemini-flash-latest confirmed working)
    const models = ['gemini-flash-latest', 'gemini-2.0-flash', 'gemini-1.5-flash'];

    for (const key of keysToTry) {
        for (const model of models) {
            try {
                const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-goog-api-key': key  // ✅ Exact header format from working curl
                    },
                    body: JSON.stringify({
                        contents: [{
                            parts: [{ text: `${systemPrompt}\n\nUser Question: ${userQuery}` }]
                        }]
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    const text = data.candidates?.[0]?.content?.parts?.map(p => p.text).join('\n').trim();
                    if (text && text.length > 5) return text;
                }
                // Bad key → skip to next key immediately
                if (res.status === 400 || res.status === 401 || res.status === 403) break;
                // Quota on this model → try next model
                if (res.status === 429) continue;
            } catch (e) {
                console.warn(`Gemini ${model}:`, e.message);
            }
        }
    }
    throw new Error("All Gemini keys unavailable");
}



/* =====================================================================
   PROVIDER 2: Pollinations AI — 100% FREE, No API Key, No Login
   ===================================================================== */
async function callPollinationsAI(systemPrompt, userQuery) {
    // Pollinations AI chat completions endpoint (browser-friendly, CORS enabled)
    const res = await fetch('https://text.pollinations.ai/openai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            model: 'openai-large',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userQuery }
            ],
            seed: 42
        })
    });
    if (res.ok) {
        const data = await res.json();
        const text = data.choices?.[0]?.message?.content?.trim();
        if (text && text.length > 5) return text;
    }
    // Fallback to GET endpoint (fully anonymous)
    const getUrl = `https://text.pollinations.ai/${encodeURIComponent(systemPrompt + '\n\n' + userQuery)}?model=openai&seed=42`;
    const getRes = await fetch(getUrl);
    if (getRes.ok) {
        const text = (await getRes.text()).trim();
        if (text && text.length > 5 && !text.includes('402') && !text.includes('deprecated')) return text;
    }
    throw new Error("Pollinations AI unavailable");
}

/* =====================================================================
   PROVIDER 3: OpenRouter Free AI (Mistral 7B)
   ===================================================================== */
async function callOpenRouterFreeAI(systemPrompt, userQuery) {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'HTTP-Referer': window.location.href,
            'X-Title': 'VaultofCodes AI Assistant'
        },
        body: JSON.stringify({
            model: 'mistralai/mistral-7b-instruct:free',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userQuery }
            ]
        })
    });
    if (res.ok) {
        const data = await res.json();
        const text = data.choices?.[0]?.message?.content?.trim();
        if (text && text.length > 5) return text;
    }
    throw new Error("OpenRouter error: " + res.status);
}

/* =====================================================================
   PROVIDER 4: Wikipedia Smart Search (last resort for factual questions)
   ===================================================================== */

/** Smart query rewriter — converts casual questions to Wikipedia search terms */
function buildWikipediaSearchTerm(query) {
    const q = query.toLowerCase().trim();

    // Chief Minister / CM patterns
    if (q.match(/cm\s+of\s+(\w[\w\s]+)/i) || q.match(/chief\s+minister\s+of\s+(\w[\w\s]+)/i)) {
        const m = q.match(/(?:cm|chief minister)\s+of\s+([\w\s]+?)(?:\s+india)?$/i);
        if (m) return `Chief Minister of ${m[1].trim()} state`;
    }

    // PM patterns
    if (q.match(/pm\s+of\s+(\w[\w\s]+)/i) || q.match(/prime\s+minister\s+of\s+(\w[\w\s]+)/i)) {
        const m = q.match(/(?:pm|prime minister)\s+of\s+([\w\s]+)/i);
        if (m) return `Prime Minister of ${m[1].trim()}`;
    }

    // President patterns
    if (q.match(/president\s+of\s+(\w[\w\s]+)/i)) {
        const m = q.match(/president\s+of\s+([\w\s]+)/i);
        if (m) return `President of ${m[1].trim()}`;
    }

    // List patterns → return null (Wikipedia bad for lists)
    if (q.match(/list\s+of\s+\d+\s+\w+/i) || q.match(/give me\s+\d+\s+\w+/i) || q.match(/name\s+\d+\s+\w+/i)) {
        return null; // Signal: don't use Wikipedia for list queries
    }

    // What is X patterns
    if (q.match(/what\s+is\s+(.+)/i)) {
        const m = q.match(/what\s+is\s+(.+)/i);
        return m ? m[1].replace(/[?]/g, '').trim() : query;
    }

    return query; // Default: use query as-is
}

/** Hardcoded accurate answers for common Indian political questions */
function getLocalKnowledge(query) {
    const q = query.toLowerCase();
    const localDB = {
        'cm of up': 'The current Chief Minister of **Uttar Pradesh (UP)** is **Yogi Adityanath** (Ajay Singh Bisht). He is a member of the Bharatiya Janata Party (BJP) and has been the CM since March 2017.',
        'cm of uttar pradesh': 'The current Chief Minister of **Uttar Pradesh (UP)** is **Yogi Adityanath** (Ajay Singh Bisht). He is a member of the Bharatiya Janata Party (BJP) and has been the CM since March 2017.',
        'cm of mp': 'The current Chief Minister of **Madhya Pradesh (MP)** is **Mohan Yadav**. He is a member of the Bharatiya Janata Party (BJP).',
        'cm of rajasthan': 'The current Chief Minister of **Rajasthan** is **Bhajanlal Sharma**. He is a member of the Bharatiya Janata Party (BJP).',
        'cm of gujarat': 'The current Chief Minister of **Gujarat** is **Bhupendra Patel**. He is a member of the Bharatiya Janata Party (BJP).',
        'cm of maharashtra': 'The current Chief Minister of **Maharashtra** is **Devendra Fadnavis**. He is a member of the Bharatiya Janata Party (BJP).',
        'cm of delhi': 'The current Chief Minister of **Delhi** is **Rekha Gupta**. She is a member of the Bharatiya Janata Party (BJP).',
        'cm of bihar': 'The current Chief Minister of **Bihar** is **Nitish Kumar**. He is the leader of the Janata Dal (United) party.',
        'cm of bengal': 'The current Chief Minister of **West Bengal** is **Mamata Banerjee**. She is the leader of the All India Trinamool Congress (AITC).',
        'cm of west bengal': 'The current Chief Minister of **West Bengal** is **Mamata Banerjee**. She is the leader of the All India Trinamool Congress (AITC).',
        'cm of tamil nadu': 'The current Chief Minister of **Tamil Nadu** is **M.K. Stalin**. He is the leader of the Dravida Munnetra Kazhagam (DMK).',
        'cm of karnataka': 'The current Chief Minister of **Karnataka** is **Siddaramaiah**. He is a member of the Indian National Congress (INC).',
        'cm of telangana': 'The current Chief Minister of **Telangana** is **A. Revanth Reddy**. He is a member of the Indian National Congress (INC).',
        'cm of kerala': 'The current Chief Minister of **Kerala** is **Pinarayi Vijayan**. He is a member of the Communist Party of India (Marxist).',
        'cm of punjab': 'The current Chief Minister of **Punjab** is **Bhagwant Mann**. He is a member of the Aam Aadmi Party (AAP).',
        'cm of haryana': 'The current Chief Minister of **Haryana** is **Nayab Singh Saini**. He is a member of the Bharatiya Janata Party (BJP).',
        'cm of jharkhand': 'The current Chief Minister of **Jharkhand** is **Hemant Soren**. He is a member of the Jharkhand Mukti Morcha (JMM).',
        'cm of chhattisgarh': 'The current Chief Minister of **Chhattisgarh** is **Vishnu Deo Sai**. He is a member of the Bharatiya Janata Party (BJP).',
        'cm of uttarakhand': 'The current Chief Minister of **Uttarakhand** is **Pushkar Singh Dhami**. He is a member of the Bharatiya Janata Party (BJP).',
        'cm of himachal': 'The current Chief Minister of **Himachal Pradesh** is **Sukhvinder Singh Sukhu**. He is a member of the Indian National Congress (INC).',
        'pm of india': 'The **Prime Minister of India** is **Narendra Modi**. He has been the PM since May 2014 and is the leader of the Bharatiya Janata Party (BJP).',
        'prime minister of india': 'The **Prime Minister of India** is **Narendra Modi**. He has been the PM since May 2014 and is the leader of the Bharatiya Janata Party (BJP).',
        'president of india': 'The **President of India** is **Droupadi Murmu**. She is the 15th President of India and assumed office on July 25, 2022.',
        'pm of russia': 'The **Prime Minister of Russia** is **Mikhail Mishustin**. He has been serving as PM since January 2020 and is a close ally of President Vladimir Putin.',
        'prime minister of russia': 'The **Prime Minister of Russia** is **Mikhail Mishustin**. He has been serving as PM since January 2020.',
        'president of russia': 'The **President of Russia** is **Vladimir Putin**. He has been the president since 2000 (with a brief period as PM from 2008–2012).',
        'pm of uk': 'The **Prime Minister of the United Kingdom** is **Keir Starmer**. He became PM in July 2024 after Labour won the general election.',
        'pm of usa': 'The **USA does not have a Prime Minister**. The head of state and government of the United States is the **President**, who is currently **Donald Trump** (since January 2025).',
        'president of usa': 'The **President of the United States** is **Donald Trump**. He assumed office on January 20, 2025.',
        'pm of canada': 'The **Prime Minister of Canada** is **Mark Carney**. He became PM in March 2025.',
        'pm of australia': 'The **Prime Minister of Australia** is **Anthony Albanese**. He has been PM since May 2022.',
        'pm of japan': 'The **Prime Minister of Japan** is **Sanae Takaichi**. She became PM in 2024.',
    };

    for (const [key, val] of Object.entries(localDB)) {
        if (q.includes(key)) return val;
    }
    return null;
}

/** List generator for common "list of N things" queries */
function generateLocalList(query) {
    const q = query.toLowerCase();
    const lists = {
        'bird': ['🦚 Peacock', '🦅 Eagle', '🦜 Parrot', '🦉 Owl', '🦩 Flamingo', '🐧 Penguin', '🦢 Swan', '🦆 Duck', '🕊️ Pigeon', '🐦 Sparrow', '🦋 Kingfisher', '🦃 Turkey', '🦤 Dodo', '🦜 Macaw', '🦅 Falcon'],
        'car': ['🚗 Toyota Camry', '🚗 Honda Civic', '🚗 BMW M3', '🚗 Mercedes-Benz C-Class', '🚗 Audi A4', '🚗 Ford Mustang', '🚗 Chevrolet Camaro', '🚗 Tesla Model 3', '🚗 Lamborghini Huracán', '🚗 Ferrari 488', '🚗 Porsche 911', '🚗 Rolls-Royce Phantom', '🚗 Volkswagen Golf', '🚗 Hyundai i20', '🚗 Maruti Swift'],
        'animal': ['🦁 Lion', '🐘 Elephant', '🐯 Tiger', '🦒 Giraffe', '🦓 Zebra', '🐻 Bear', '🦊 Fox', '🐺 Wolf', '🦅 Eagle', '🐬 Dolphin', '🦏 Rhinoceros', '🦛 Hippopotamus', '🐊 Crocodile', '🐍 Python Snake', '🦋 Butterfly'],
        'fruit': ['🍎 Apple', '🍌 Banana', '🍊 Orange', '🍇 Grapes', '🍓 Strawberry', '🥭 Mango', '🍍 Pineapple', '🍉 Watermelon', '🍑 Peach', '🍒 Cherry', '🥥 Coconut', '🍋 Lemon', '🍐 Pear', '🥝 Kiwi', '🫐 Blueberry'],
        'country': ['🇮🇳 India', '🇺🇸 United States', '🇨🇳 China', '🇷🇺 Russia', '🇬🇧 United Kingdom', '🇯🇵 Japan', '🇩🇪 Germany', '🇫🇷 France', '🇮🇹 Italy', '🇦🇺 Australia', '🇧🇷 Brazil', '🇨🇦 Canada', '🇰🇷 South Korea', '🇲🇽 Mexico', '🇿🇦 South Africa'],
        'flower': ['🌹 Rose', '🌻 Sunflower', '🌺 Hibiscus', '🌸 Cherry Blossom', '🌼 Daisy', '💐 Tulip', '🪷 Lotus', '🌷 Orchid', '🌿 Jasmine', '🌱 Marigold'],
        'planet': ['🪐 Mercury', '🌕 Venus', '🌍 Earth', '🔴 Mars', '🟠 Jupiter', '🪐 Saturn', '🔵 Uranus', '🌑 Neptune'],
        'programming language': ['🐍 Python', '☕ Java', '⚡ JavaScript', '🦀 C/C++', '💎 Ruby', '🐘 PHP', '🦕 TypeScript', '🔵 Kotlin', '🍎 Swift', '🏃 Go', '#️⃣ C#', '🦾 Rust', '📊 R', '🔷 Scala', '🖥️ MATLAB'],
        'vegetable': ['🥕 Carrot', '🥦 Broccoli', '🧅 Onion', '🧄 Garlic', '🍅 Tomato', '🥔 Potato', '🌽 Corn', '🥒 Cucumber', '🍆 Eggplant', '🌶️ Chili Pepper'],
        'sport': ['⚽ Football/Soccer', '🏏 Cricket', '🏀 Basketball', '🎾 Tennis', '🏊 Swimming', '🏋️ Weightlifting', '🏸 Badminton', '🏓 Table Tennis', '🎳 Bowling', '🤸 Gymnastics'],
        'state of india': [
            '1. Andhra Pradesh — Capital: Amaravati', '2. Arunachal Pradesh — Capital: Itanagar', '3. Assam — Capital: Dispur',
            '4. Bihar — Capital: Patna', '5. Chhattisgarh — Capital: Raipur', '6. Goa — Capital: Panaji',
            '7. Gujarat — Capital: Gandhinagar', '8. Haryana — Capital: Chandigarh', '9. Himachal Pradesh — Capital: Shimla',
            '10. Jharkhand — Capital: Ranchi', '11. Karnataka — Capital: Bengaluru', '12. Kerala — Capital: Thiruvananthapuram',
            '13. Madhya Pradesh — Capital: Bhopal', '14. Maharashtra — Capital: Mumbai', '15. Manipur — Capital: Imphal',
            '16. Meghalaya — Capital: Shillong', '17. Mizoram — Capital: Aizawl', '18. Nagaland — Capital: Kohima',
            '19. Odisha — Capital: Bhubaneswar', '20. Punjab — Capital: Chandigarh', '21. Rajasthan — Capital: Jaipur',
            '22. Sikkim — Capital: Gangtok', '23. Tamil Nadu — Capital: Chennai', '24. Telangana — Capital: Hyderabad',
            '25. Tripura — Capital: Agartala', '26. Uttar Pradesh — Capital: Lucknow', '27. Uttarakhand — Capital: Dehradun',
            '28. West Bengal — Capital: Kolkata'
        ]
    };

    // Find number requested
    const numMatch = q.match(/(\d+)/);
    const count = numMatch ? parseInt(numMatch[1]) : 10;

    for (const [key, items] of Object.entries(lists)) {
        if (q.includes(key)) {
            const slice = items.slice(0, count);
            return slice.join('\n');
        }
    }
    return null;
}

async function callWikipediaAPI(userQuery) {
    const searchTerm = buildWikipediaSearchTerm(userQuery);
    if (!searchTerm) throw new Error("Wikipedia not suitable for this query");

    const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(searchTerm)}&srlimit=3&format=json&origin=*`;
    const searchRes = await fetch(searchUrl, { headers: { 'Accept': 'application/json' } });
    if (!searchRes.ok) throw new Error("Wikipedia search failed: " + searchRes.status);

    const searchData = await searchRes.json();
    const topResult = searchData.query?.search?.[0];
    if (!topResult) throw new Error("No Wikipedia results");

    const extractUrl = `https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&pageids=${topResult.pageid}&format=json&origin=*`;
    const extractRes = await fetch(extractUrl, { headers: { 'Accept': 'application/json' } });
    if (!extractRes.ok) throw new Error("Wikipedia extract failed");

    const extractData = await extractRes.json();
    const page = Object.values(extractData.query?.pages || {})[0];
    const extract = page?.extract?.trim();
    if (!extract || extract.length < 30) throw new Error("Wikipedia extract empty");

    return `### ${page.title}\n\n${extract.slice(0, 1200)}`;
}

/* =====================================================================
   TEST API KEY
   ===================================================================== */
async function testGeminiApiKey(apiKey) {
    if (!apiKey) return { success: false, message: 'Please enter your Gemini API Key.' };
    try {
        await callGoogleGeminiAPI("You are a helpful assistant.", "Say hello in one sentence.", apiKey.trim());
        return { success: true, message: '🟢 Google Gemini API is ACTIVE & CONNECTED!' };
    } catch (e) {
        return { success: false, message: `🔴 Gemini Key Error: ${e.message}` };
    }
}

/* =====================================================================
   MAIN AI GENERATION ENGINE — 5-Stage Waterfall
   ===================================================================== */
async function generateAIResponse(functionId, promptId, userQuery, customApiKey = null) {
    const func = AI_FUNCTIONS[functionId] || AI_FUNCTIONS.qa;
    const sysPrompt = func.prompts[0].systemPrompt;
    const geminiKey = customApiKey
        || localStorage.getItem('gemini_api_key')
        || (typeof APP_CONFIG !== 'undefined' ? APP_CONFIG.GEMINI_API_KEY : '');

    // STAGE 1: Check local knowledge database (instant accurate results)
    const localAnswer = getLocalKnowledge(userQuery);
    if (localAnswer) {
        return { text: localAnswer, source: 'VaultofCodes Knowledge Base', apiStatus: 'success' };
    }

    // STAGE 2: Check local list generator for "list of N things" queries
    const listAnswer = generateLocalList(userQuery);
    if (listAnswer) {
        const numMatch = userQuery.match(/(\d+)/);
        const count = numMatch ? numMatch[1] : '10';
        const topic = userQuery.replace(/list|of|\d+|name|give|me|some|\?/gi, '').trim();
        return {
            text: `### List of ${count} ${topic.charAt(0).toUpperCase() + topic.slice(1)}\n\n${listAnswer}`,
            source: 'VaultofCodes Knowledge Base', apiStatus: 'success'
        };
    }

    // STAGE 3: Try Google Gemini (if API key is available)
    if (geminiKey && geminiKey.trim().length > 5) {
        try {
            const text = await callGoogleGeminiAPI(sysPrompt, userQuery, geminiKey.trim());
            return { text, source: 'Google Gemini AI', apiStatus: 'success' };
        } catch (e) {
            console.warn("Gemini failed:", e.message);
        }
    }

    // STAGE 4: Try Pollinations AI (Free, No Key)
    try {
        const text = await callPollinationsAI(sysPrompt, userQuery);
        return { text, source: 'Pollinations AI (Free)', apiStatus: 'success' };
    } catch (e) {
        console.warn("Pollinations failed:", e.message);
    }

    // STAGE 5: Try OpenRouter Free AI
    try {
        const text = await callOpenRouterFreeAI(sysPrompt, userQuery);
        return { text, source: 'OpenRouter Mistral AI', apiStatus: 'success' };
    } catch (e) {
        console.warn("OpenRouter failed:", e.message);
    }

    // STAGE 6: Wikipedia (last resort for factual queries)
    try {
        const text = await callWikipediaAPI(userQuery);
        return { text, source: 'Wikipedia Knowledge Base', apiStatus: 'success' };
    } catch (e) {
        console.warn("Wikipedia failed:", e.message);
    }

    return {
        text: `⚠️ **Unable to generate response**\n\nAll AI providers are currently unavailable.\n\n**Quick Fix:** Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) (starts with \`AIzaSy...\`) and paste it in Settings ⚙️.`,
        source: 'Assistant Engine', apiStatus: 'error'
    };
}
