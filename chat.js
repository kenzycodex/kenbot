document.addEventListener('DOMContentLoaded', async () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const messagesContainer = document.getElementById('messages');
    const scrollDownIcon = document.getElementById('scroll-down-icon');

    const email = localStorage.getItem('email');
    let username = 'Guest';
    let profilePic = './images/1.png';

    // Fetch user profile
    if (email) {
        try {
            const response = await fetch(`/getUserProfile?email=${encodeURIComponent(email)}`);
            if (response.ok) {
                const data = await response.json();
                username = data.username || 'Guest';
                if (data.profilePicFilename) {
                    profilePic = `./${data.profilePicFilename}`;
                }
            } else {
                console.error('Failed to fetch user profile:', response.statusText);
            }
        } catch (error) {
            console.error('Error fetching user profile:', error);
        }
    }

    appendMessage('KenBot', `Welcome, ${username}!`, 'bot-message');

    // Function to scroll to the bottom of the chat box smoothly
    function scrollToBottom() {
        const chatBox = document.getElementById('chat-box');
        const lastMessage = chatBox.lastElementChild;
        if (lastMessage) {
            lastMessage.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }

    // Event listener for the scroll down icon
    scrollDownIcon.addEventListener('click', () => {
        scrollToBottom();
    });

    // Initial scroll to bottom
    scrollToBottom();

    // Event listener for form submission (sending user message)
    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const messageText = userInput.value.trim();
        if (messageText === '') return;

        // Disable the send button while processing the message
        chatForm.querySelector('button[type="submit"]').disabled = true;
        chatForm.querySelector('button[type="submit"]').style.opacity = 0.5;

        appendMessage('You', messageText, 'user-message');
        userInput.value = '';

        try {
            // Display loading indicator
            const loadingMessage = appendLoadingMessage();

            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `query=${encodeURIComponent(messageText)}`
            });

            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }

            const data = await response.json();
            messagesContainer.removeChild(loadingMessage); // Remove loading indicator
            appendMessage('KenBot', data.response, 'bot-message');
            scrollToBottom(); // Scroll to bottom after appending bot's response
        } catch (error) {
            console.error('Error:', error);
            appendMessage('KenBot', 'Sorry, something went wrong. Please try again later.', 'bot-message');
            scrollToBottom(); // Scroll to bottom even if there's an error message
        } finally {
            // Re-enable the send button after processing the message
            chatForm.querySelector('button[type="submit"]').disabled = false;
            chatForm.querySelector('button[type="submit"]').style.opacity = 1;
        }
    });

    // Function to append a message to the chat UI
    function appendMessage(sender, text, messageClass) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', messageClass);

        const profilePicElement = document.createElement('img');
        profilePicElement.classList.add('profile-pic');
        profilePicElement.src = sender === 'You' ? profilePic : './images/KenBot-logo.png';

        messageElement.appendChild(profilePicElement);
        messageElement.innerHTML += `<span>${text}</span>`;
        messagesContainer.appendChild(messageElement);

        // After appending message, scroll to bottom if not manually scrolled up
        if (!isManuallyScrolledUp()) {
            scrollToBottom();
        }
    }

    // Function to append a loading message (simulated)
    function appendLoadingMessage() {
        const loadingMessage = document.createElement('div');
        loadingMessage.classList.add('message', 'loading-message', 'bot-message'); // Ensure 'bot-message' class is added

        const loadingBubble = document.createElement('div');
        loadingBubble.classList.add('loading-bubble');
        loadingBubble.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';

        loadingMessage.appendChild(loadingBubble);
        messagesContainer.appendChild(loadingMessage);

        // After appending loading message, scroll to bottom if not manually scrolled up
        if (!isManuallyScrolledUp()) {
            scrollToBottom();
        }

        return loadingMessage; // Return the loading message element
    }

    // Function to check if the chat box is manually scrolled up
    function isManuallyScrolledUp() {
        // Calculate if scrolled to the bottom (considering a small threshold)
        return messagesContainer.scrollTop + messagesContainer.clientHeight < messagesContainer.scrollHeight - 20;
    }
});