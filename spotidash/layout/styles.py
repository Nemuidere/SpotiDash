STYLES = {
    "bg": "#121212",
    "card_bg": "#1E1E1E",
    "accent": "#4A90D9",
    "text": "#F0F0F0",
    "text_muted": "#B0B0B0",
    "border_radius": "12px",
    "spacing": "20px",
}

GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body {
    margin: 0 !important;
    padding: 0 !important;
    background-color: #121212;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    color: #F0F0F0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    min-height: 100vh;
}

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #121212;
}

::-webkit-scrollbar-thumb {
    background: #4A90D9;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #5BA0E9;
}

a {
    color: #4A90D9;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
"""
