// Function to handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const next = document.getElementById('next').value;
    
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = ''; // Clear previous errors
    
    try {
        const response = await fetch('/api/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({ email, password, next }),
            credentials: 'include', // Include cookies
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Redirect to 'next' URL or default
            const redirectUrl = data.next || '/';
            window.location.href = redirectUrl;
        } else {
            // Display error messages
            errorMessage.textContent = data.detail || 'Login failed. Please try again.';
        }
    } catch (error) {
        console.error('Error during login:', error);
        errorMessage.textContent = 'An error occurred. Please try again later.';
    }
}

// Function to handle signup
async function handleSignup(event) {
    event.preventDefault();
    
    const displayName = document.getElementById('display_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const next = document.getElementById('next').value;
    
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = ''; // Clear previous errors
    
    if (password !== confirmPassword) {
        errorMessage.textContent = 'Passwords do not match.';
        return;
    }
    
    try {
        const response = await fetch('/api/signup/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({ display_name: displayName, email, password, confirm_password: confirmPassword, next }),
            credentials: 'include', // Include cookies
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Redirect to 'next' URL or default
            const redirectUrl = data.next || '/';
            window.location.href = redirectUrl;
        } else {
            // Display error messages
            // Handle specific field errors if provided
            if (data.email) {
                errorMessage.textContent = data.email.join(' ');
            } else if (data.display_name) {
                errorMessage.textContent = data.display_name.join(' ');
            } else {
                errorMessage.textContent = 'Signup failed. Please check your inputs.';
            }
        }
    } catch (error) {
        console.error('Error during signup:', error);
        errorMessage.textContent = 'An error occurred. Please try again later.';
    }
}

// Function to handle logout
async function handleLogout() {
    try {
        const response = await fetch('/api/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            credentials: 'include', // Include cookies
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Redirect to login page
            window.location.href = '/login.html';
        } else {
            alert('Logout failed. Please try again.');
        }
    } catch (error) {
        console.error('Error during logout:', error);
        alert('An error occurred. Please try again later.');
    }
}

// Function to check authentication
async function checkAuth() {
    try {
        const response = await fetch('/api/user-info/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Include cookies
        });
        
        return response.ok; // true if authenticated
    } catch (error) {
        console.error('Error checking authentication:', error);
        return false;
    }
}

// Function to get CSRF token from cookies
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return '';
}

// Attach event listeners
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
    
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
});