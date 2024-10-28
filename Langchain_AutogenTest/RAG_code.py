import os
from langchain_core.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_chroma import Chroma
from dotenv import load_dotenv
from autogen import AssistantAgent
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Initialize Gemini embeddings
gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Load the vector store from disk
vectorstore_disk = Chroma(
    persist_directory="MechDesignAgents/Langchain_AutogenTest/store/test",  #path to your vectorstore
    embedding_function=gemini_embeddings
)

retriever = vectorstore_disk.as_retriever(search_kwargs={"k": 1})

# Configure ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    top_p=0.85
)

# Define the prompt template
llm_prompt_template = """You are an assistant for providing CadQuery codes.
Use the following context to create the model using python code.
If you don't know the answer, just say that you don't know.
Keep the answer concise.\n
DesignProblem: {question} \nContext: {context} \nAnswer:"""

llm_prompt = PromptTemplate.from_template(llm_prompt_template)

# Format docs function
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Create RAG chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | llm_prompt
    | llm
    | StrOutputParser()
)

# Define configuration for the agents
config_list = [{
    "model": "llama3-70b-8192",
    "api_key": os.getenv("GROQ_API_KEY"),
    "api_base": "https://api.groq.com/openai/v1",
    "api_type": "groq"
}]

# Termination message function
def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

cad_coder = AssistantAgent(
    "CadQuery Code Writer",
    system_message= '''You are a CadQuery expert specializing in creating CAD models using Python. Follow the exact structure and format provided below to solve design problems and save the CAD models in STL, STEP, and DXF formats. 
    Adhere strictly to the following outline for every response within the python markdown :
1. ***Python markdown and python file name ***
    Always enter the python code block inside python markdown ```python followed by # filename: file_name.py on the next line.
    This file name should represent name of design you are trying are trying to create. Don't include dimension though.
2. **Import Libraries:**
   Always include necessary imports, especially `cadquery` and `ocp_vscode` for model visualization.
3. **Define Parameters:**
   Clearly define parameters for the model, such as dimensions and other properties.
4. **Create the CAD Model:**
   Use CadQuery functions to build the CAD model based on the defined parameters.
5. **Save the Model:**
   Save the model in STL, STEP, and DXF formats using `cq.exporters.export`.
6. **Visualize the Model:**
   Use `show()` from the `ocp_vscode` library to visualize the created model.
7. **Example Structure:** 
   ```python
   # filename: box.py
   import cadquery as cq
   from ocp_vscode import *  # Always include this for visualization.

   # Step 1: Define Parameters
   height = 60.0
   width = 80.0
   thickness = 10.0
/home/susil/autogen/Langchain 
   # Step 2: Create the CAD Model
   box = cq.Workplane("XY").box(height, width, thickness)

   # Step 3: Save the Model
   cq.exporters.export(box, "box.stl")
   cq.exporters.export(box.section(), "box.dxf")
   cq.exporters.export(box, "box.step")

   # Step 4: Visualize the Model
   show(box)  # Always use this to visualize the model.
   ``` 
   Here we end the python code block.
''',
    llm_config={"config_list": config_list},
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    description="CadQuery Code Writer who writes python code to create CAD models following the system message.",
)

reviewer_executor = AssistantAgent(
    name="Code Reviewer",
    system_message=''' You are a code review expert. Your role is to ensure that the "Creator" agent's response follows the exact structure and format specified. Check the response against the following guidelines:
    Python Markdown: Make sure the code block are inside python markdown ```python
    File name : Ensure that the filename for python code is mentioned properly as #filename: file_name.py
    Make sure the code executes properly.
    Import Libraries: Verify that the necessary imports, including cadquery and ocp_vscode, are included.
    Define Parameters: Ensure all necessary parameters (e.g., dimensions) are defined clearly.
    Create the CAD Model: Confirm that the model is built correctly using the provided parameters.
    Save the Model: Make sure the model is saved in STL, STEP, and DXF formats.
    Visualize the Model: Check if show() is used for visualization.
    If any step is missing, incorrect, or not following the instructions, provide constructive feedback to the "Creator" agent to correct it.
    Do not forget to execute the codeblock
    Reply `TERMINATE` in the end when code executes successfully ''' ,
    llm_config={"config_list": config_list},
    description="Code Reviewer who can review the python code created and executes it to generate CAD models using CadQuery",
    code_execution_config= {
        "work_dir": "CADs",
        "use_docker": False,
    },
)  

# Function to reset agent
def reset_agents():
     cad_coder.reset()
     reviewer.reset()

# User input and chain execution
user_input = input("Enter the design requirement:")
result = rag_chain.invoke(user_input)

# Combine the information into a single message
combined_message = f"""Design Task:
User's design requirement: {user_input}

Retrived information:( this may not contain the correct information but is the data retrived from the cad query snippets use it as reference for code generation )
{result}

and include show(model) to visualize the code

Please create a CadQuery code implementation for this design following the specified format and guidelines."""

# Initiate chat with a single message
reviewer_executor.initiate_chat(cad_coder, message=combined_message)