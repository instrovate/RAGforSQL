import streamlit as st
import sqlite3
import os
import requests
from llama_index.core import SQLDatabase
from llama_index.llms.openai import OpenAI
from llama_index.indices.struct_store import NLSQLTableQueryEngine

st.set_page_config(page_title="RAG over SQL", page_icon="🧠")
st.title("🧠 RAG Over SQL (LlamaIndex + Streamlit + SQLite)")

# Step 1: Use uploaded or default database
uploaded_file = st.file_uploader("Upload your own SQLite .db file", type=["db"])

if uploaded_file:
    db_path = "uploaded.db"
    with open(db_path, "wb") as f:
        f.write(uploaded_file.read())
else:
    # Download sample DB from GitHub if not present
    db_path = "Instrovate_sample_employee.db"
    db_url = "https://raw.githubusercontent.com/instrovate/RAGforSQL/main/Instrovate_sample_employee.db"
    if not os.path.exists(db_path):
        r = requests.get(db_url)
        with open(db_path, "wb") as f:
            f.write(r.content)

# Optional: Preview schema
if st.checkbox("🔍 Preview database schema"):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        for table in tables:
            st.subheader(f"📄 Table: {table[0]}")
            rows = cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5").fetchall()
            columns = [desc[0] for desc in cursor.description]
            st.dataframe([dict(zip(columns, row)) for row in rows])
        conn.close()
    except Exception as e:
        st.error(f"Error previewing DB: {e}")

# Step 2: Setup LLM + Query Engine
try:
    llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
    sql_db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    query_engine = NLSQLTableQueryEngine(sql_database=sql_db, llm=llm)
except Exception as e:
    st.error(f"Error initializing SQL engine: {e}")
    st.stop()

# Step 3: Ask natural language question
user_input = st.text_input("💬 Ask a question about the data:")

if st.button("Run Query") and user_input:
    try:
        response = query_engine.query(user_input)
        st.success("✅ Answer:")
        st.write(response.response)

        st.info("🧾 SQL Generated:")
        st.code(response.metadata.get("sql_query", "SQL not available"), language="sql")
    except Exception as e:
        st.error(f"Query error: {e}")
