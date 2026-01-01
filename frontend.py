from rag_pipeline import answer_query, retrieve_docs,llm_model

import streamlit as st
uploaded_file =st.file_uploader("Upload PDF", type="pdf",accept_multiple_files=False)

user_query = st.text_area("Enter your prompt: ", height=150, placeholder="Ask anything!")
ask_question= st.button("Ask AI Lawyer")
if ask_question:
    if uploaded_file:
        st.chat_message("user").write(user_query)

        #RAG PIPELINE
        retrieved_docs=retrieve_docs(user_query)
        response =answer_query(documents=retrieved_docs, model=llm_model, query= user_query)
        # fixed_response="Hi, this is a fixed resposne."
        st.chat_message("AI Lawyer").write(response)

    else:
        st.error("Kindy upload a PDF file to proceed.")

