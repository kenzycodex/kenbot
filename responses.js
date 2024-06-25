document.addEventListener('DOMContentLoaded', function () {
    const responses = {
        "greetings": {
            "responses": ["Hello!", "Hi there!", "Hey!"],
            "followUpQuestions": ["How can I assist you today?", "What brings you here?", "Is there anything specific you'd like to know?"]
        },
        "farewells": {
            "responses": ["Goodbye!", "Bye!", "See you later!"],
            "followUpQuestions": ["Feel free to come back anytime.", "Is there anything else I can help you with?", "Have a great day!"]
        },
        "questions": {
            "responses": ["What more can I help you with?", "Tell me more about it.", "Have you considered...?"],
            "followUpQuestions": ["Is there anything else you'd like to know?", "How can I assist you further?", "Do you need assistance with anything else?"]
        },
        // Add more categories and responses as needed
    };

    const username = localStorage.getItem('username') || 'Guest';
    sendBotMessage(`Welcome, ${username}!`);

    // Initialize session storage for storing chat history
    let chatHistory = sessionStorage.getItem('chatHistory');
    if (!chatHistory) {
        chatHistory = [];
    } else {
        chatHistory = JSON.parse(chatHistory);
        // Restore previous chat history
        chatHistory.forEach(chat => {
            addMessage(chat.sender, chat.message);
        });
    }

    document.getElementById('chat-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const input = document.getElementById('user-input');
        const message = input.value.trim(); // Trim extra spaces
        input.value = '';

        addMessage('user', message);

        // Save user message to session storage
        chatHistory.push({ sender: 'user', message });
        sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));

        setTimeout(async function () {
            let botReply = '';
            if (message.toLowerCase().includes('google')) {
                botReply = "I'm sorry, I can't perform Google searches in this environment.";
            } else {
                botReply = await getBotReply(message);
            }
            addMessage('bot', botReply);

            // Save bot reply to session storage
            chatHistory.push({ sender: 'bot', message: botReply });
            sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        }, 500);
    });

    function addMessage(sender, text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        const textElement = document.createElement('div');
        textElement.textContent = text;

        messageElement.appendChild(textElement);
        document.getElementById('messages').appendChild(messageElement);
        messageElement.scrollIntoView();
    }

    async function getBotReply(message) {
        const category = getCategory(message);
        
        if (category) {
            const responseObj = responses[category];
            const response = getRandomResponse(responseObj.responses);
            const followUpQuestion = getRandomResponse(responseObj.followUpQuestions);
            return `${response}\n\n${followUpQuestion}`;
        } else {
            const response = await getExternalReply(message);
            const followUpQuestions = generateFollowUpQuestions(message);
            return `${response}\n\n${followUpQuestions}`;
        }
    }

    function getCategory(message) {
        for (const key in responses) {
            if (responses.hasOwnProperty(key)) {
                if (message.toLowerCase().includes(key)) {
                    return key;
                }
            }
        }
        return null;
    }

    function getRandomResponse(responsesArray) {
        return responsesArray[Math.floor(Math.random() * responsesArray.length)];
    }

    function generateFollowUpQuestions(message) {
        // Generate follow-up questions based on user input
        return "What more can I help you with?";
    }

    function sendBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'bot-message');

        const textElement = document.createElement('div');
        textElement.textContent = message;

        messageElement.appendChild(textElement);
        document.getElementById('messages').appendChild(messageElement);
        messageElement.scrollIntoView();
    }

    async function getExternalReply(query) {
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            if (response.ok) {
                const result = await response.json();
                return result.summary || "I couldn't find a good answer. Can you ask something else?";
            } else {
                return "Error retrieving search results.";
            }
        } catch (error) {
            console.error('Error:', error);
            return "Error retrieving search results.";
        }
    }
});
