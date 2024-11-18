import autogen
import base64
import os
from groq import Groq
from typing import Dict, List, Union, Literal
from rich.console import Console
from rich.markdown import Markdown

def analyze_drawing_with_groq(
    image_url: str,
    prompt: str,
    analysis_type: Literal["general", "verification", "final"] = "general"
) -> str:
    """
    Analyze an engineering drawing using Groq's vision model.
    
    Args:
        image_url: Path to the image file
        prompt: Specific prompt for the analysis
        analysis_type: Type of analysis to perform
        
    Returns:
        str: Analysis response from Groq
    """
    # Read and encode the image
    with open(image_url, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        image_data_url = f"data:image/png;base64,{encoded_image}"
    
    # Enhance prompt based on analysis type
    enhanced_prompt = prompt
    if analysis_type == "verification":
        enhanced_prompt = f"Verify the following in the engineering drawing: {prompt}. Focus on measurement accuracy and cross-view consistency."
    elif analysis_type == "final":
        enhanced_prompt = f"Provide a final confirmation of: {prompt}. Include all critical dimensions and specifications."
    
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
                        "text": enhanced_prompt
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
    
    return completion.choices[0].message.content

def create_agents(image_url: str, config_list: List[Dict]):
    # Define function schema for AutoGen
    function_map = {
        "analyze_drawing_with_groq": {
            "name": "analyze_drawing_with_groq",
            "description": "Analyze an engineering drawing using Groq vision model",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "Path to the engineering drawing image"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Analysis prompt for the drawing"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["general", "verification", "final"],
                        "description": "Type of analysis to perform"
                    }
                },
                "required": ["image_url", "prompt"]
            }
        }
    }

    # Create function calling config
    llm_config = {
        "config_list": config_list,
        "functions": list(function_map.values()),
        "timeout": 120
    }

    # Primary analyzer agent
    primary_analyzer = autogen.AssistantAgent(
        name="primary_analyzer",
        system_message="""You are an engineering drawing analyst. Follow these steps:
        1. When you receive a question about the drawing, call analyze_drawing_with_groq with analysis_type="general"
        2. Extract key dimensions, tolerances, and specifications from the response
        3. Present findings clearly and ask verification_agent to check critical measurements
        4. Always specify which views and dimensions need verification""",
        llm_config=llm_config,
        function_map=function_map
    )

    # Verification agent
    verification_agent = autogen.AssistantAgent(
        name="verification_agent",
        system_message="""You are a verification specialist. Follow these steps:
        1. When asked to verify measurements, call analyze_drawing_with_groq with analysis_type="verification"
        2. Focus on verifying specific measurements across different views
        3. Compare dimensions and tolerances for consistency
        4. Report findings to final_reporter with clear confirmation or discrepancies""",
        llm_config=llm_config,
        function_map=function_map
    )

    # Final reporter agent
    final_reporter = autogen.AssistantAgent(
        name="final_reporter",
        system_message="""You are a technical documentation specialist. Follow these steps:
        1. After receiving verified information, call analyze_drawing_with_groq with analysis_type="final"
        2. Compile a comprehensive report including:
           - All verified critical dimensions
           - Material specifications
           - Tolerances and allowances
           - Important notes or warnings
        3. Present the report in a clear, structured format
        4. End your report with TERMINATE""",
        llm_config=llm_config,
        function_map=function_map
    )

    # User proxy agent
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False,
        function_map=function_map
    )

    return primary_analyzer, verification_agent, final_reporter, user_proxy

def process_engineering_drawing(image_url: str, question: str) -> None:
    """
    Process an engineering drawing through the multi-agent system.
    """
    # Configure the agents
    config_list = [
    {

        "model": "llama-3.2-90b-vision-preview",
        "api_key":  os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    },
    {
        "model": 'gemini-pro',
        "api_key": os.environ["GEMINI_API_KEY"],  # Replace with your API key variable
        "api_type": "google",
    },
    {

        "model": "llama3-8b-8192",
        "api_key":  os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    },
    
]
    
    # Create agents with registered functions
    primary_analyzer, verification_agent, final_reporter, user_proxy = create_agents(image_url, config_list)
    
    # Set up the group chat
    groupchat = autogen.GroupChat(
        agents=[user_proxy, primary_analyzer, verification_agent, final_reporter],
        messages=[],
        max_round=10
    )
    manager = autogen.GroupChatManager(groupchat=groupchat)
    
    # Create the initial message with the image URL included
    initial_message = {
        "content": f"""Please analyze this engineering drawing regarding: {question}
        
        The drawing is located at: {image_url}
        
        Primary Analyzer: Start with a general analysis of the drawing.
        Verification Agent: Wait for specific measurements to verify.
        Final Reporter: Compile the final report after verification.""",
        "role": "user"
    }
    
    # Start the conversation
    user_proxy.initiate_chat(manager, message=initial_message)

# Example usage
if __name__ == "__main__":
    # Example usage
    image_url = "/home/niel77/MechanicalAgents/mechdesignagents/images/Drawing-of-the-connecting-rod_W640.jpg"
    question = "What are the critical dimensions and material specifications of this connecting rod?"
    
    process_engineering_drawing(image_url, question)