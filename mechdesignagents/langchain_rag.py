import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

def langchain_rag(code_question: str, 
                  pdf_path="../data/cadquery-readthedocs-io-en-latest.pdf", 
                  persist_directory="./Cadquery_db") -> str:
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # Initialize LLM
    llm = ChatGroq(model="llama3-8b-8192", api_key=os.environ["GROQ_API_KEY"])
    
    # Check if the vector store already exists
    if os.path.exists(persist_directory):
        # Load existing vector store
        vectorstore = Chroma(
            collection_name="CadQuery_Documentation", 
            embedding_function=embeddings,
            persist_directory=persist_directory
        )
        print("Loaded existing vector store.")
    else:
        # If vector store doesn't exist, create it
        # Load and split the document
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        all_splits = text_splitter.split_documents(documents)
        
        # Create and persist the vector store
        vectorstore = Chroma.from_documents(
            collection_name="CadQuery_Documentation",
            documents=all_splits, 
            embedding=embeddings,
            persist_directory=persist_directory
        )
        print("Created and persisted new vector store.")
    
    # Create retriever
    retriever = vectorstore.as_retriever()

    # Define prompt template
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. "
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    # Create chains
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # Invoke the chain
    response = rag_chain.invoke({"input": code_question})
    return response["answer"]

# Example usage
# if __name__ == "__main__":
#     while True:
#         question = input("Enter your question regarding Cadquery: ")
#         print(langchain_rag(question))
    
