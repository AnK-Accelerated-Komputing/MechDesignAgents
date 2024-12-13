import autogen
import base64
import os
import json
from datetime import datetime
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability

from typing import Dict, Annotated, Any
import ollama
from pathlib import Path

# Global variable to store current image path
CURRENT_IMAGE_PATH = None

# Configuration for language models
config_list = [
    {
        "model": "gpt-4o-0806",
        "api_key": os.environ["AZURE_API_KEY"],
        "base_url": os.environ["AZURE_OPENAI_BASE"],
        "api_type": "azure",
        "api_version": "2024-08-01-preview"
    }
]

llm_config = {"config_list": config_list}

# User Proxy Agent
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "coding", "use_docker": False}
)

drawing_recognizer= MultimodalConversableAgent(
    name= "Drawing_Recognition_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are a Drawing Recognition Agent. Your task is to identify all the views (e.g., front, top, side) present in an engineering drawing 
    image and their respective positions within the image. Recognize geometric shapes, features, and annotations such as lines, arcs, and text. 
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
blank_size_predictor = autogen.AssistantAgent(
    name= "Blank_Size_Predictor_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are a Blank_Size_Predictor_Agent. Your task is to predict the optimum size of the blank required for 
    manufacturing based on the verified dimensions of all views. Analyze the combined dimensions and 
    determine whether the blank should be rectangular or cylindrical. 
    Provide the predicted blank size, and shape in JSON format
    """
)

price_predictor = autogen.AssistantAgent(
    name= "Price_Predictor_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are a Price Predictor Agent. Your task is to predict the price of the blank based on the material and 
    dimensions provided in the Blank_Size_Predictor_Agent's output. 
    If the material or price per unit volume is not provided, ask the user for clarification. 
    If no input is available, make a reasonable prediction based on standard materials and pricing. 
    Return the predicted price in JSON format.
    """
)

formatter = autogen.AssistantAgent(
    name= "Formatting_and_Output_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    Use the verified dimensions provided by the Verification Agent to format the results into a clear and structured output. 
    Include dimension names (e.g., width, height), values, and units (if present). 
    Provide the formatted results for final review by the User_proxy.
    """
)

general_qa = autogen.AssistantAgent(
    name= "GEneral_Query_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You answer general queries on the drawing prompted by the User.
    """
)

def process_engineering_drawing(question: str,image_path) -> None:
    """Process an engineering drawing through multi-agent system."""
    groupchat = autogen.GroupChat(agents=[user_proxy, drawing_recognizer, dimension_extractor, verifier,blank_size_predictor,price_predictor,general_qa], messages=[], max_round=20)

    vision_capability = VisionCapability(lmm_config={"config_list": config_list, "temperature": 0.3, "max_tokens": 1024})
    group_chat_manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    vision_capability.add_to_agent(group_chat_manager)

    rst = user_proxy.initiate_chat(
        group_chat_manager,
        message=f"""{question}:
                            <img {image_path}>.""",
    )
    print(rst.cost)

def validate_image_path(image_path: str) -> bool:
    """Validate if the image file exists and is an image file"""
    valid_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    path = Path(image_path)
    return path.exists() and path.suffix.lower() in valid_extensions

def set_image_path(path: str) -> bool:
    """Set the global image path after validation"""
    global CURRENT_IMAGE_PATH
    if validate_image_path(path):
        CURRENT_IMAGE_PATH = path
        return True
    return False

if __name__ == "__main__":
    while True:
        # Get image path from user
        image_path = input("Enter the path to your engineering drawing (or 'exit' to exit): ")
        if image_path.lower() == 'exit':
            break

        # Set and validate image path
        if not set_image_path(image_path):
            print("Invalid image path or unsupported format. Please try again.")
            continue

        # Get question from user
        question = input("Enter your question about the drawing: ")
        
        # Process the drawing
        try:
            process_engineering_drawing(question, image_path)
        except Exception as e:
            print(f"Error processing drawing: {e}")
            continue

        # Ask if user wants to analyze another drawing
        another = input("\nWould you like to analyze another drawing? (yes/no): ")
        if another.lower() != 'yes':
            break