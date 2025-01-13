from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import os
from typing_extensions import Annotated
from utils.langchain_rag import langchain_rag


#Definig config list for llms. Add more llms if you want. By default
#Autogen will select the first one until it can use it.
config_list = [
    {

        "model": "llama-3.2-90b-text-preview",
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


#This is for terminating the chat. This can be passed as one line functin as well.
def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

#Defining agents for designing
#First we define designer userproxy agent which takes input from human

# Function Call Agent - Acts as first responder
functioncall_agent = AssistantAgent(
    name="Function Call Agent",
    is_termination_msg=termination_msg,
    human_input_mode="Never",
    llm_config={"config_list": config_list},
    system_message="""You are the first responder for all CAD design requests. Follow strictly:
1. ALWAYS check for registered functions first for requested CAD model
2. If function exists: Call it with provided parameters or reasonable defaults
3. If successful: Forward to User for feedback with explicit message "Forwarding to User for feedback now" and skip the next step."""
)

proxy_user = UserProxyAgent(
    name="Proxy User",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER", # Use ALWAYS for human in the loop
    max_consecutive_auto_reply=5, #Change it to limit the number of replies from this agent
    code_execution_config= False,
    system_message=" Proxy user who:"
    "1. Executes the registered function"
    "2. Forwards the execution to User with message 'Forwarding to User for feedback'."
    )

# Designer Expert - Provides structured approach
designer_expert = AssistantAgent(
    name="Designer Expert",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    llm_config={"config_list": config_list},
    system_message="""You only respond when Function Call Agent explicitly forwards a request to you.
When activated:
1. List required parameters
2. Provide single CadQuery-based approach in clear steps
3. End with 'Forwarding to CAD Assistant for documentation search.'
Keep responses analytical and never provide code."""
)

# CAD Coder Assistant - RAG-focused helper
cad_coder_assistant = AssistantAgent(
    name="CAD Coder Assistant",
    system_message="""You only activate when Designer Expert forwards a request.
1. Use provided RAG function to search CadQuery documentation
2. Find relevant code patterns and examples
3. Summarize findings and forward to CAD Coder with message:
   'Documentation search complete. Providing patterns to CAD Coder:'""",
    llm_config={"config_list": config_list}
)

# CAD Coder - Implementer
cad_coder = AssistantAgent(
    name="CadQuery Code Writer",
    system_message="""You only respond to input from CAD Coder Assistant and write python code to create CAD models using CadQuery  .
Create complete CadQuery implementation:
1. Full imports (cadquery, ocp_vscode)
2. All parameters
3. Complete model creation
4. Export commands (STL, STEP, DXF)
5. Visualization with show() from ocp_vscode
End with 'Forwarding to Executor for implementation.'
Strictly follow the structure of example below to write python code for CAD models.
        Example:
```
        python
        # filename: box.py
        import cadquery as cq
        from ocp_vscode import *

        # Step 1: Define Parameters
        height = 60.0
        width = 80.0
        thickness = 10.0

        # Step 2: Create the CAD Model
        box = cq.Workplane("XY").box(height, width, thickness)

        # Step 3: Save the Model
        cq.exporters.export(box, "box.stl")
        cq.exporters.export(box.section(), "box.dxf")
        cq.exporters.export(box, "box.step")

        # Step 4: Visualize the Model
        show(box)
```
        Only use CadQuery’s predefined shapes and operations based on the analyst’s instructions.
""",
    llm_config={"config_list": config_list}
)

# Executor - Implementation
executor = AssistantAgent(
    name="Executor",
    system_message="""You only activate when CAD Coder forwards code.
1. Execute provided code in work directory
2. Capture all outputs
3. Forward results to Reviewer with:
   Success: 'Execution successful. Reviewer, please verify:'
   Failure: 'Execution failed. Reviewer, please analyze:'""",
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "NewCADs",
        "use_docker": False,
    }
)

# Reviewer - Final check
reviewer = AssistantAgent(
    name="Reviewer",
    system_message="""You only respond to Executor's results.
On success: 
- Confirm to User with 'Model created successfully.'
On failure:
- Send to CAD Coder: 'Code needs revision. Specific issues:'
  followed by CadQuery-specific fixes""",
    llm_config=llm_config
)

# User Proxy - Human interface
User = UserProxyAgent(
    name="User",
    system_message="""Design requester who:
1. Initiates with CAD design requests
2. Receives final confirmation or results
3. Can provide feedback if needed""",
    human_input_mode="ALWAYS",
    code_execution_config=False
)

@cad_coder_assistant.register_for_execution()
@cad_coder_assistant.register_for_llm(description= "Code finder using Retrieval Augmented Generation")
def call_rag(
    question: Annotated[float, "Task for which code to be found"],
) -> str:
    return langchain_rag(question)

#clears the history of the old chats
def reset_agents():
    User.reset()
    # designer_aid.reset()
    cad_coder_assistant.reset()
    executor.reset()
    cad_coder.reset()
    reviewer.reset()
    designer_expert.reset()


