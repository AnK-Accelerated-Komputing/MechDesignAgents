import autogen
import base64
import os
from groq import Groq
from typing import Dict, List, Union, Literal
from rich.console import Console
from rich.markdown import Markdown

config_list = [
    {

        "model": "llama3-groq-70b-8192-tool-use-preview",
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


def analyze_drawing_with_groq(
    image_url: str,
    prompt: str,
    analysis_type: Literal["general", "verification", "final"] = "general"
) -> Dict[str, str]:
    """
    Analyze an engineering drawing using Groq's vision model.
    Returns both the raw response and formatted results.
    """
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

llm_config = {
    "config_list": config_list,
    "functions": list(function_map.values()),
    "timeout": 120
}

# Primary analyzer agent
primary_analyzer = autogen.AssistantAgent(
    name="primary_analyzer",
    system_message="""You are an engineering drawing analyst. Follow these steps strictly:
    1. ALWAYS begin by calling analyze_drawing_with_groq to get the Groq vision model's analysis
    2. CLEARLY state "GROQ VISION ANALYSIS:" followed by the exact response from Groq
    3. Then say "MY ANALYSIS:" before adding your interpretation
    4. If the Groq response is unclear or missing critical information, call the function again with a more specific prompt
    5. Ask verification_agent to check specific measurements you've identified
    
    NEVER make assumptions about measurements or specifications without Groq's analysis.""",
    llm_config=llm_config,
    function_map=function_map
)

# Verification agent
verification_agent = autogen.AssistantAgent(
    name="verification_agent",
    system_message="""You are a verification specialist. Follow these steps strictly:
    1. For each measurement to verify, call analyze_drawing_with_groq with a specific verification prompt
    2. ALWAYS state "GROQ VERIFICATION RESULTS:" followed by the exact Groq response
    3. Then say "VERIFICATION ANALYSIS:" before your interpretation
    4. Compare measurements across different views
    5. If any discrepancy is found, call the function again with a focused prompt on that specific area
    
    NEVER confirm measurements without explicit Groq verification.""",
    llm_config=llm_config,
    function_map=function_map
)

# Final reporter agent
final_reporter = autogen.AssistantAgent(
    name="final_reporter",
    system_message="""You are a technical documentation specialist. Follow these steps strictly:
    1. Call analyze_drawing_with_groq for final confirmation of all specifications
    2. Start your report with "FINAL GROQ VERIFICATION:" followed by the exact Groq response
    3. Then say "FINAL REPORT:" before providing your structured summary
    4. Include only measurements and specifications that were explicitly verified by Groq
    5. Clearly mark any uncertainties or measurements that couldn't be verified
    
    End your report with TERMINATE only after Groq verification is complete.""",
    llm_config=llm_config,
    function_map=function_map
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "coding", "use_docker": False},
    function_map=function_map
)


def process_engineering_drawing(image_url: str, question: str) -> None:
    """
    Process an engineering drawing through the multi-agent system.
    """
        
    groupchat = autogen.GroupChat(
        agents=[user_proxy, primary_analyzer, verification_agent, final_reporter],
        messages=[],
        max_round=5,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat)
    
    initial_message = {
        "content": f"""Analyze this engineering drawing at {image_url} regarding: {question}

        IMPORTANT: 
        - Each agent must explicitly show the Groq vision model's response before their analysis
        - All measurements and specifications must come from Groq's analysis
        - Clearly separate Groq's responses from your interpretations
        - Do not make assumptions without Groq verification""",
        "role": "user"
    }
    
    user_proxy.initiate_chat(manager, message=initial_message)

# Example usage
if __name__ == "__main__":
    image_url = "/home/niel77/MechanicalAgents/mechdesignagents/images/Drawing-of-the-connecting-rod_W640.jpg"
    question = "What are the critical dimensions and material specifications of this engineering part?"
    
    process_engineering_drawing(image_url, question)