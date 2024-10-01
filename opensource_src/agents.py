from autogen import ConversableAgent
from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
)


config_list_gemini = [
    {   'model': 'mistral-nemo',
        'base_url': 'http://0.0.0.0:4000',
        'api_key' : 'NULL',
        
    }
]

gemini_config = {
    "timeout": 600,
    "seed": 25,
    "temperature": 0,
    "config_list": config_list_gemini,
    }


Cad_codewriter = AssistantAgent(
    "CAD Code Writer",
    system_message='''CAD Code Writer.You are a CadQuery expert and you write codes in Python to create CAD models using CADquery. 
        Here is an example of abox you created and saved in the step, dxf and stl format.
        ##
        Q: Create a box of size 80*60*10 and save it in stl, step and dxf file format.
        A:
        import cadquery as cq
        from ocp_vscode import * # this is used to visualize model with OCP CAD viewer
        height = 60.0
        width = 80.0
        thickness = 10.0
        # make the base
        box = cq.Workplane("XY").box(height, width, thickness)
        show(box)
        # cq.exporters.export(box, "box.stl")
        # cq.exporters.export(box.section(), "box.dxf")
        # cq.exporters.export(box, "box.step")
        ##
        ''',
    llm_config=gemini_config,
    human_input_mode="NEVER",
)
cad_data = RetrieveUserProxyAgent(
    name="CAD Code Writer's Assistant",
    human_input_mode="NEVER",
    default_auto_reply="Reply `TERMINATE` if the task is done.",
    max_consecutive_auto_reply=3,
    retrieve_config={
        "task": "code",
        "docs_path": "/home/niel77/MechanicalAgents/data/Examples_small.md",
        "chunk_token_size": 1000,
        "model": config_list_gemini[0]['model'],
        "embedding_model": embeddings,
        'clean_up_tokenization_spaces': False,
        "collection_name": "hello",
        "get_or_create": True,
    },
    code_execution_config=False,  # we don't want to execute code in this case.
    description="Assistant who has extra content retrieval power for solving difficult problems.",
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=3,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "NewCAD",
        "use_docker": False,
    },
)

user_proxy.initiate_chat(Cad_codewriter,message="Write Cadquery code to create plate with a hole.")
#problem_prompt=input("Enter your design problem: ")
#problem_prompt = '''Design a brick that is 10 inches tall, 6 inches wide and 3 inches thick with filleted edges'''
#result = user_proxy.initiate_chat(Cad_codewriter, message=problem_prompt)


# from chromadb.utils import embedding_functions
# default_ef = embedding_functions.DefaultEmbeddingFunction()
# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# from langchain_community.document_loaders import PyPDFLoader

# loader = PyPDFLoader("/home/niel77/MechanicalAgents/cadquery-readthedocs-io-en-latest.pdf")
# pages = loader.load_and_split()