import autogen
import base64
import os
from groq import Groq
from typing import Dict, List, Union, Literal
from rich.console import Console
from rich.markdown import Markdown

print(os.environ.get("GROQ_API_KEY"))

class DrawingAnalyzer:
    def __init__(self, image_url: str):
        self.image_url = image_url
        self.groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    
    def analyze_drawing(self, prompt: str, analysis_type: Literal["general", "verification", "final"] = "general") -> Dict[str, str]:
        """
        Analyze an engineering drawing using Groq's vision model.
        """
        try:
            # Read and encode the image
            with open(self.image_url, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                image_data_url = f"data:image/png;base64,{encoded_image}"
            
            # Enhance prompt based on analysis type
            enhanced_prompt = prompt
            if analysis_type == "verification":
                enhanced_prompt = f"Verify the following in the engineering drawing: {prompt}. Focus on measurement accuracy and cross-view consistency."
            elif analysis_type == "final":
                enhanced_prompt = f"Provide a final confirmation of: {prompt}. Include all critical dimensions and specifications."
            
            # Create completion request
            completion = self.groq_client.chat.completions.create(
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

class PrimaryAnalyzerAgent(autogen.AssistantAgent):
    def __init__(self, name: str, analyzer: DrawingAnalyzer, llm_config: Dict):
        system_message = """You are an engineering drawing analyst. Follow these steps strictly:
        1. ALWAYS begin by calling self.analyzer.analyze_drawing to get the Groq vision model's analysis
        2. CLEARLY state "GROQ VISION ANALYSIS:" followed by the exact response from Groq
        3. Then say "MY ANALYSIS:" before adding your interpretation
        4. If the Groq response is unclear, call analyze_drawing again with a more specific prompt
        5. Ask verification_agent to check specific measurements you've identified
        
        NEVER make assumptions about measurements without Groq's analysis."""

        super().__init__(name=name, system_message=system_message, llm_config=llm_config)
        self.analyzer = analyzer

class VerificationAgent(autogen.AssistantAgent):
    def __init__(self, name: str, analyzer: DrawingAnalyzer, llm_config: Dict):
        system_message = """You are a verification specialist. Follow these steps strictly:
        1. For each measurement to verify, call self.analyzer.analyze_drawing with specific verification prompts
        2. ALWAYS state "GROQ VERIFICATION RESULTS:" followed by the exact Groq response
        3. Then say "VERIFICATION ANALYSIS:" before your interpretation
        4. Compare measurements across different views
        5. If any discrepancy is found, call analyze_drawing again with a focused prompt
        
        NEVER confirm measurements without explicit Groq verification."""

        super().__init__(name=name, system_message=system_message, llm_config=llm_config)
        self.analyzer = analyzer

class FinalReporterAgent(autogen.AssistantAgent):
    def __init__(self, name: str, analyzer: DrawingAnalyzer, llm_config: Dict):
        system_message = """You are a technical documentation specialist. Follow these steps strictly:
        1. Call self.analyzer.analyze_drawing for final confirmation of all specifications
        2. Start your report with "FINAL GROQ VERIFICATION:" followed by the exact Groq response
        3. Then say "FINAL REPORT:" before providing your structured summary
        4. Include only measurements and specifications that were explicitly verified by Groq
        5. Clearly mark any uncertainties or measurements that couldn't be verified
        
        End your report with TERMINATE only after Groq verification is complete."""

        super().__init__(name=name, system_message=system_message, llm_config=llm_config)
        self.analyzer = analyzer

def create_agents(image_url: str, config_list: List[Dict]):
    # Create the drawing analyzer
    analyzer = DrawingAnalyzer(image_url)
    
    # Create LLM config
    llm_config = {
        "config_list": config_list,
        "timeout": 120
    }
    
    # Initialize agents with the analyzer
    primary_analyzer = PrimaryAnalyzerAgent(
        name="primary_analyzer",
        analyzer=analyzer,
        llm_config=llm_config
    )
    
    verification_agent = VerificationAgent(
        name="verification_agent",
        analyzer=analyzer,
        llm_config=llm_config
    )
    
    final_reporter = FinalReporterAgent(
        name="final_reporter",
        analyzer=analyzer,
        llm_config=llm_config
    )
    
    # Create user proxy
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={"work_dir": "coding", "use_docker": False}
    )
    
    return primary_analyzer, verification_agent, final_reporter, user_proxy

def process_engineering_drawing(image_url: str, question: str) -> None:
    """
    Process an engineering drawing through the multi-agent system.
    """
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
    
    primary_analyzer, verification_agent, final_reporter, user_proxy = create_agents(image_url, config_list)
    
    groupchat = autogen.GroupChat(
        agents=[user_proxy, primary_analyzer, verification_agent, final_reporter],
        messages=[],
        max_round=10
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
    # Set up the environment
    image_url = "/home/niel77/MechanicalAgents/mechdesignagents/images/Drawing-of-the-connecting-rod_W640.jpg"
    question = "What are the critical dimensions and material specifications of the part in this drawing image?"
    
    # Run the analysis
    process_engineering_drawing(image_url, question)