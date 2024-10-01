from agents import *


#for two agent system with just designer and cad coder.
problem_prompt=input("Enter your design problem: ")
result = designer.initiate_chat(cad_coder, message=problem_prompt)