from typing import Union
import autogen
from autogen import AssistantAgent
from autogen.agentchat.contrib.img_utils import get_pil_image, pil_to_data_uri
from autogen import register_function
from autogen import ConversableAgent
from typing import Dict, List
from typing import Annotated, TypedDict
from autogen import Agent


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


user = autogen.UserProxyAgent(
    name="User",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="ALWAYS",
    system_message="User. You are a human admin. You present the problem.",
    llm_config=False,
    code_execution_config={
        "work_dir": "CAD",
        "use_docker": False,
    },
)

planner = AssistantAgent(
    name="planner",
    system_message = '''Planner. You are a helpful AI assistant. Your task is to suggest a comprehensive plan to solve a given task.

Explain the Plan: Begin by providing a clear overview of the plan.
Break Down the Plan: For each part of the plan, explain the reasoning behind it, and describe the specific actions that need to be taken.
No Execution: Your role is strictly to suggest the plan. Do not take any actions to execute it.
No Tool Call: If tool call is required, you must include the name of the tool and the agent who calls it in the plan. However, you are not allowed to call any Tool or function yourself. 

''',
    llm_config=gpt4turbo_config,
    description='Who can suggest a step-by-step plan to solve the task by breaking down the task into simpler sub-tasks.',
)

assistant = AssistantAgent(
    name="assistant",
    system_message = '''You are a helpful AI assistant.
    
Your role is to call the appropriate tools and functions as suggested in the plan. You act as an intermediary between the planner's suggested plan and the execution of specific tasks using the available tools. You ensure that the correct parameters are passed to each tool and that the results are accurately reported back to the team.

Return "TERMINATE" in the end when the task is over.
''',
    llm_config=gpt4turbo_config,
    description='''An assistant who calls the tools and functions as needed and returns the results. Tools include "rate_novelty_feasibility" and "generate_path".''',
)