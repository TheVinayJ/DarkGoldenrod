function getCSRFToken() {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function getAuthorId() {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('author_id='));
    return cookie ? cookie.split('=')[1] : null;
}