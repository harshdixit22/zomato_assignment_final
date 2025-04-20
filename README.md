
# Zomato Restaurant Chatbot


This is an AI-powered chatbot built with LangChain, HuggingFace, FAISS, and Streamlit to answer restaurant-related questions from a structured knowledge base. It can provide accurate, context-aware answers to queries about menus, dietary options, prices, and more.





## Documentation

HuggingFace API Key

You’ll need a HuggingFace API token to use the language model.

Get your token from HuggingFace.

Replace the placeholder in .env:
## Run Locally

Clone the project

```bash
  git clone https://github.com/harshdixit22/zomato_assignment_final.git
```

Go to the project directory

```bash
  cd zomato_assignment_final
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Create the vector store

```bash
  python .\knowledge_base.py
```
Run the Chatbot

```bash
  python -m streamlit run .\chatbot.py
```
