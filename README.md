
# Zomato Restaurant Chatbot


This is an AI-powered chatbot built with LangChain, HuggingFace, FAISS, and Streamlit to answer restaurant-related questions from a structured knowledge base. It can provide accurate, context-aware answers to queries about menus, dietary options, prices, and more.

## Other Submission Link

[Demo video ](https://drive.google.com/file/d/13mzTjU-5tHXgww0Ah-ji6VBqqZB7cL0M/view)
[Technical Report ](https://docs.google.com/document/d/1i4DERSvCNfU1cYx8HyswSDJ83szxAMej_aSuBySFMbw/edit?usp=sharing)
[system architecture](https://lucid.app/lucidchart/29a36474-98a8-4f1d-b7dc-3989632a3f05/edit?viewport_loc=-298%2C-607%2C3513%2C1628%2C0_0&invitationId=inv_3c99a76c-e02c-4c72-b296-4cb3d8c9ca6c)



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
