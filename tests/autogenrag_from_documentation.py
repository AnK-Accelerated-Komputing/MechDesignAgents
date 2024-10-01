# %%

import chromadb

import autogen
from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent


config_list_gemini = [
    {
        "model": 'gemini-pro',
        "api_key": os.environ["GEMINI_API_KEY"],  # Replace with your API key variable
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
assistant = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "NewCAD",
        "use_docker": False,
    },
)


URL = "/data/Examples_small.md"
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
        "docs_path": "/data/Examples_small.md",
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "get_or_create": True,
        "overwrite": False,  # Set to True if you want to overwrite existing collections
        "clean_up_tokenization_spaces": True,
    },
    code_execution_config=False,
    description = "You are a retriever agent who codes in python to create 3D model in CadQuery"
)
# %%
assistant.reset()

# given a problem, we use the ragproxyagent to generate a prompt to be sent to the assistant as the initial message.
# the assistant receives the message and generates a response. The response will be sent back to the ragproxyagent for processing.
# The conversation continues until the termination condition is met, in RetrieveChat, the termination condition when no human-in-loop is no code block detected.
# With human-in-loop, the conversation will continue until the user says "exit".
code_problem = "Write a CadQuery code to create a plate with hole."
ragproxyagent.initiate_chat(
    assistant, message=ragproxyagent.message_generator, problem=code_problem,n_results=1, search_string="plate with hole"
)  # search_string is used as an extra filter for the embeddings search, in this case, we only want to search documents that contain "spark".
# %%
