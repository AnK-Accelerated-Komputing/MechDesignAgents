# %%
import json
import os

import chromadb

import autogen
from autogen import AssistantAgent
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
# Accepted file formats for that can be stored in
# a vector database instance
from autogen.retrieve_utils import TEXT_FORMATS
print("Accepted file formats for `docs_path`:")
print(TEXT_FORMATS)

# %%
assistant = AssistantAgent(
    name="assistant",
    system_message="You are a helpful assistant.",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list_gemini,
    },
)

from chromadb.utils import embedding_functions
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(google_api_key="AIzaSyBEx8PESd9f8ff1IqMSQ2usB-cLngPZLug",model="models/embedding-001")
default_ef = embedding_functions.DefaultEmbeddingFunction()


URL = "/home/niel77/MechanicalAgents/data/Examples_small.md"
# 2. create the RetrieveUserProxyAgent instance named "ragproxyagent"
# Refer to https://microsoft.github.io/autogen/docs/reference/agentchat/contrib/retrieve_user_proxy_agent
# and https://microsoft.github.io/autogen/docs/reference/agentchat/contrib/vectordb/chromadb
# for more information on the RetrieveUserProxyAgent and ChromaVectorDB
ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "code",
        "docs_path": [
            URL
            ],
        "chunk_token_size": 200,
        "model": config_list_gemini[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/Examples_db"),
         # set to True if you want to overwrite an existing collection
        "get_or_create": False,  # set to False if don't want to reuse an existing collection
        "collection_name": "cadquery1",
        "must_break_at_empty_line": False,
        "embedding_function": default_ef,
    },
    code_execution_config=False,  # set to False if you don't want to execute the code
)
# %%
assistant.reset()

# given a problem, we use the ragproxyagent to generate a prompt to be sent to the assistant as the initial message.
# the assistant receives the message and generates a response. The response will be sent back to the ragproxyagent for processing.
# The conversation continues until the termination condition is met, in RetrieveChat, the termination condition when no human-in-loop is no code block detected.
# With human-in-loop, the conversation will continue until the user says "exit".
code_problem = "Write a CadQuery code to create a plate with hole."
ragproxyagent.initiate_chat(
    assistant, message=ragproxyagent.message_generator, problem=code_problem, search_string="plate with hole"
)  # search_string is used as an extra filter for the embeddings search, in this case, we only want to search documents that contain "spark".
# %%
