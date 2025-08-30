import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# -------------------- CONFIGURE GEMINI --------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash")

# -------------------- PAGE CONFIG -------------------------
st.set_page_config(page_title="Website Crawler Chatbot", page_icon="🌐", layout="centered")
st.title("🌐 Website Crawler Chatbot")
st.write("Enter a URL, I'll read it and answer your questions!")

# -------------------- STORE STATE -------------------------
if "page_text" not in st.session_state:
    st.session_state.page_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_url" not in st.session_state:
    st.session_state.last_url = ""

# -------------------- HELPER FUNCTIONS --------------------
def is_valid_url(url):
    """Check if the entered URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def fetch_text_from_url(url):
    """Fetch visible text from the given website URL."""
    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text(separator=" ")
        clean_text = ' '.join(text.split())
        return clean_text
    except Exception as e:
        return f"Error fetching URL: {e}"

def summarize_if_needed(text, max_chars=8000):
    """Summarize content if too long to fit into Gemini comfortably."""
    if len(text) <= max_chars:
        return text
    st.info("Page is large — summarizing before sending to Gemini...")
    prompt = f"Summarize this webpage content clearly in under {max_chars} characters:\n\n{text}"
    summary = model.generate_content(prompt).text
    return summary

# -------------------- URL INPUT -------------------------
url = st.text_input("Enter a website URL", value="", key="url_box")

if url:
    if not is_valid_url(url):
        st.error("Please enter a valid URL (e.g., https://example.com)")
    elif url != st.session_state.last_url:
        with st.spinner("Fetching website content..."):
            page_text = fetch_text_from_url(url)
            if page_text.startswith("Error"):
                st.error(page_text)
                st.session_state.page_text = ""
            else:
                st.session_state.page_text = summarize_if_needed(page_text)
                st.session_state.last_url = url
                st.success("Website content fetched! Now you can ask questions below.")

# -------------------- DISPLAY CHAT HISTORY -------------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Answer:** {msg['content']}")

# -------------------- CHAT INPUT -------------------------
if st.session_state.page_text and (prompt := st.chat_input("Ask about this website...")):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get response from Gemini
    with st.spinner("Thinking..."):
        query = f"Here is content from {url}:\n\n{st.session_state.page_text}\n\nQuestion: {prompt}\nAnswer clearly and format nicely in markdown:"
        try:
            response = model.generate_content(query)
            answer = response.text
        except Exception as e:
            answer = f"Error getting answer: {e}"

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()  # refresh to show new input box
