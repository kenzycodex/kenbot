const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const togglePassword = document.getElementById('toggle-password');
const passwordField = document.getElementById('password');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (email.trim() === '' || password.trim() === '') {
        showError('Email and password are required.');
        return;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const responseData = await response.json();

        if (response.ok) {
            localStorage.setItem('email', email); // Store the email in local storage
            showSuccess(responseData.message);
            loginForm.reset();

            // Check if username and profile picture filename are stored in session storage
            const username = sessionStorage.getItem('username') || 'Guest';
            const profilePicFilename = sessionStorage.getItem('profilePicFilename') || './images/1.png';

            // Redirect to chat.html upon successful login
            window.location.href = `chat.html?username=${encodeURIComponent(username)}&profilePicFilename=${encodeURIComponent(profilePicFilename)}`;
        } else {
            console.error("Login failed:", responseData.error);
            showError(responseData.error);
            passwordField.value = ''; // Reset the password field
        }
    } catch (error) {
        console.error('Error:', error);
        showError('An error occurred while processing your request.');
    }
});

// Password Toggle Handling
togglePassword.addEventListener('click', () => {
    const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordField.setAttribute('type', type);
    togglePassword.classList.toggle('fa-eye-slash');
    togglePassword.classList.toggle('fa-eye');
});

function showError(message) {
    loginError.textContent = message;
    loginError.classList.add('show');
    setTimeout(() => {
        loginError.classList.remove('show');
    }, 4000);
}

function showSuccess(message) {
    loginError.textContent = message; // Update the error message element to show success messages
    loginError.classList.add('success'); // Add a 'success' class for styling
    loginError.classList.add('show');
    setTimeout(() => {
        loginError.classList.remove('show');
        loginError.classList.remove('success'); // Remove the 'success' class after hiding the message
    }, 4000);
}
