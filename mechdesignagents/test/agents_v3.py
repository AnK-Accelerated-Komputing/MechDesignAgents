from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from ocp_vscode import *
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent

import os
from typing_extensions import Annotated
from utils.llm import LLMConfigSelector

#Definig default config list for llms. Add more llms if you want. By default
#Autogen will select the first one until it can use it.
config_list_selection = LLMConfigSelector()
llm_config = {
    "seed": 25,
    "temperature": 0.3,
    "config_list": [config_list_selection.get_model_config()],
    # "request_timeout": 600,
    # "retry_wait_time": 120,
}

#This is for terminating the chat. This can be passed as one line functin as well.
def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

#Defining agents for designing
#First we define designer userproxy agent which takes input from human

User = UserProxyAgent(
    name="User",
    is_termination_msg=termination_msg,
    human_input_mode="ALWAYS", # Use ALWAYS for human in the loop
    max_consecutive_auto_reply=5, #Change it to limit the number of replies from this agent
    #here we define the coding configuration for executing the code generated by agent 
    # code_execution_config= {
    #     "work_dir": "NewCADs",
    #     "use_docker": False,
    # },
    code_execution_config= False,
    # llm_config={"config_list": config_list}, #you can also select a particular model from the config list here for llm
    system_message=""" You provide image for creating CAD models from it. """,
    # description= "The designer who asks questions to create CAD models using CadQuery",
    # default_auto_reply="Reply `TERMINATE` if the task is done.",
)

drawing_recognizer= MultimodalConversableAgent(
    name= "Drawing_Recognition_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are a Drawing Recognition Agent. Your task is to identify all the views (e.g., front, top, side) present in an engineering drawing 
    image and their respective positions within the image. Recognize geometric shapes, features, and annotations such as lines, arcs, and text and tables. 
    Return a structured representation of the identified views with their positions in JSON format.
    Each view should include its label and relative position in the drawing.
    """
)

dimension_extractor = MultimodalConversableAgent(
    name= "Dimension_Extraction_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are a Dimension Extraction Agent. Your task is to analyze the JSON output from the Drawing Recognition Agent. 
    For each view, use its position to locate it in the engineering drawing image and extract the major dimensions (e.g., length, width, height, or diameter).
    Name the dimensions appropriately and identify geometric tolerances for each view if present. 
    Output the results for all views in a JSON format.
    """
)

verifier = MultimodalConversableAgent(
    name= "Verification_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are a Verification_Agent. Your task is to validate the JSON output from the Dimension_Extraction_Agent by cross-checking the dimensions and 
    tolerances with the annotations or scale references in the drawing image. Ensure consistency and accuracy, then 
    provide a confidence score for each dimension of each view. 
    Output the verified data and confidence scores in JSON format.
    """
)

designer_expert = AssistantAgent(
    name="Designer_Expert",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER", # Use ALWAYS for human in the loop
    llm_config=llm_config, #you can also select a particular model from the config list here for llm
    system_message="""You are a CAD Design Expert who provides concise plan and directions to support CAD modeling in CadQuery. 
    You should also revise the approach based on feedback from designer. Explain in clear steps what
    needs to be done by CadQuery Code Writer. 
    For each design required based on the results of Verification_Agent:
    Clearly list the necessary parameters.
    Offer a single, focused design approach using CadQuery-specific methods or geometry data only.
    Structure responses as: Required Parameters: [list essential parameters] Design Approach: [CadQuery-driven approach, structured into logical steps]
    Keep answers brief, direct, and strictly analytical to aid smooth CadQuery implementation.
    Also keep in mind to create 2D sketch for creating 3D model whenever applicable.
    NEVER provide code.""",
    description= "The designer expert who provides approach to answer questions to create CAD models in CadQuery",
)

cad_coder = AssistantAgent(
    "CadQuery_Code_Writer",
    system_message= """You follow the approved plan by Designer Expert.
    You write python code to create CAD models using CadQuery.
    Wrap the code in a code block that specifies the script type. 
    The user can't modify your code. 
    So do not suggest incomplete code which requires others to modify. 
    Don't use a code block if it's not intended to be executed by the executor.
    Don't include multiple code blocks in one response. 
    Do not ask others to copy and paste the result. 
    Check the execution result returned by the executor.
    If the result indicates there is an error, fix the error and output the code again.
    Suggest the full code instead of partial code or code changes. 
    For every response, use this format in Python markdown:
        Adhere strictly to the following outline
        Python Markdown and File Name
        Start with ```python and # filename: <design_name>.py (based on model type).

        Import Libraries
        ALWAYS import cadquery and ocp_vscode (for visualization).

        Define Parameters
        List dimensions or properties exactly as instructed by the analyst.

        Create the CAD Model
        Build models using only CadQuery’s primitives and boolean operations as directed.

        Save the Model
        Export in STL, STEP, and DXF formats.

        Visualize the Model
        Use show(model_name) from ocp_vscode to visualize.

        Example:
```python
        # filename: box.py
        import cadquery as cq
        from ocp_vscode import * #never forget this line

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
        show(box) #always visualize the model
```
        Only use CadQuery’s predefined shapes and operations based on the analyst’s instructions.""",
    llm_config=llm_config,
    human_input_mode="NEVER",
    description="CadQuery Code Writer who writes python code to create CAD models following the system message.",
)


executor = AssistantAgent(
    name="Executor",
    is_termination_msg=termination_msg,
    system_message="You save and execute the code written by the CadQuery Code Writer and report and save the result and pass it to Reviewer.",
    code_execution_config= {
        "last_n_messages": 3,
        "work_dir": "NewCADs",
        "use_docker": False,
        
    },
    description= "Executor who executes the code written by CadQuery Code Writer."
)
reviewer = AssistantAgent(
    name="Reviewer",
    is_termination_msg=termination_msg,
    system_message=''' If code ran successfully, just pass message that it ran successfully to User for final feedback.
    IF execution fails,then only you suggest changes to code written by CadQuery Code Writer
    making sure that CadQuery Code Writer is using methods and functions available within CadQuery library
    for recreating the cad model specified by User and using show method from ocp_vscode library to visualize the model.
    ''' ,
    llm_config=llm_config,
    description="Code Reviewer who can review python code written by CadQuery Code Writer after executed by Executor.",
)

#clears the history of the old chats
def reset_agents():
    User.reset()
    drawing_recognizer.reset()
    dimension_extractor.reset()
    verifier.reset()
    executor.reset()
    cad_coder.reset()
    reviewer.reset()
    designer_expert.reset()

