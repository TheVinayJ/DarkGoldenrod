// Taken from Django Lab Instructions

import { marked } from "marked"; // Import the markdown converter

// Handle Markdown conversion and rendering
document.getElementById('convert-btn').addEventListener('click', e => {
  e.preventDefault();   // Prevents native functionality for this event
  const markdownText = document.getElementById('markdown-editor').value;
  const htmlOutput = marked(markdownText); // Convert markdown to HTML
  document.getElementById('markdown-output').innerHTML = htmlOutput; // Add the generated HTML code to the output div element
});