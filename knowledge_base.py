import json
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- Load restaurant JSON data ---
with open('./sample_data/data.json', 'r') as f:
    restaurants = json.load(f)

# --- Convert restaurant menus into long-text documents ---
docs = []
for restaurant in restaurants:
    text = f"Restaurant Name: {restaurant['name']}\n"
    text += f"Address: {restaurant['contact_info']['address']}\n"
    text += f"Hours: {restaurant['contact_info']['hours']}\n"
    text += f"Price Range: ${restaurant['price_range']['min']} - ${restaurant['price_range']['max']}\n"
    text += f"Total Items: {restaurant['item_count']}\n\n"
    text += "Menu Items:\n"

    for item in restaurant['menu_items']:
        text += f"- {item['item']} (${item['price']}): {item['description']}\n"
        if item['vegetarian']:
            text += "  This item is vegetarian.\n"
        if item['vegan']:
            text += "  This item is vegan.\n"
        if item['gluten_free']:
            text += "  This item is gluten-free.\n"
        if item['spicy']:
            text += "  This item is spicy.\n"

    docs.append(Document(page_content=text, metadata={"restaurant": restaurant["name"]}))

# --- Chunk into smaller pieces
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = splitter.split_documents(docs)

# --- Create the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# --- Store embeddings in vector database
DB_FAISS_PATH = "vectorstore/db_faiss"
db = FAISS.from_documents(chunks, embedding_model)
db.save_local(DB_FAISS_PATH)
