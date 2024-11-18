from autogen import GroupChat, GroupChatManager
from designer_functions import *
from agents import *



def designers_chat(design_problem: str):
    """
    Initiates a collaborative design discussion between multiple AI agents to solve a given design problem.
    
    This function sets up a structured group chat environment where different specialized agents
    (designer, expert, CAD coder, executor, and reviewer) work together to address design challenges.
    The conversation follows a round-robin pattern where each agent contributes in turn.

    Parameters:
    -----------
    design_problem : str
        The design problem or challenge to be addressed by the group.
        Should be a clear, detailed description of the design requirements or issues.

    Flow:
    -----
    1. Resets all agents to their initial state
    2. Creates a group chat with specialized design agents
    3. Configures chat parameters (rounds, speaker selection, etc.)
    4. Initiates the conversation with the designer agent as the starting point

    Agents:
    -------
    - designer: Main user proxy agent that initiates and guides the discussion
    - designer_expert: Provides specialized design knowledge and best practices
    - cad_coder: Handles technical implementation and CAD-related aspects
    - executor: Responsible for implementing proposed solutions
    - reviewer: Evaluates and validates proposed solutions

    Configuration:
    -------------
    - Maximum rounds: 50
    - Speaker selection: Round-robin (each agent speaks in turn)
    - Repeat speakers: Not allowed
    - LLM configuration: Uses predefined llm_config settings

    Example:
    --------
    >>> problem = "Design a sustainable water bottle that's both eco-friendly and user-friendly"
    >>> designers_chat(problem)
    
    Notes:
    ------
    - Agents must be properly initialized before calling this function
    - The GroupChat and GroupChatManager classes should be imported and configured
    - The llm_config should be properly set up with appropriate model parameters
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