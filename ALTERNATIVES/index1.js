const responses = {
    "greetings": ["Hello!", "Hi there!", "Hey!"],
    "farewells": ["Goodbye!", "Bye!", "See you later!"],
    // Add more categories and responses as needed
};

document.addEventListener('DOMContentLoaded', function () {
    const username = localStorage.getItem('username') || 'Guest';
    sendBotMessage(`Welcome, ${username}!`);

    document.getElementById('chat-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const input = document.getElementById('user-input');
        const message = input.value;
        input.value = '';

        addMessage('user', message);

        setTimeout(async function () {
            let botReply = '';
            if (message.toLowerCase().includes('google')) {
                botReply = "I'm sorry, I can't perform Google searches in this environment.";
            } else {
                botReply = await getBotReply(message);
            }
            addMessage('bot', botReply);
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
            const responsesArray = responses[category];
            return responsesArray[Math.floor(Math.random() * responsesArray.length)];
        } else {
            return await getExternalReply(message);
        }
    }

    function getCategory(message) {
        if (message.toLowerCase().includes('hello') || message.toLowerCase().includes('hi')) {
            return 'greetings';
        } else if (message.toLowerCase().includes('goodbye') || message.toLowerCase().includes('bye')) {
            return 'farewells';
        } else {
            return null;
        }
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
