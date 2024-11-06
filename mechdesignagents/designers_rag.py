from agents import *
from typing_extensions import Annotated
from autogen import GroupChat, GroupChatManager



def _reset_agents():
    designer.reset()
    designer_aid.reset()
    cad_coder.reset()
    reviewer.reset()


def rag_chat(design_problem : str):
    _reset_agents()
    groupchat = GroupChat(
        agents=[designer_aid, cad_coder, reviewer], messages=[], max_round=12, speaker_selection_method="round_robin"
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with designer_aid as this is the user proxy agent.
    designer_aid.initiate_chat(
        manager,
        message=designer_aid.message_generator,
        problem=design_problem,
        n_results=3,
    )

prompt = input("Enter your design problem: ")
rag_chat(prompt)