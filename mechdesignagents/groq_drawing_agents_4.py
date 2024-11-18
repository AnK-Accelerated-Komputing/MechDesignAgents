import autogen
import base64
import os
from groq import Groq
from typing import Dict, List, Union, Literal, Annotated

# Configure the agents with function calling capability
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


@user_proxy.register_for_execution()
def analyze_drawing_with_groq(
    image_url: Annotated[str, "Path to the engineering drawing image"],
    prompt: Annotated[str, "Analysis prompt for the drawing"],
    analysis_type: Annotated[Literal["general", "verification", "final"], "Type of analysis to perform"] = "general"
) -> Dict[str, str]:
    try:
        # Read and encode the image
        with open(image_url, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_data_url = f"data:image/png;base64,{encoded_image}"
        
        # Enhance prompt based on analysis type
        enhanced_prompt = prompt
        if analysis_type == "verification":
            enhanced_prompt = f"Verify specifically and only this detail in the engineering drawing: {prompt}. Focus on measurement accuracy and cross-view consistency."
        elif analysis_type == "final":
            enhanced_prompt = f"Provide a final confirmation of exactly this detail: {prompt}. Focus only on this specific aspect."
        
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
        
        return {
            "groq_response": completion.choices[0].message.content,
            "analysis_type": analysis_type,
            "prompt_used": enhanced_prompt,
            "status": "success"
        }
        
    except Exception as e:
        return {
            "groq_response": None,
            "analysis_type": analysis_type,
            "prompt_used": enhanced_prompt,
            "status": "error",
            "error_message": str(e)
        }
    
# Define the function for all agents
def get_llm_config(analyze_drawing_function):
    return {
        "config_list": config_list,
        "functions": [
            {
                "name": "analyze_drawing_with_groq",
                "description": "Analyze engineering drawing using Groq vision model",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_url": {
                            "type": "string",
                            "description": "Path to the engineering drawing image"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Specific analysis prompt for the drawing"
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
        ]
    }


# Create the primary agents with enhanced prompts
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
    llm_config=get_llm_config(analyze_drawing_with_groq)
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
    llm_config=get_llm_config(analyze_drawing_with_groq)
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
    llm_config=get_llm_config(analyze_drawing_with_groq)
)



def process_engineering_drawing(image_url: str, question: str) -> None:
    """
    Process an engineering drawing through the multi-agent system.
    """
    groupchat = autogen.GroupChat(
        agents=[user_proxy, primary_analyzer, verification_agent, final_reporter],
        messages=[],
        max_round=15  # Increased to allow for multiple function calls
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

# Example usage
if __name__ == "__main__":
    image_url = "/home/niel77/MechanicalAgents/mechdesignagents/images/Drawing-of-the-connecting-rod_W640.jpg"
    question = "Analyze this engineering drawing comprehensively. What are all the critical dimensions, views, and material specifications?"
    
    process_engineering_drawing(image_url, question)