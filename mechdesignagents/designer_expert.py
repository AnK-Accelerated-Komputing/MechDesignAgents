from autogen import GroupChat, GroupChatManager
from designer_functions import *
from agents import *



def designers_chat(design_problem: str):
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

    Configuration:
        - max_round: 50
        - speaker_selection: round_robin
        - allow_repeat_speaker: False

    Example:
        >>> designers_chat("Design a water bottle")
    """
    reset_agents()
    groupchat = GroupChat(
        agents=[designer, designer_expert, cad_coder, executor, reviewer],
        messages=[],
        max_round=50,
        speaker_selection_method="round_robin",
        # speaker_selection_method="auto",
        allow_repeat_speaker=False,
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the designer as this is the user proxy agent.
    designer.initiate_chat(
        manager,
        message=design_problem,
    )

def main():
    """Main function for running the CAD design chat system."""
    print("\nCAD Design Assistant")
    print("-------------------")
    print("Enter 'quit' to exit the program")
    
    while True:
        try:
            prompt = input("\nEnter your design problem: ")
            if prompt.lower() == 'quit':
                print("\nExiting CAD Design Assistant")
                break
            designers_chat(prompt)
            
        except KeyboardInterrupt:
            print("\nSession interrupted by user")
            break
        except ValueError as ve:
            print(f"\nError: {str(ve)}")
            print("Please try again with a more detailed prompt")
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try again or contact support if the issue persists")

if __name__ == "__main__":
    main()