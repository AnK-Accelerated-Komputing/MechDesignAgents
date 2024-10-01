# %%
from autogen import ConversableAgent
from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent



config_list_gemini = [
    {
        "model": 'gemini-pro',
        "api_key": 'AIzaSyBEx8PESd9f8ff1IqMSQ2usB-cLngPZLug',  # Replace with your API key variable
        "api_type": "google",
    }
]

gemini_config = {
    "seed": 25,
    "temperature": 0,
    "config_list": config_list_gemini,
    "request_timeout": 600,
    "retry_wait_time": 120,
}


# %%
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain

# %%
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    api_key="AIzaSyBEx8PESd9f8ff1IqMSQ2usB-cLngPZLug",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

# %%
loaders = [ PyPDFLoader('./Examples_small.pdf') ]
docs = []
for l in loaders:
    docs.extend(l.load())
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
docs = text_splitter.split_documents(docs)

# %%
from chromadb.utils import embedding_functions
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(google_api_key="AIzaSyBEx8PESd9f8ff1IqMSQ2usB-cLngPZLug",model="models/embedding-001")

vectorstore = Chroma(
    collection_name="full_documents",
    embedding_function=embeddings
)
vectorstore.add_documents(docs)

# %%
qa = ConversationalRetrievalChain.from_llm(
    llm,
    vectorstore.as_retriever(),
    memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True)
)

# %%
def cadquery_coder(design: str) -> str:
  response = qa({"design": design})
  return response["design"]

# %%
llm_config={
    "request_timeout": 600,
    "seed": 42,
    "config_list": gemini_config,
    "temperature": 0,
    "functions": [
        {
            "name": "cadquery_coder",
            "description": "Create Cadquery codes to design the required part.",
            "parameters": {
                "type": "object",
                "properties": {
                    "design": {
                        "type": "string",
                        "description": "The design to be created with CadQuery",
                    }
                },
                "required": ["design"],
            },
        }
    ],
}

# %%
# create an AssistantAgent instance named "assistant"
assistant = AssistantAgent(
    name="assistant",
    llm_config=gemini_config,
)
# create a UserProxyAgent instance named "user_proxy"
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config= {
        "work_dir": "NewCAD1",
        "use_docker": False,
    },
    llm_config=gemini_config,
    system_message="""Reply TERMINATE if the task has been solved at full satisfaction.
Otherwise, reply CONTINUE, or the reason why the task is not solved yet.""",
    function_map={"cadquery_coder": cadquery_coder}
)

# %%
user_proxy.initiate_chat(
    assistant,
    message="""
Write the CadQuery code to create a plate with hole.
"""
)

# %%



