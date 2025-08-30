import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# -------------------- CONFIGURE GEMINI --------------------
genai.configure(api_key="AIzaSyD7t-BdtWEKIV4hafPIWtHRcerrFSKfGGI")
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

# -------------------- FETCH WEBSITE CONTENT -------------------------
def fetch_text_from_url(url):
    try:
        res = requests.get(url, timeout=60)
        soup = BeautifulSoup(res.text, "html.parser")
        # Remove script/style
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=" ")
        return ' '.join(text.split())[:8000]  # limit text to avoid token overflow
    except Exception as e:
        return f"Error fetching URL: {e}"

# -------------------- URL INPUT -------------------------
url = st.text_input("Enter a website URL", value="", key="url_box")
if url and st.session_state.page_text == "":
    with st.spinner("Fetching website content..."):
        st.session_state.page_text = fetch_text_from_url(url)
    if "Error" in st.session_state.page_text:
        st.error(st.session_state.page_text)
    else:
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
        query = f"Here is content from {url}: {st.session_state.page_text}\n\nQuestion: {prompt}\nAnswer clearly:"
        response = model.generate_content(query)
        answer = response.text

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()  # refresh to show new input box
