from agents import *
from autogen import GroupChat, GroupChatManager



def _reset_agents():
    User.reset()
    designer_aid.reset()
    cad_coder.reset()
    executor.reset()
    reviewer.reset()


def rag_chat(design_problem : str):
    _reset_agents()
    groupchat = GroupChat(
        agents=[designer_aid, cad_coder,executor, reviewer], messages=[], max_round=12, speaker_selection_method="round_robin"
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with designer_aid as this is the user proxy agent.
    User.initiate_chat(
        manager,
        message=design_problem,
    )

prompt = input("Enter your design problem: ")
rag_chat(prompt)