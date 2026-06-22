import streamlit as st
import ollama
import sqlite3
import pandas as pd
import fitz
import os
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="NeuroSphere AI",
    page_icon="🧠",
    layout="wide"
)

# -----------------------------
# DATABASE
# -----------------------------

conn = sqlite3.connect(
    "chat_history.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats(
id INTEGER PRIMARY KEY AUTOINCREMENT,
question TEXT,
answer TEXT,
timestamp TEXT
)
""")

conn.commit()

# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("NeuroSphere AI")

model_choice = st.sidebar.selectbox(
    "Choose Model",
    [
        "llama3.1:8b",
        "qwen3:8b",
        "deepseek-r1:8b"
    ]
)

uploaded_file = st.sidebar.file_uploader(
    "Upload PDF / CSV",
    type=["pdf", "csv"]
)

# -----------------------------
# SESSION MEMORY
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# TITLE
# -----------------------------

st.title("🧠 NeuroSphere AI")

st.caption(
    "Offline Enterprise Multi-Agent Assistant"
)

# -----------------------------
# DISPLAY CHAT
# -----------------------------

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# FILE PROCESSING
# -----------------------------

context_text = ""

if uploaded_file:

    if uploaded_file.name.endswith(".pdf"):

        with open(
            uploaded_file.name,
            "wb"
        ) as f:
            f.write(uploaded_file.getbuffer())

        pdf = fitz.open(
            uploaded_file.name
        )

        for page in pdf:
            context_text += page.get_text()

    elif uploaded_file.name.endswith(".csv"):

        df = pd.read_csv(
            uploaded_file
        )

        context_text = df.head(
            50
        ).to_string()

# -----------------------------
# CHAT INPUT
# -----------------------------

prompt = st.chat_input(
    "Ask anything..."
)

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    messages = [
        {
            "role": "system",
            "content":
            """
            You are NeuroSphere AI.

            You are an advanced AI assistant.

            Answer accurately.

            Use uploaded document
            context if available.
            """
        }
    ]

    if context_text:

        messages.append(
            {
                "role": "system",
                "content":
                f"Document Context:\n{context_text}"
            }
        )

    for m in st.session_state.messages:

        messages.append(
            {
                "role": m["role"],
                "content": m["content"]
            }
        )

    with st.chat_message("assistant"):

        response_box = st.empty()

        full_response = ""

        stream = ollama.chat(
            model=model_choice,
            messages=messages,
            stream=True
        )

        for chunk in stream:

            text = chunk["message"]["content"]

            full_response += text

            response_box.markdown(
                full_response + "▌"
            )

        response_box.markdown(
            full_response
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )

    cursor.execute(
        """
        INSERT INTO chats
        (
        question,
        answer,
        timestamp
        )
        VALUES
        (
        ?, ?, ?
        )
        """,
        (
            prompt,
            full_response,
            str(datetime.now())
        )
    )

    conn.commit()

# -----------------------------
# CHAT HISTORY
# -----------------------------

st.sidebar.subheader(
    "Recent Chats"
)

history = pd.read_sql_query(
    """
    SELECT *
    FROM chats
    ORDER BY id DESC
    LIMIT 10
    """,
    conn
)

st.sidebar.dataframe(
    history,
    use_container_width=True
)
