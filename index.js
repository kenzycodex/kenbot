const signupForm = document.getElementById('signup-form');
const signupError = document.getElementById('signup-error');
const signupSuccess = document.getElementById('signup-success');
const passwordField = document.getElementById('password');
const confirmPasswordField = document.getElementById('confirm-password');
const togglePassword = document.getElementById('toggle-password');
const toggleConfirmPassword = document.getElementById('toggle-confirm-password');
const profilePicInput = document.getElementById('profile-pic-input');
const profilePic = document.getElementById('profile-pic');
const profilePicIcon = document.getElementById('profile-pic-icon');
const passwordStrengthText = document.getElementById('password-strength');
const passwordMatch = document.getElementById('password-match');

// Profile Picture Handling
profilePicIcon.addEventListener('click', () => {
    profilePicInput.click();
});

profilePic.addEventListener('click', () => {
    profilePicInput.click();
});

profilePicInput.addEventListener('change', () => {
    const file = profilePicInput.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = () => {
            profilePic.src = reader.result;
            profilePic.style.display = 'block';
            profilePicIcon.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
});

// Form Submission Handling
signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = passwordField.value;
    const confirmPassword = confirmPasswordField.value;
    const gender = document.getElementById('gender').value;
    const profilePicFile = profilePicInput.files[0];

    if (password !== confirmPassword) {
        showMessage(signupError, 'Passwords do not match.');
        return;
    }

    if (!gender) {
        showMessage(signupError, 'Please select your gender.');
        return;
    }

    if (!profilePicFile) {
        showMessage(signupError, 'Please upload a profile picture.');
        return;
    }

    const passwordStrength = validatePasswordStrength(password);
    if (!passwordStrength.isValid) {
        showMessage(signupError, passwordStrength.message);
        return;
    }

    const reader = new FileReader();
    reader.onload = async () => {
        const profilePicData = reader.result;

        const formData = {
            username,
            email,
            password,
            gender,
            profilePic: profilePicData
        };

        try {
            const response = await fetch('/saveData', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                showMessage(signupSuccess, 'Signed up successfully!');
                signupForm.reset();
                profilePic.src = "default-avatar.png";
                profilePic.style.display = 'none';
                profilePicIcon.style.display = 'block';
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000);
            } else {
                const errorData = await response.json();
                if (errorData.error) {
                    showMessage(signupError, errorData.error);
                } else {
                    showMessage(signupError, 'An unknown error occurred.');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage(signupError, 'An error occurred while processing your request.');
        }
    };

    reader.readAsDataURL(profilePicFile);
});

// Password Toggle Handling
togglePassword.addEventListener('click', () => {
    const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordField.setAttribute('type', type);
    togglePassword.classList.toggle('fa-eye-slash');
    togglePassword.classList.toggle('fa-eye');
});

toggleConfirmPassword.addEventListener('click', () => {
    const type = confirmPasswordField.getAttribute('type') === 'password' ? 'text' : 'password';
    confirmPasswordField.setAttribute('type', type);
    toggleConfirmPassword.classList.toggle('fa-eye-slash');
    toggleConfirmPassword.classList.toggle('fa-eye');
});

// Password Strength Validation
passwordField.addEventListener('input', () => {
    const passwordStrength = validatePasswordStrength(passwordField.value);
    passwordStrengthText.textContent = passwordStrength.message;
    passwordStrengthText.style.color = passwordStrength.isValid ? 'green' : 'red';
});

// Password Match Validation
confirmPasswordField.addEventListener('input', () => {
    const matchMessage = passwordField.value === confirmPasswordField.value ? 'Passwords match.' : 'Passwords do not match.';
    passwordMatch.textContent = matchMessage;
    passwordMatch.style.color = passwordField.value === confirmPasswordField.value ? 'green' : 'red';
});

// Password Strength Checker
function validatePasswordStrength(password) {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasNonalphas = /\W/.test(password);

    if (password.length < minLength) {
        return { isValid: false, message: 'Password must be at least 8 characters long.' };
    }
    if (!hasUpperCase) {
        return { isValid: false, message: 'Password must have at least one uppercase letter.' };
    }
    if (!hasLowerCase) {
        return { isValid: false, message: 'Password must have at least one lowercase letter.' };
    }
    if (!hasNumbers) {
        return { isValid: false, message: 'Password must have at least one number.' };
    }
    if (!hasNonalphas) {
        return { isValid: false, message: 'Password must have at least one special character.' };
    }
    return { isValid: true, message: 'Strong password.' };
}

// Show Message Function
function showMessage(element, message) {
    element.textContent = message;
    element.classList.add('show');
    setTimeout(() => {
        element.classList.remove('show');
    }, 4000);
}
