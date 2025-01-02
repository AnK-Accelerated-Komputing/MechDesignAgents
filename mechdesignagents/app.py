from autogen import GroupChat, GroupChatManager
# from designer_functions import *
from agents_v3 import *
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability

def multimodal_designers_chat(image_path: str):
    """
    Creates a group chat environment for collaborative design problem solving.

    Args:
        image_path(str): The image path for which model is to be created.

    Required Agents:
        - designer
        - designer_expert
        - cad_coder
        - executor
        - reviewer
        - cad_reviewer

    Configuration:
        - max_round: 50
        - speaker_selection: round_robin
        - allow_repeat_speaker: False

    Example:
        >>> designers_chat("Design a water bottle")
    """
    reset_agents()
    groupchat = GroupChat(
        agents=[User,drawing_recognizer,dimension_extractor,verifier,designer_expert,cad_coder, executor, reviewer],
        messages=[],
        max_round=50,
        # speaker_selection_method="round_robin",
        speaker_selection_method="auto",
        allow_repeat_speaker=False,
        func_call_filter=True,
        select_speaker_auto_verbose=False,
        send_introductions= True, 
        # allowed_or_disallowed_speaker_transitions=allowed_transitions,
        # speaker_transitions_type="allowed"
    )
    vision_capability = VisionCapability(lmm_config=llm_config)
    group_chat_manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    vision_capability.add_to_agent(group_chat_manager)

    rst = User.initiate_chat(
        group_chat_manager,
        message=f"<img {image_path}>",
    )
    print(rst.cost)



def main():
    """Main function for running the CAD creation  system."""
    print("\n Let's create CAD")
    print("-------------------")
    print("Enter 'exit' to exit the program")
    
    while True:
        try:
            image_path = input("\nEnter the path to the image for CAD model creation (or 'exit'if you want to exit): ")
            if image_path.lower() == 'exit':
                print("\nExiting CAD creation  system")
                break
            multimodal_designers_chat(image_path)
            
        except KeyboardInterrupt:
            print("\nSession interrupted by user")
            break
        except ValueError as ve:
            print(f"\nError: {str(ve)}")
            print("Please try again with a more detailed prompt")
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try again or create github issues if the problem persists")

if __name__ == "__main__":
    main()