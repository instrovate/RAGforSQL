import streamlit as st
import sqlite3
import os
import requests
from llama_index.core import SQLDatabase, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.core.query_engine import NLSQLTableQueryEngine


st.set_page_config(page_title="RAG over SQL", page_icon="🧠")
st.title("🧠 RAG Over SQL (LlamaIndex + Streamlit + SQLite)")

   # Set OpenAI Key from Streamlit secrets
        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]

# Step 1: Upload or load default DB
uploaded_file = st.file_uploader("Upload your own SQLite .db file", type=["db"])
if uploaded_file:
    db_path = "uploaded.db"
    with open(db_path, "wb") as f:
        f.write(uploaded_file.read())
else:
    db_path = "Instrovate_sample_employee.db"
    db_url = "https://raw.githubusercontent.com/instrovate/RAGforSQL/main/Instrovate_sample_employee.db"
    if not os.path.exists(db_path):
        r = requests.get(db_url)
        with open(db_path, "wb") as f:
            f.write(r.content)

# Step 2: Preview schema
if st.checkbox("🔍 Preview DB Schema"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        st.subheader(f"📄 Table: {table[0]}")
        data = cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5").fetchall()
        cols = [desc[0] for desc in cursor.description]
        st.dataframe([dict(zip(cols, row)) for row in data])
    conn.close()

# Step 3: Initialize SQL RAG engine
try:
    llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
    sql_db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    engine = NLSQLTableQueryEngine(sql_database=sql_db, llm=llm)
except Exception as e:
    st.error(f"Engine init failed: {e}")
    st.stop()

# Step 4: Natural Language to SQL Query
user_input = st.text_input("💬 Ask something about your database")

if st.button("Run Query") and user_input:
    try:
        result = engine.query(user_input)
        st.success("✅ Answer:")
        st.write(result.response)
        st.info("🧾 SQL Used:")
        st.code(result.metadata.get("sql_query", "No SQL metadata returned"), language="sql")
    except Exception as e:
        st.error(f"Query failed: {e}")
