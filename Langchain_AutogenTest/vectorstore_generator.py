from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")



def load_and_split_pdf(pdf_path):   
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()  # Load documents from the PDF
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, 
    chunk_overlap=100,
    separators="\n",
    )  # Configure splitter
    split_documents = text_splitter.split_documents(documents)  # Split the documents into smaller chunks
    return split_documents


pdf_path = "MechDesignAgents/data/ExamplesCadquery.pdf" #path of your pdf file
split_documents = load_and_split_pdf(pdf_path)



vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="MechDesignAgents/Langchain_AutogenTest/store/Test1",  # Where to save data locally, remove if not necessary
)

# Add split documents to the vector store using add_texts
vector_store.add_texts([doc.page_content for doc in split_documents])

