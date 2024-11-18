from autogen import GroupChat, GroupChatManager
from designer_functions import *
from mechdesignagents.tests.claude_agents import *
from typing import Optional, Dict
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_design_prompt(prompt: str) -> bool:
    """
    Validate the design prompt before processing.
    
    Args:
        prompt (str): The design problem prompt
        
    Returns:
        bool: True if prompt is valid, raises ValueError otherwise
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Design prompt must be a non-empty string")
    if len(prompt.strip()) < 10:
        raise ValueError("Design prompt is too short. Please provide more details.")
    return True

def format_design_prompt(prompt: str) -> str:
    """
    Format the design prompt to provide better context to the agents.
    
    Args:
        prompt (str): Original design prompt
        
    Returns:
        str: Formatted prompt with additional context
    """
    return f"""CAD Design Request:
{prompt}

Please follow this structured workflow:
1. Designer Expert: 
   - Analyze requirements
   - Break down the geometry
   - Propose implementation approach
   
2. CAD Coder:
   - Implement solution based on expert analysis
   - Follow coding standards
   - Include proper documentation
   
3. Reviewer:
   - Validate implementation
   - Check code quality
   - Verify manufacturability
   
4. Designer:
   - Final approval
   - Request revisions if needed

Requirements:
- All dimensions must be specified
- Consider manufacturing constraints
- Include proper documentation
- Follow CadQuery best practices
"""

def norag_chat(design_problem: str, max_rounds: int = 12) -> None:
    """
    Execute a group chat for CAD design without RAG agent.
    
    Args:
        design_problem (str): The design problem to solve
        max_rounds (int, optional): Maximum number of chat rounds. Defaults to 12.
    """
    try:
        # Validate input
        validate_design_prompt(design_problem)
        
        # Log start of session
        logger.info("Starting new CAD design session")
        start_time = time.time()
        
        # Reset agents
        logger.info("Resetting agents")
        reset_agents()
        
        # Format the design prompt
        formatted_prompt = format_design_prompt(design_problem)
        
        # Initialize group chat with optimal settings
        groupchat = GroupChat(
            agents=[designer, designer_expert, cad_coder, reviewer],
            messages=[],
            max_round=max_rounds,
            speaker_selection_method="round_robin",  # More predictable for CAD workflow
            allow_repeat_speaker=False,
        )
        
        # Initialize manager with enhanced configuration
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={
                **llm_config,  # Base config from agents.py
                "max_retries": 3,
                "retry_wait_time": 60,
            }
        )
        
        # Start the chat
        logger.info("Initiating group chat")
        designer.initiate_chat(
            manager,
            message=formatted_prompt,
        )
        
        # Log completion
        duration = time.time() - start_time
        logger.info(f"CAD design session completed in {duration:.2f} seconds")
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Error during chat execution: {str(e)}")
        raise

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
                
            logger.info(f"Received design prompt: {prompt[:100]}...")
            norag_chat(prompt)
            
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