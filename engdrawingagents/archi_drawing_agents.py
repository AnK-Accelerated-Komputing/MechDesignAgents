import autogen
import os
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability
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

boundary_recognizer= MultimodalConversableAgent(
    name= "BoundaryRecognitionAgent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are an agent specialized in recognizing the outer boundary of floor plans. 
    Analyze the drawing to identify the outer walls, dimensions, and any entrances (e.g., doors). 
    Provide this information in JSON format, specifying the type and location of entrances.
    """
)

room_recognizer = MultimodalConversableAgent(
    name= "RoomRecognitionAgent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are an agent designed to recognize rooms within a floor plan. Using the boundary information provided by BoundaryRecognitionAgent, detect the rooms, their dimensions, and their relative positions. 
    Assign appropriate labels (e.g., 'Living Room', 'Bedroom') based on size and context. Return the data in JSON format.
    """
)

room_feature_recognizer = MultimodalConversableAgent(
    name= "RoomFeatureAgent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are an agent tasked with analyzing room features. For each room recognized by RoomRecognitionAgent, identify walls, windows (gaps in the walls), and doors. 
    Provide their locations, dimensions, and align them with room data. Return the details in JSON format.
    """
)

furniture_fixture_recognizer = MultimodalConversableAgent(
    name= "FurnitureAndFixtureAgent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are an agent for identifying furniture and fixtures in floor plans. For each room whose walls and doors have been recognized by RoomFeatureAgent, detect items such as kitchen counters, sinks, stoves, toilets, and bathtubs. 
    Specify their type, location, and dimensions. Integrate the output with the room data and return in JSON format.
    """
)

verifier = MultimodalConversableAgent(
    name= "Verification_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    You are a verification agent tasked with validating JSON data from previous agents. 
    Cross-check the JSON output with the floor plan drawing to ensure consistency in dimensions, room names, feature placements, and relative positions.
    Highlight any discrepancies and provide a corrected JSON output if necessary
    """
)

formatter = autogen.AssistantAgent(
    name= "Formatting_and_Output_Agent",
    # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config = False,
    llm_config=llm_config,
    system_message="""
    Use the verified JSON data provided by the Verification Agent to consolidate all the results into a clear and structured JSON output. 
    Provide the formatted results for final review by the User_proxy.
    """
)

general_qa = autogen.AssistantAgent(
    name= "General_Query_Agent",
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
    groupchat = autogen.GroupChat(agents=[user_proxy, boundary_recognizer, room_recognizer, room_feature_recognizer, furniture_fixture_recognizer, verifier, formatter, general_qa], messages=[], max_round=20)

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
        image_path = input("Enter the path to your architectural drawing (or 'exit' to exit): ")
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
        if another.lower() != ('yes' or 'y'):
            break