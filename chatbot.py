import os
import html
import streamlit as st
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint


from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

DB_FAISS_PATH="vectorstore/db_faiss"
@st.cache_resource


#load the vector store
def get_vectorstore():
    embedding_model=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    db=FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
    return db


#set the prompt
def set_custom_prompt(custom_prompt_template):
    prompt=PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])
    return prompt

def load_llm(huggingface_repo_id,HF_TOKEN):
    llm=HuggingFaceEndpoint(
        repo_id=huggingface_repo_id,
        task="text-generation",
        temperature=0.5,
        max_new_tokens=512,  
        huggingfacehub_api_token=HF_TOKEN
    )
    return llm


def main():
    st.title("Chatbot!")

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        st.chat_message(message['role']).markdown(message['content'])

    prompt=st.chat_input("Pass your prompt here")

    if prompt:
        st.chat_message('user').markdown(prompt)
        st.session_state.messages.append({'role':'user', 'content': prompt})

        CUSTOM_PROMPT_TEMPLATE =CUSTOM_PROMPT_TEMPLATE = """
            You are a helpful and context-aware assistant designed to answer restaurant-related questions using the provided context.
            IMPORTANT: After answering the user's question, do not continue or generate additional Q&A. Do not assume the user wants more examples.


            Instructions:
            - Use ONLY the context to answer.
            - If the answer isn't in the context, say: "I don't know based on the available information."
            - Be direct and concise.
            - Use clear formatting like numbered lists or line breaks.
            - If the user asks for restaurant names, do NOT list items unless requested.
            - Prioritize relevance when filtering or comparing.
            - Do not make up data not present in the context.

            ### Examples:

            Question: Which restaurants have gluten-free options?
            Answer:
            1. The Greenhouse
            2. Urban Vegan
            3. Spice Route

            Question: What is the price range for Quay?
            Answer: $12.0 - $365.0

            Question: Does Bella Pasta have any spicy dishes?
            Answer:
            Yes. Bella Pasta has the following spicy items:
            - Fried Calamari
            - Boneless Buffalo Tenders

            Question: Compare the number of vegetarian options between Sushi Zen and Urban Vegan.
            Answer:
            - Sushi Zen: 5 vegetarian items
            - Urban Vegan: 11 vegetarian items

            --- End of Examples ---

            ## End of Examples

            ### Context:
            {context}

            ### User Question:
            {question}

            ### Final Answer:
           
         """

        
        HUGGINGFACE_REPO_ID="mistralai/Mistral-7B-Instruct-v0.3"
        HF_TOKEN=os.environ.get("HF_TOKEN")

        try: 
            vectorstore=get_vectorstore()
            if vectorstore is None:
                st.error("Failed to load the vector store")

            qa_chain=RetrievalQA.from_chain_type(
                llm=load_llm(huggingface_repo_id=HUGGINGFACE_REPO_ID, HF_TOKEN=HF_TOKEN),
                # chain_type="stuff",
                retriever=vectorstore.as_retriever(),
                # return_source_documents=True,
                chain_type_kwargs={'prompt':set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
            )

            response=qa_chain.invoke({'query':prompt})

            result=response["result"]
            result_to_show = result
            
            st.chat_message('assistant').markdown(result_to_show)
            st.session_state.messages.append({'role':'assistant', 'content': result_to_show})

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
