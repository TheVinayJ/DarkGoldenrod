import { marked } from "marked"; // Import the markdown converter

console.log("markdown-editor.js loaded");

// Step 1: Create a custom renderer
const renderer = new marked.Renderer();

renderer.image = function (href, title, text) {
  // Check if href is an object with an href property
  if (href && typeof href.href === "string") {
    const width = 300; // Desired width in pixels
    const height = 200; // Desired height in pixels

    // Build the image HTML with fixed dimensions
    let img = `<br><img src="${href.href}" alt="${text}" width="${width}" height="${height}"`;

    if (title) {
      img += ` title="${title}"`;
    }

    img += " /><br>";

    return img;
  } else {
    console.error("Invalid href passed to renderer.image: ", href);
    return ""; // Return an empty string if href is not valid
  }
};

// Step 2: Configure marked to use the custom renderer
marked.setOptions({
  renderer: renderer,
  // You can include other options here as needed
});

// Handle Markdown conversion and rendering for the Create Post page
const convertBtn = document.getElementById('convert-btn');

if (convertBtn) {
  convertBtn.addEventListener('click', e => {
    e.preventDefault(); // Prevent the default form submission
    const markdownText = document.getElementById('markdown-editor').value;
    const htmlOutput = marked(markdownText); // Convert markdown to HTML using the custom renderer
    document.getElementById('markdown-output').innerHTML = htmlOutput; // Display the HTML
    console.log("Markdown converted for create post");
  });
}

// Function to convert markdown in specified elements
function convertMarkdownInElements(selector) {
  const markdownElements = document.querySelectorAll(selector);
  console.log(`Found ${markdownElements.length} markdown elements in selector "${selector}"`);

  markdownElements.forEach(function(element) {
    const markdownText = element.textContent.trim(); // Get the raw markdown text
    const htmlContent = marked(markdownText); // Convert markdown to HTML using the custom renderer
    element.innerHTML = htmlContent; // Replace the markdown with HTML content
    console.log("Markdown converted for a feed post");
    console.log(`Markdown: ${markdownText}`);
    console.log(`HTML: ${htmlContent}`);
  });
}

// Handle Markdown rendering for the Feed page
document.addEventListener('DOMContentLoaded', function() {
  console.log("DOM fully loaded and parsed");

  // Convert markdown in elements with class "markdown-output"
  convertMarkdownInElements('.markdown-output');

  // Convert markdown in elements with class "post-content"
  convertMarkdownInElements('.post-content');
});