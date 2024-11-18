from autogen.agentchat.contrib.llava_agent import LLaVAAgent
from autogen import UserProxyAgent
import os
import base64

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading image: {e}")
        return None

# Groq LLaVA configuration
llava_config_list = [
    {
        "model": "llava-v1.5-7b-4096-preview",
        "api_key": os.environ["GROQ_API_KEY"],
        "api_type": "groq",
        "base_url": "https://api.groq.com/openai/v1",
    }
]

# Create the drawing expert agent
drawing_expert = LLaVAAgent(
    name="Drawing Expert",
    max_consecutive_auto_reply=10,
    system_message="""You are a CAD drawing expert who translates image provided by user into detailed drawing specifications.  
    Provide dimensions, tolerances, materials, and other necessary information for creating a professional engineering drawing.  
    Always respond in a structured format, separating different aspects of the drawing clearly.""",
    llm_config={
        "config_list": llava_config_list,
        "temperature": 0.5,
        "max_new_tokens": 1000
    }
)

def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

user_proxy = UserProxyAgent(
    name="User",
    is_termination_msg=termination_msg,
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=5,
    code_execution_config=False,
    system_message="""You are a user who provides engineering drawing descriptions."""
)

# Initialize the chat with proper error handling
image_path = "/home/niel77/MechanicalAgents/mechdesignagents/images/Drawing-of-Connecting-rod-Optimized.png"

try:
    # Verify image exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Convert image to base64
    base64_image = image_to_base64(image_path)
    if base64_image is None:
        raise ValueError("Failed to convert image to base64")
    
    # Prepare the message with the correct format for LLaVA
    message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Provide me all the details of this engineering drawing."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        ]
    }
    
    # Initiate the chat
    user_proxy.initiate_chat(
        drawing_expert,
        message=message
    )

except Exception as e:
    print(f"Error occurred: {str(e)}")
    print(f"Error type: {type(e)}")
    import traceback
    print(f"Full traceback:\n{traceback.format_exc()}")