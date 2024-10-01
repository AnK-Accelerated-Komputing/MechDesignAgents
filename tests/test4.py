# %%

from langchain_core.prompts  import PromptTemplate
from langchain import hub
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import StrOutputParser
from langchain.schema.prompt_template import format_document
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.vectorstores import Chroma


# %%

loader = PyPDFLoader("data/Examples_small.pdf")
docs = loader.load()
     
# %%
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# If there is no environment variable set for the API key, you can pass the API
# key to the parameter `google_api_key` of the `GoogleGenerativeAIEmbeddings`
# function: `google_api_key = "key"`.

gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key="AIzaSyBEx8PESd9f8ff1IqMSQ2usB-cLngPZLug")

# %% 

# Save to disk
vectorstore = Chroma.from_documents(
                     documents=docs,                 # Data
                     embedding=gemini_embeddings,    # Embedding model
                     persist_directory="./chroma_db" # Directory to save data
                     )
     
# %%

# Load from disk
vectorstore_disk = Chroma(
                        persist_directory="./chroma_db",       # Directory of db
                        embedding_function=gemini_embeddings   # Embedding model
                   )
# Get the Retriever interface for the store to use later.
# When an unstructured query is given to a retriever it will return documents.
# Read more about retrievers in the following link.
# https://python.langchain.com/docs/modules/data_connection/retrievers/
#
# Since only 1 document is stored in the Chroma vector store, search_kwargs `k`
# is set to 1 to decrease the `k` value of chroma's similarity search from 4 to
# 1. If you don't pass this value, you will get a warning.
retriever = vectorstore_disk.as_retriever(search_kwargs={"k": 1})

# Check if the retriever is working by trying to fetch the relevant docs related
# to the word 'MMLU' (Massive Multitask Language Understanding). If the length is greater than zero, it means that
# the retriever is functioning well.
print(len(retriever.invoke("CadQuery")))     


#%%

from langchain_google_genai import ChatGoogleGenerativeAI

# If there is no environment variable set for the API key, you can pass the API
# key to the parameter `google_api_key` of the `ChatGoogleGenerativeAI` function:
# `google_api_key="key"`.
llm = ChatGoogleGenerativeAI(model="gemini-pro",
                 temperature=0.7,google_api_key="AIzaSyBEx8PESd9f8ff1IqMSQ2usB-cLngPZLug", top_p=0.85)
     
#%%
# # Prompt template to query Gemini
llm_prompt_template = """You are an assistant for providing CadQuery codes.
Use the following context to create the model using python code..
If you don't know the answer, just say that you don't know.
keep the answer concise.\n
DesignProblem: {question} \nContext: {context} \nAnswer:"""

llm_prompt = PromptTemplate.from_template(llm_prompt_template)

print(llm_prompt)     


#%%
# Combine data from documents to readable string format.
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Create stuff documents chain using LCEL.
#
# This is called a chain because you are chaining together different elements
# with the LLM. In the following example, to create the stuff chain, you will
# combine the relevant context from the website data matching the question, the
# LLM model, and the output parser together like a chain using LCEL.
#
# The chain implements the following pipeline:
# 1. Extract the website data relevant to the question from the Chroma
#    vector store and save it to the variable `context`.
# 2. `RunnablePassthrough` option to provide `question` when invoking
#    the chain.
# 3. The `context` and `question` are then passed to the prompt where they
#    are populated in the respective variables.
# 4. This prompt is then passed to the LLM (`gemini-pro`).
# 5. Output from the LLM is passed through an output parser
#    to structure the model's response.
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | llm_prompt
    | llm
    | StrOutputParser()
)

#%%
result = rag_chain.invoke("Write CadQuery code to create a plate of dimension 100*100 and thickness 5mm with hole of diameter 20mm.")
# %%
print(result)
# %%
