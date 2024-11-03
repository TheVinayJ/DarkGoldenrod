async function checkAuthAndRedirect() {
    try {
        const response = await fetch('/api/user-info/', {
            method: 'GET',
            credentials: 'include', // Include cookies
            redirect: 'manual'      // Handle redirects manually
        });

        if (response.status === 303) {
            const location = response.headers.get('Location');
            if (location) {
                window.location.href = location;
            }
        } else if (response.status === 401) {
            // Optional: Handle 401 Unauthorized if not using 303 redirects
            const currentPath = window.location.pathname;
            window.location.href = `/login.html?next=${encodeURIComponent(currentPath)}`;
        }
        // If authenticated, allow the page to load normally
    } catch (error) {
        console.error('Error during authentication check:', error);
        const currentPath = window.location.pathname;
        window.location.href = `/login.html?next=${encodeURIComponent(currentPath)}`;
    }
}

// Call this function on protected pages
document.addEventListener('DOMContentLoaded', checkAuthAndRedirect);