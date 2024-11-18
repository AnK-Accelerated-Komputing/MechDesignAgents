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
    system_message="""You are an engineering drawing analyst. You first obtain the number of views
     and major dimensions of the parts along with the material specifications if given following thses steps strictly:
    1. ALWAYS begin by calling analyze_drawing_with_groq to get the Groq vision model's analysis for your queries
    2. CLEARLY state "GROQ VISION ANALYSIS:" followed by the exact response from Groq and interpret it elaborately
    3. Then pass the resulting analysis to verification_agent to verify the information and to final_reporter for summary.
    4. If the Groq response is unclear or missing critical information, call the function again with a more specific prompt
    
    NEVER make assumptions about measurements or specifications without Groq's analysis.""",
    llm_config={"config_list": config_list}
)

verification_agent = autogen.AssistantAgent(
    name="verification_agent",
    system_message="""You are a verification specialist that verifies the drawing details obtained from 
    the primary_analyzer following these steps strictly:
    1. For each measurement to verify, call analyze_drawing_with_groq with a single specific verification prompt that ensures
    that the dimension specification are correct.
    2. ALWAYS state "GROQ VERIFICATION RESULTS:" followed by the exact Groq response
    3. Then summarize all the verified results to pass it to final_reporter for final summarization of all details of the drawing
    4. Compare measurements across different views
    5. If any discrepancy is found, call the function again with a focused prompt on that specific area
    
    NEVER confirm measurements without explicit Groq verification.""",
    llm_config={"config_list": config_list}
)

final_reporter = autogen.AssistantAgent(
    name="final_reporter",
    system_message="""You are a technical documentation specialist that provides the final report
    of the engineering drawing following these steps strictly:
    1. Use the response from primary_analyzer and verification_agent to create a detailed yet tacit summary of the drawing.
    2. If any details are missed call analyze_drawing_with_groq for finding that detail with the query.
    2. Start your report with "FINAL REPORT:" before providing your structured summary
    4. Include only measurements and specifications that were explicitly verified by Groq
    5. Clearly mark any uncertainties or measurements that couldn't be verified before verifing them by calling analyze_drawing_with_groq 
    for that measurement.
    
    End your report with TERMINATE after you think the report contains all the necessary detail.""",
    llm_config={"config_list": config_list}
)

# Register the analyze_drawing function with all agents
@user_proxy.register_for_execution()
@primary_analyzer.register_for_llm(description="Analyze engineering drawing using Groq vision model for getting as much detail of the drawing as possible")
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


@user_proxy.register_for_execution()
@final_reporter.register_for_llm(description="Analyze engineering drawing using Groq vision model for creating a final report of the drawing")
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

# Example usage
if __name__ == "__main__":
    image_url = "/home/niel77/MechanicalAgents/mechdesignagents/images/Drawing-of-the-connecting-rod_W640.jpg"
    question = "Explain the part in the drawing.What are the critical dimensions and material specifications of this engineering part?"
    
    process_engineering_drawing(image_url, question)