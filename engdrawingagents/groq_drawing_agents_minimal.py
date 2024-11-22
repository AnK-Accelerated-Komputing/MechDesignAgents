import autogen
import base64
import os
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from typing import Dict, Annotated
from groq import Groq
import chromadb
from pathlib import Path


# Configure the agents
config_list = [
    {
        "model": "llama3-groq-70b-8192-tool-use-preview",
        "api_key": os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    },
    {
        "model": 'gemini-pro',
        "api_key": os.environ["GEMINI_API_KEY"],
        "api_type": "google",
    },
    {
        "model": "llama3-8b-8192",
        "api_key": os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    }
]
llm_config = {"config_list": config_list}


# User Proxy Agent
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "coding", "use_docker": False}
)

# Primary Analyzer
primary_analyzer = autogen.AssistantAgent(
    name="primary_analyzer",
    system_message="""You are an expert Engineering drawing analyst that:
    1. Receives query from user about drawing
    2. Always calls tool analyze_drawing_with_groq to get initial answer
    3. Formats response as:
       - GROQ ANALYSIS: [groq response]
       - MY FINDINGS: [interpretation]
    4. Passes findings to verification agent""",
    llm_config=llm_config
)

# Verification Agent
verification_agent = autogen.AssistantAgent(
    name="verification_agent",
    system_message=f"""You are a Verification specialist that:
    1. Receives analysis from primary_analyzer
    2. Always verifies each finding using calling tool analyze_drawing_again_with_groq. For example:
    if you receive that there are two view in the drawing at image_path, you will call tool 
    analyze_drawing_again_with_groq with image_path argument containing the image url and prompt asking if there are two just two views in the drawing.
    3. Reports as:
       - VERIFICATION CHECK: [groq verification response]
       - STATUS: [Confirmed/Discrepancy Found]
    4. If confirmed, presents final answer as 
        - FINAL ANSWER: [final answer]
        """,
    llm_config=llm_config
)


# Register the analyze_drawing function with all agents
@user_proxy.register_for_execution()
@primary_analyzer.register_for_llm(description="Analyze engineering drawing using Groq vision model for getting as much detail of the drawing as possible")
def analyze_drawing_with_groq(
    image_url: Annotated[str, "Path to the engineering drawing image"],
    prompt: Annotated[str, "Analysis prompt for the drawing"],
) -> Dict[str, str]:
    try:
        # Read and encode the image
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_data_url = f"data:image/png;base64,{encoded_image}"
       
        # Initialize Groq client
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        
        # Create completion request
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            temperature=0,
            max_tokens=1024,
        )
        
        return {
            "groq_response": completion.choices[0].message.content,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "groq_response": None,
            "status": "error",
            "error_message": str(e)
        }

def process_engineering_drawing(image_url: str, question: str) -> None:
    """
    Process an engineering drawing through the multi-agent system.
    """
    groupchat = autogen.GroupChat(
    agents=[user_proxy, primary_analyzer, verification_agent],
    speaker_selection_method="round_robin",
    messages=[],
    max_round=20
    )   
    manager = autogen.GroupChatManager(groupchat=groupchat)
    
    initial_message = {
        "content": f"""Please analyze this drawing at {image_url} with the question: {question}

        Follow this exact sequence:
        1. primary_analyzer: Use analyze_drawing_again_with_groq to analyze the drawing
        2. primary_analyzer: Share findings with verification_agent
        3. verification_agent: Verify the findings using analyze_drawing_with_groq
        4. verification_agent: If verified, present final answer
        
        Begin analysis now.
        """,
        "role": "user"
    }
    
    user_proxy.initiate_chat(manager, message=initial_message)

@user_proxy.register_for_execution()
@verification_agent.register_for_llm(description="Analyze engineering drawing using Groq vision model again for verifying your queries on details of drawing")
def analyze_drawing_again_with_groq(
    image_url: Annotated[str, "Path to the engineering drawing image"],
    prompt: Annotated[str, "Analysis prompt for the drawing"],
) -> Dict[str, str]:
    try:
        # Read and encode the image
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_data_url = f"data:image/png;base64,{encoded_image}"
            
        # Initialize Groq client
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        
        # Create completion request
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            temperature=0,
            max_tokens=1024,
        )
        
        return {
            "groq_response": completion.choices[0].message.content,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "groq_response": None,
            "status": "error",
            "error_message": str(e)
        }

def validate_image_path(image_path: str) -> bool:
    """Validate if the image file exists and is an image file"""
    valid_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    path = Path(image_path)
    return path.exists() and path.suffix.lower() in valid_extensions

if __name__ == "__main__":
    while True:
        # Get image path from user
        image_path = input("Enter the path to your engineering drawing (or 'quit' to exit): ")
        if image_path.lower() == 'quit':
            break

        # Validate image path
        if not validate_image_path(image_path):
            print("Invalid image path or unsupported format. Please try again.")
            continue

        # Get question from user
        question = input("Enter your question about the drawing: ")
        
        # Process the drawing
        try:
            process_engineering_drawing(image_path, question)
        except Exception as e:
            print(f"Error processing drawing: {e}")
            continue

        # Ask if user wants to analyze another drawing
        another = input("\nWould you like to analyze another drawing? (yes/no): ")
        if another.lower() != 'yes':
            break