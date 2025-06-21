import streamlit as st
import os
import sqlite3
from llama_index.core import SQLDatabase, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.indices.struct_store import NLSQLTableQueryEngine

# Title
st.title("🧠 RAG Over SQL (LlamaIndex + Streamlit + SQLite)")

# Upload or use default DB
uploaded_file = st.file_uploader("Upload a SQLite .db file", type="db")
db_path = "sample_employee.db"

if uploaded_file is not None:
    with open("uploaded.db", "wb") as f:
        f.write(uploaded_file.read())
    db_path = "uploaded.db"

# Preview DB schema if checkbox checked
if st.checkbox("🔍 Show Table Schema (Preview)"):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table_name in tables:
        st.subheader(f"Table: {table_name[0]}")
        rows = conn.execute(f"SELECT * FROM {table_name[0]} LIMIT 5").fetchall()
        col_names = [desc[0] for desc in conn.execute(f"SELECT * FROM {table_name[0]} LIMIT 1").description]
        st.dataframe([dict(zip(col_names, row)) for row in rows])
    conn.close()

# Initialize LLM + SQLDatabase
try:
    llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
    sql_database = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    query_engine = NLSQLTableQueryEngine(sql_database=sql_database, llm=llm)
except Exception as e:
    st.error(f"Error initializing query engine: {e}")
    st.stop()

# User question
question = st.text_input("💬 Ask a question about the database:")

if st.button("🔎 Run Query") and question:
    try:
        response = query_engine.query(question)
        st.success("✅ Query Answer:")
        st.write(response.response)
        st.info("💡 Generated SQL:")
        st.code(response.metadata.get("sql_query", "SQL not found"), language="sql")
    except Exception as e:
        st.error(f"Error during query: {e}")
