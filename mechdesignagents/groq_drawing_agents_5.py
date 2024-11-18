import autogen
import base64
import os
from groq import Groq
from typing import Dict, List, Union, Literal, Annotated

# Configure the agents
config_list = [
    {
        "model": "llama3-groq-70b-8192-tool-use-preview",
        "api_key": os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    },
    {
        "model": 'gemini-pro',
        "api_key": os.environ["GEMINI_API_KEY"],
        "api_type": "google",
    },
    {
        "model": "llama3-8b-8192",
        "api_key": os.environ["GROQ_API_KEY"],
        "api_type": "groq", 
    }
]

# Create user proxy
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "coding", "use_docker": False}
)

# Create the primary agents
primary_analyzer = autogen.AssistantAgent(
    name="primary_analyzer",
    system_message="""You are an expert engineering drawing analyst. Your task is to thoroughly analyze the drawing by:

    1. FIRST ANALYSIS:
    - Call analyze_drawing_with_groq with a prompt to identify number of views and basic layout
    - Call again with a prompt specifically for material specifications
    - Call once more for major dimensions
    
    2. DETAILED EXAMINATION:
    - For each unclear detail, call analyze_drawing_with_groq with specific focused prompts
    - Ask about manufacturing notes, tolerances, or surface finishes separately
    
    3. COMPILATION:
    - Clearly state "GROQ VISION ANALYSIS:" before each Groq response
    - After each response, say "MY INTERPRETATION:" and explain what you found
    - Organize findings into: Views, Dimensions, Materials, and Special Notes
    
    4. HANDOFF:
    - List specific measurements for verification_agent to check
    - Highlight any unclear areas needing extra verification
    
    Remember: Make multiple, specific calls to analyze_drawing_with_groq as needed. Don't try to get everything in one call.""",
    llm_config={"config_list": config_list}
)

verification_agent = autogen.AssistantAgent(
    name="verification_agent",
    system_message="""You are a meticulous verification specialist. Your process must be:

    1. SYSTEMATIC VERIFICATION:
    - Take each measurement from primary_analyzer
    - Call analyze_drawing_with_groq separately for EACH dimension with very specific prompts
    - For each critical dimension, check it in multiple views if possible
    
    2. CROSS-REFERENCING:
    - Call analyze_drawing_with_groq to verify relationships between dimensions
    - Verify tolerances and special specifications separately
    - Check for consistency across different views
    
    3. REPORTING:
    - State "GROQ VERIFICATION RESULTS:" before each response
    - For each verification, state "VERIFICATION STATUS:" as Confirmed/Discrepancy Found
    - If discrepancy found, call analyze_drawing_with_groq again with more focused prompt
    
    4. SUMMARY:
    - Create list of all verified dimensions with confidence levels
    - Note any discrepancies or uncertainties found
    
    Make multiple, specific calls to analyze_drawing_with_groq. Each call should focus on one aspect.""",
    llm_config={"config_list": config_list}
)

final_reporter = autogen.AssistantAgent(
    name="final_reporter",
    system_message="""You are a precise technical documentation specialist. Your reporting process must be:

    1. INITIAL REVIEW:
    - Review all verified information from previous agents
    - Call analyze_drawing_with_groq for any missing critical details
    
    2. VERIFICATION COMPLETION:
    - For any uncertain measurements, call analyze_drawing_with_groq with specific queries
    - Double-check critical specifications with focused prompts
    
    3. REPORT COMPILATION:
    - Start with "FINAL REPORT:"
    - Organize into sections: Overview, Critical Dimensions, Material Specifications, Manufacturing Notes
    - For each uncertain item, call analyze_drawing_with_groq for final verification
    
    4. QUALITY CHECK:
    - Review report for completeness
    - Call analyze_drawing_with_groq for final confirmation of critical details
    - Add confidence levels for each major specification
    
    End with "TERMINATE" only after ALL specifications are verified. Make multiple calls to analyze_drawing_with_groq as needed.""",
    llm_config={"config_list": config_list}
)

# Register the analyze_drawing function with all agents
@user_proxy.register_for_execution()
@primary_analyzer.register_for_llm(description="Analyze engineering drawing using Groq vision model for getting as much detail of the drawing as possible")
def analyze_drawing_with_groq(
    image_url: Annotated[str, "Path to the engineering drawing image"],
    prompt: Annotated[str, "Analysis prompt for the drawing"],
) -> Dict[str, str]:
    try:
        # Read and encode the image
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_data_url = f"data:image/png;base64,{encoded_image}"
       
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
                            "text": prompt
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
        
        return {
            "groq_response": completion.choices[0].message.content,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "groq_response": None,
            "status": "error",
            "error_message": str(e)
        }

def process_engineering_drawing(image_url: str, question: str) -> None:
    """
    Process an engineering drawing through the multi-agent system.
    """
    groupchat = autogen.GroupChat(
        agents=[user_proxy, primary_analyzer, verification_agent, final_reporter],
        speaker_selection_method = "round_robin",
        messages=[],
        max_round=10,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat)
    
    initial_message = {
        "content": f"""Analyze this engineering drawing at {image_url} regarding: {question}

        IMPORTANT: 
        - Make multiple, specific calls to analyze_drawing_with_groq as needed
        - Each call should focus on one specific aspect or measurement
        - Verify all critical dimensions in multiple views where possible
        - Do not rely on a single function call for all information
        - Cross-verify important specifications""",
        "role": "user"
    }
    
    user_proxy.initiate_chat(manager, message=initial_message)

@user_proxy.register_for_execution()
@verification_agent.register_for_llm(description="Analyze engineering drawing using Groq vision model for verifying your queries on details of drawing")
def analyze_drawing_with_groq(
    image_url: Annotated[str, "Path to the engineering drawing image"],
    prompt: Annotated[str, "Analysis prompt for the drawing"],
) -> Dict[str, str]:
    try:
        # Read and encode the image
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_data_url = f"data:image/png;base64,{encoded_image}"
            
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
                            "text": prompt
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
        
        return {
            "groq_response": completion.choices[0].message.content,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "groq_response": None,
            "status": "error",
            "error_message": str(e)
        }


@user_proxy.register_for_execution()
@final_reporter.register_for_llm(description="Analyze engineering drawing using Groq vision model for creating a final report of the drawing")
def analyze_drawing_with_groq(
    image_url: Annotated[str, "Path to the engineering drawing image"],
    prompt: Annotated[str, "Analysis prompt for the drawing"],
) -> Dict[str, str]:
    try:
        # Read and encode the image
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_data_url = f"data:image/png;base64,{encoded_image}"
        
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
                            "text": prompt
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
        
        return {
            "groq_response": completion.choices[0].message.content,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "groq_response": None,
            "status": "error",
            "error_message": str(e)
        }

# Example usage
if __name__ == "__main__":
    image_url = "/home/niel77/MechanicalAgents/mechdesignagents/images/Spanner_n.jpg"
    question = "Explain the part in the drawing. What are the critical dimensions and material specifications of this engineering part?"
    
    process_engineering_drawing(image_url, question)