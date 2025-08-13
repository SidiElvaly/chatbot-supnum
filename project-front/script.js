document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const themeToggle = document.getElementById('theme-toggle');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const historyToggle = document.getElementById('history-toggle');
    const historyPanel = document.getElementById('history-panel');
    const closeHistory = document.getElementById('close-history');
    const mobileOverlay = document.getElementById('mobile-overlay');
    const conversationHistory = document.getElementById('conversation-history');
    const historyList = document.getElementById('history-list');
    const languageSelector = document.getElementById('language-selector');
    
    // Configuration
    const API_ENDPOINT = 'http://localhost:8002/chat';
    let currentLang = 'en'; // Default language
    
    // Conversation state
    let currentConversation = [];
    let conversations = [];
    let currentConvoId = null;
    
    // Set current time in welcome message
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Initialize with sample history
    initializeSampleHistory();
    
    // Theme toggle functionality
    themeToggle.addEventListener('click', function() {
        document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    });
    
    // Check for saved theme preference
    if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
    
    // Language selector functionality
    languageSelector.addEventListener('change', function(e) {
        currentLang = e.target.value;
        updateUILanguage();
    });
    
    // Update UI based on selected language
    function updateUILanguage() {
        // RTL support for Arabic
        if (currentLang === 'ar') {
            document.getElementById("chat-messages").dir = 'rtl';
            document.getElementById("message-input").dir = 'rtl';
            document.body.classList.add('rtl');
        } else {
            document.getElementById("chat-messages").dir = 'ltr';
            document.getElementById("message-input").dir = 'ltr';
            document.body.classList.remove('rtl');
        }
        
        // Update input placeholder based on language
        updatePlaceholderText();
    }
    
    // Update input placeholder text
    function updatePlaceholderText() {
        const placeholders = {
            'en': 'Type your message here...',
            'fr': 'Tapez votre message ici...',
            'ar': 'اكتب رسالتك هنا...'
        };
        messageInput.placeholder = placeholders[currentLang] || placeholders['en'];
    }
    
    // Sidebar toggle for mobile
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('hidden');
        mobileOverlay.classList.toggle('hidden');
    });
    
    // History toggle
    historyToggle.addEventListener('click', function() {
        historyPanel.classList.toggle('hidden');
        mobileOverlay.classList.toggle('hidden');
    });
    
    // Close history panel
    closeHistory.addEventListener('click', function() {
        historyPanel.classList.add('hidden');
        mobileOverlay.classList.add('hidden');
    });
    
    // Close panels when clicking on overlay
    mobileOverlay.addEventListener('click', function() {
        sidebar.classList.add('hidden');
        historyPanel.classList.add('hidden');
        mobileOverlay.classList.add('hidden');
    });
    
    // Handle form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        
        if (message) {
            // Add user message to chat
            addMessage(message, 'user');
            currentConversation.push({ text: message, sender: 'user', time: new Date() });
            messageInput.value = '';
            
            // Simulate bot typing
            const typingDiv = simulateTyping();
            
            try {
                // Call the backend API
                const response = await fetchBackend(message);
                
                // Remove typing indicator
                chatMessages.removeChild(typingDiv);
                
                // Add bot response to chat
                addMessage(response.answer, 'bot');
                currentConversation.push({ text: response.answer, sender: 'bot', time: new Date() });
                
                // Update conversation history
                updateHistory();
            } catch (error) {
                // Remove typing indicator
                chatMessages.removeChild(typingDiv);
                
                // Show error message in current language
                const errorMessages = {
                    'en': "Sorry, I'm having trouble connecting to the server. Please try again later.",
                    'fr': "Désolé, je rencontre des problèmes pour me connecter au serveur. Veuillez réessayer plus tard.",
                    'ar': "عذرًا، أواجه مشكلة في الاتصال بالخادم. يرجى المحاولة مرة أخرى لاحقًا."
                };
                const errorMessage = errorMessages[currentLang] || errorMessages['en'];
                addMessage(errorMessage, 'bot');
                currentConversation.push({ text: errorMessage, sender: 'bot', time: new Date() });
                
                console.error('API Error:', error);
            }
        }
    });
    
    // Fetch response from backend with language parameter
    async function fetchBackend(message) {
        const url = `${API_ENDPOINT}?question=${encodeURIComponent(message)}&lang=${currentLang}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // Add a message to the chat with RTL support
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('flex', 'animate-fade-in');
        
        const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        if (sender === 'user') {
            messageDiv.classList.add('justify-end');
            messageDiv.innerHTML = `
                <div class="max-w-xs md:max-w-md lg:max-w-lg bg-primary-600 dark:bg-primary-700 text-white rounded-lg p-3 ${currentLang === 'ar' ? 'text-right' : ''}">
                    <p>${text}</p>
                    <p class="text-xs text-primary-200 dark:text-primary-300 mt-2">${timeString}</p>
                </div>
            `;
        } else {
            messageDiv.classList.add('justify-start');
            // Preserve newlines in bot responses
            const formattedText = text.replace(/\n/g, '<br>');
            messageDiv.innerHTML = `
                <div class="max-w-xs md:max-w-md lg:max-w-lg bg-primary-100 dark:bg-primary-900/50 rounded-lg p-3 ${currentLang === 'ar' ? 'text-right' : ''}">
                    <p>${formattedText}</p>
                    <p class="text-xs text-secondary-500 dark:text-secondary-400 mt-2">${timeString}</p>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Simulate bot typing
    function simulateTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('flex', 'justify-start', 'animate-fade-in');
        typingDiv.innerHTML = `
            <div class="bg-primary-100 dark:bg-primary-900/50 rounded-lg p-3">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-secondary-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    <div class="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return typingDiv;
    }
    
    // Initialize with sample conversation history
    function initializeSampleHistory() {
        conversations = [];
        renderConversationHistory();
    }
    
    // Render conversation history in both sidebars
    function renderConversationHistory() {
        // Clear existing history
        conversationHistory.innerHTML = '';
        historyList.innerHTML = '';
        
        // Sort conversations by most recent
        conversations.sort((a, b) => {
            const lastMsgA = a.messages[a.messages.length - 1]?.time || new Date(0);
            const lastMsgB = b.messages[b.messages.length - 1]?.time || new Date(0);
            return lastMsgB - lastMsgA;
        });
        
        // Add conversations to both panels
        conversations.forEach(convo => {
            const lastMessage = convo.messages[convo.messages.length - 1];
            const timeString = lastMessage.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const dateString = lastMessage.time.toLocaleDateString();
            
            // Sidebar preview
            const previewItem = document.createElement('li');
            previewItem.innerHTML = `
                <button class="w-full text-left px-3 py-2 rounded hover:bg-secondary-100 dark:hover:bg-secondary-700 transition truncate conversation-item ${currentConvoId === convo.id ? 'bg-primary-100 dark:bg-primary-900/50' : ''}" data-id="${convo.id}">
                    <span class="font-medium">${convo.title}</span>
                    <span class="block text-xs text-secondary-500 dark:text-secondary-400 truncate">${convo.preview}</span>
                </button>
            `;
            conversationHistory.appendChild(previewItem);
            
            // History panel full item
            const historyItem = document.createElement('li');
            historyItem.innerHTML = `
                <div class="p-3 rounded-lg hover:bg-secondary-100 dark:hover:bg-secondary-700 transition cursor-pointer conversation-item ${currentConvoId === convo.id ? 'bg-primary-50 dark:bg-primary-900/30' : ''}" data-id="${convo.id}">
                    <h3 class="font-medium">${convo.title}</h3>
                    <p class="text-sm text-secondary-500 dark:text-secondary-400 truncate">${convo.preview}</p>
                    <div class="flex justify-between items-center mt-1">
                        <p class="text-xs text-secondary-400 dark:text-secondary-500">${timeString}</p>
                        <p class="text-xs text-secondary-400 dark:text-secondary-500">${dateString}</p>
                    </div>
                </div>
            `;
            historyList.appendChild(historyItem);
        });
        
        // Add click handlers to conversation items
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', function() {
                const convoId = parseInt(this.getAttribute('data-id'));
                loadConversation(convoId);
                
                // Close panels on mobile
                sidebar.classList.add('hidden');
                historyPanel.classList.add('hidden');
                mobileOverlay.classList.add('hidden');
            });
        });
    }
    
    // Load a conversation into the chat
    function loadConversation(id) {
        const conversation = conversations.find(c => c.id === id);
        if (!conversation) return;
        
        currentConvoId = id;
        
        // Clear current chat
        chatMessages.innerHTML = '';
        currentConversation = [];
        
        // Add welcome message
        const welcomeDiv = document.createElement('div');
        welcomeDiv.classList.add('flex', 'justify-start');
        welcomeDiv.innerHTML = `
            <div class="max-w-xs md:max-w-md lg:max-w-lg bg-primary-100 dark:bg-primary-900/50 rounded-lg p-3">
                <p>Continuing previous conversation about "${conversation.title}"</p>
                <p class="text-xs text-secondary-500 dark:text-secondary-400 mt-2">${conversation.messages[0].time.toLocaleDateString()}</p>
            </div>
        `;
        chatMessages.appendChild(welcomeDiv);
        
        // Add conversation messages
        conversation.messages.forEach(msg => {
            addMessage(msg.text, msg.sender);
            currentConversation.push(msg);
        });
        
        // Re-render history to update active state
        renderConversationHistory();
    }
    
    // Update the conversation history
    function updateHistory() {
        if (currentConversation.length > 0) {
            const lastUserMessage = currentConversation.filter(m => m.sender === 'user').slice(-1)[0];
            const lastMessage = currentConversation.slice(-1)[0];
            
            if (lastUserMessage) {
                const preview = lastUserMessage.text.length > 30 
                    ? lastUserMessage.text.substring(0, 30) + '...' 
                    : lastUserMessage.text;
                
                // Create new conversation if none exists
                if (!currentConvoId) {
                    const newConvo = {
                        id: Date.now(),
                        title: lastUserMessage.text.length > 20 
                            ? lastUserMessage.text.substring(0, 20) + '...' 
                            : lastUserMessage.text,
                        preview: preview,
                        messages: [...currentConversation]
                    };
                    conversations.unshift(newConvo);
                    currentConvoId = newConvo.id;
                } else {
                    // Update existing conversation
                    const convo = conversations.find(c => c.id === currentConvoId);
                    if (convo) {
                        convo.messages = [...currentConversation];
                        convo.preview = preview;
                    }
                }
                
                renderConversationHistory();
            }
        }
    }
    
    // Enable Enter key to submit, Shift+Enter for new line
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Initialize UI language
    updateUILanguage();
});

