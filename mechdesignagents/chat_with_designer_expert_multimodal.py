from autogen import GroupChat, GroupChatManager
# from designer_functions import *
from agents import *
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability
import re

# allowed_transitions = {
#     User: [functioncall_agent,User],
#     functioncall_agent: [User, designer_expert],
#     designer_expert: [cad_coder_assistant],
#     cad_coder_assistant: [cad_coder],
#     cad_coder: [executor],
#     executor: [reviewer],
#     reviewer: [User, cad_coder]  # Can go back to user for approval or cad_coder for fixes
# }

def multimodal_designers_chat(design_problem: str):
    """
    Creates a group chat environment for collaborative design problem solving.

    Args:
        design_problem (str): The design problem to be discussed.

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
        # agents=[User,designer_expert,cad_coder, executor, reviewer,cad_data_reviewer],
        agents=[User,designer_expert,cad_coder, executor, reviewer],

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
        message=design_problem,
    )
    output= rst.chat_history
    stl_filename = None
    for entry in output:
        if entry['name'] == 'CadQuery_Code_Writer' and 'stl' in entry['content']:
            # Find the filename (e.g., plate_with_hole.stl)
            stl_filename_match = re.search(r'\"([^\"]+\.stl)\"', entry['content'])
            if stl_filename_match:
                stl_filename = stl_filename_match.group(1)

    # Define the base path
    base_path = '/home/niel77/MechDesignAgents/mechdesignagents/NewCADs'

    # Append the filename to the path
    if stl_filename:
        full_path = f"{base_path}/{stl_filename}"
        return full_path
    else:
        return None




def main():
    """Main function for running the CAD design chat system."""
    print("\nCAD Design Assistant")
    print("-------------------")
    print("Enter 'exit' to exit the program")
    
    while True:
        try:
            prompt = input("\nEnter your design problem (or 'exit'if you want to exit): ")
            if prompt.lower() == 'exit':
                print("\nExiting CAD Design Assistant")
                break
            multimodal_designers_chat(prompt)
            
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