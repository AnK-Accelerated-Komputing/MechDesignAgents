from autogen import ConversableAgent, AssistantAgent, UserProxyAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import cadquery
from ocp_vscode import *
import chromadb
import os
from typing import Dict, List, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Improved config list with better error handling and model selection strategy
config_list = [
    {
        "model": "llama-3.1-8b-instant",
        "api_key": os.getenv("GROQ_API_KEY"),
        "api_type": "groq",
        "context_length": 8192,  # Explicitly define context length
    },
    {
        "model": "gemini-pro",
        "api_key": os.getenv("GEMINI_API_KEY"),
        "api_type": "google",
        "context_length": 8192,
    },
    {
        "model": "llama3-8b-8192",
        "api_key": os.getenv("GROQ_API_KEY"),
        "api_type": "groq",
        "context_length": 8192,
    },
]

# Enhanced LLM configuration with better error handling and retry logic
llm_config = {
    "seed": 25,
    "temperature": 0.1,  # Slightly increased for more creative responses while maintaining consistency
    "config_list": config_list,
    "request_timeout": 600,
    "retry_wait_time": 120,
    "max_retries": 3,  # Add maximum retry attempts
    "context_window": 8192,  # Explicitly set context window
    "timeout": 600,  # Global timeout
}

def termination_msg(message: Union[str, Dict]) -> bool:
    """
    Enhanced termination message checker with better type handling and validation.
    
    Args:
        message: The message to check for termination
        
    Returns:
        bool: True if message indicates termination, False otherwise
    """
    if isinstance(message, dict):
        content = str(message.get("content", "")).upper()
        return "TERMINATE" in content or "TASK COMPLETED" in content
    return False

# Enhanced work directory configuration
WORK_DIR = os.path.join(os.getcwd(), "NewCADs")
os.makedirs(WORK_DIR, exist_ok=True)

# Improved code execution configuration
code_execution_config = {
    "work_dir": WORK_DIR,
    "use_docker": False,
    "timeout": 300,  # 5 minutes timeout for code execution
    "last_n_messages": 3,  # Consider last 3 messages for context
}
# Designer's enhanced system message
designer = UserProxyAgent(
    name="Designer",
    is_termination_msg=termination_msg,
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=5,
    code_execution_config=code_execution_config,
    llm_config=llm_config,
    system_message="""You are a CAD design expert working exclusively with CadQuery for Python. Your role is to:
    1. Specify exact dimensional requirements for CadQuery modeling
    2. Define geometric features in terms of CadQuery operations (workplane, sketch, extrude, etc.)
    3. Validate that generated models meet requirements
    
    When specifying requirements, always include:
    - Base workplane selection (XY, YZ, or XZ)
    - Precise dimensions in millimeters
    - Required CadQuery operations (e.g., extrude, revolve, sweep, loft)
    - Feature relationships and constraints
    
    Reply TERMINATE if the CadQuery model meets all requirements.
    Reply CONTINUE with specific feedback about CadQuery implementation if adjustments are needed.
    
    Each design request must specify:
    - Primary workplane and coordinate system
    - Critical dimensions
    - Required CadQuery features and operations
    - Success criteria in terms of CadQuery model attributes""",
    description="Expert CAD designer specializing in CadQuery implementations",
)

# Designer Expert's enhanced system message
designer_expert = AssistantAgent(
    name="Designer Expert",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    llm_config=llm_config,
    system_message="""You are a CadQuery implementation specialist. Analyze design requirements and provide CadQuery-specific solutions.

    For each design request:
    1. CadQuery Requirements Analysis:
       - Base workplane selection
       - Required CadQuery operations (sketch, extrude, fillet, etc.)
       - Feature sequence and dependencies
       - Dimensional constraints
    
    2. CadQuery Solution Architecture:
       - Workplane setup and coordinate system
       - Feature tree organization
       - Boolean operations sequence
       - Construction geometry requirements
    
    3. CadQuery Implementation Strategy:
       - Sketch profiles and constraints
       - Solid modeling operations
       - Pattern and transform operations
       - Assembly structure (if needed)
    
    Format responses as:
    CADQUERY SETUP:
    - Workplane: [XY/YZ/XZ]
    - Origin: [Coordinate system setup]
    - Units: [mm/inches]
    
    FEATURE SEQUENCE:
    1. [First CadQuery operation]
    2. [Second CadQuery operation]
    ...
    
    IMPLEMENTATION NOTES:
    - [CadQuery-specific considerations]
    - [Performance optimization notes]
    - [Common pitfalls to avoid]""",
    description="CadQuery implementation strategist",
)

# CAD Coder's enhanced system message
cad_coder = AssistantAgent(
    name="CadQuery Code Writer",
    system_message="""You are a CadQuery programming expert. Generate clean, efficient CadQuery code following these requirements:

    Code Structure:
    1. Required Imports:
       ```python
       import cadquery as cq
       from ocp_vscode import *
       ```
    
    2. CadQuery Best Practices:
       - Use proper workplane management
       - Implement selective operations
       - Chain operations efficiently
       - Use variables for parametric design
       - Apply proper constraints in sketches
    
    3. Feature Implementation:
       - Start with base workplane
       - Create clean sketch profiles
       - Use efficient solid operations
       - Apply transforms and patterns
       - Add finish features (fillets, chamfers)
    
    4. Code Organization:
       ```python
       # filename: component_name.py
       import cadquery as cq
       from ocp_vscode import *
       
       # Parameters
       params = {
           "length": 100.0,  # mm
           "width": 50.0,    # mm
           "height": 25.0    # mm
       }
       
       # Create base feature
       result = (cq.Workplane("XY")
                .box(params["length"], 
                    params["width"], 
                    params["height"])
       )
       
       # Export
       cq.exporters.export(result, "output.step")
       
       # Display
       show(result)
       ```
    
    Always include:
    - Parameter definitions
    - Clear operation chaining
    - proper workplane management
    - Export to standard formats
    - Model visualization""",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

designer_aid = RetrieveUserProxyAgent(
    name="Designer_Assistant",
    is_termination_msg=termination_msg,
    human_input_mode="ALWAYS",
    llm_config=llm_config,
    retrieve_config={
        "task": "code",
        "docs_path": [
            "/home/niel77/MechanicalAgents/data/code_documentation.pdf",
        ],
        "chunk_token_size": 1000,  # Increased for better context
        "collection_name": "groupchat",
        "get_or_create": True,
        "similarity_threshold": 0.75,  # Add similarity threshold
        "num_relevant_chunks": 5,  # Specify number of relevant chunks to retrieve
    },
    code_execution_config=False,
)

# Reviewer's enhanced system message
reviewer = AssistantAgent(
    name="Code Reviewer",
    is_termination_msg=termination_msg,
    system_message="""You are a CadQuery code review specialist. Review code for:

    1. CadQuery Best Practices:
       - Proper workplane usage
       - Efficient operation chaining
       - Correct constraint application
       - Appropriate feature sequence
       - Parameter organization
    
    2. Code Quality:
       - Clear parameter definitions
       - Proper operation chain structure
       - Error handling for CadQuery operations
       - Documentation of critical steps
    
    3. Model Validation:
       - Proper base workplane selection
       - Correct feature sequence
       - Appropriate use of CadQuery operations
       - Export format implementation
    
    Review Checklist:
    WORKPLANE MANAGEMENT:
    - [ ] Appropriate base workplane
    - [ ] Proper workplane transitions
    - [ ] Clear coordinate system usage
    
    OPERATIONS:
    - [ ] Efficient operation chaining
    - [ ] Appropriate boolean operations
    - [ ] Proper sketch constraints
    - [ ] Correct transformation usage
    
    CODE STRUCTURE:
    - [ ] Clear parameter organization
    - [ ] Proper operation sequence
    - [ ] Error handling
    - [ ] Documentation
    
    Reply TERMINATE only when code meets all CadQuery standards.""",
    llm_config=llm_config,
    code_execution_config=code_execution_config,
)

def reset_agents() -> None:
    """Reset all agents to their initial state."""
    try:
        for agent in [designer, designer_aid,designer_expert, cad_coder, reviewer]:
            agent.reset()
        logger.info("All agents reset successfully")
    except Exception as e:
        logger.error(f"Error resetting agents: {str(e)}")
        raise