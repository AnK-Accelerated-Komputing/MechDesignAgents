from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
import os

from autogen.agentchat.contrib.llava_agent import LLaVAAgent, llava_call


config_list = [
    {

        "model": "llama-3.2-90b-vision-preview",
        "api_key":  os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    },
    {
        "model": 'gemini-pro',
        "api_key": os.environ["GEMINI_API_KEY"],  # Replace with your API key variable
        "api_type": "google",
    },
    {

        "model": "llama3-8b-8192",
        "api_key":  os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    },
    
]

llm_config = {
    "seed": 25,
    "temperature": 0,
    "config_list": config_list,
    "request_timeout": 600,
    "retry_wait_time": 120,
}

def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

user_proxy = UserProxyAgent(
    name="User",
    is_termination_msg=termination_msg,
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=5,
    code_execution_config=False,
    system_message="""You are a user who provides engineering drawing descriptions.""",
)

drawing_expert = MultimodalConversableAgent(
    name="Drawing Expert",
    is_termination_msg=termination_msg,
    llm_config={"config_list": config_list, "temperature": 0.5, "max_tokens": 500},
    system_message="""You are a CAD drawing expert who translates image provided by user into detailed drawing specifications.  Provide dimensions, tolerances, materials, and other necessary information for creating a professional engineering drawing.  Always respond in a structured format, separating different aspects of the drawing clearly.""",
)

import base64

with open("/home/niel77/MechanicalAgents/mechdesignagents/images/image.png", "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    image_data_url = f"data:image/png;base64,{encoded_image}"

user_proxy.initiate_chat(
    drawing_expert,
    message=f"""
    Provide me all the details of this engineering drawing.
        <img {image_data_url}>
    """
)

