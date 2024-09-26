from autogen import ConversableAgent
from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent

import chromadb

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
    name="CadQuery coder",
    system_message="""You are a Cadquery code writer that retrieves the relevant code from the given context to create CAD models.
            Write your code script in Markdown format. For example:
            ```python
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
        ```
        The code provided will be executed in the order it is written. If a code block fails to execute try to fix the error and write the code block again.
        Once all code blocks are successfully executed, return 'TERMINATE' to end the conversation.
        """,
    human_input_mode="NEVER",
    llm_config=gemini_config,
    code_execution_config=False,
    retrieve_config={
        "task": "qa",
        "docs_path": "/home/niel77/MechanicalAgents/data/Examples_small.md",
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "get_or_create": True,
        "overwrite": True,  # Set to True if you want to overwrite existing collections
    },
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "NewCAD",
        "use_docker": False,
    },
)

#user_proxy.initiate_chat(cad_data,message="Write Cadquery code to create plate with a hole.")
#problem_prompt=input("Enter your design problem: ")
#problem_prompt = '''Design a brick that is 10 inches tall, 6 inches wide and 3 inches thick with filleted edges'''
#result = user_proxy.initiate_chat(Cad_codewriter, message=problem_prompt)

cad_data.initiate_chat(user_proxy, 
                       message=cad_data.message_generator, 
                       problem="Write Cadquery code to create plate with a hole.",
                        summary_method='reflection_with_llm'
                       )