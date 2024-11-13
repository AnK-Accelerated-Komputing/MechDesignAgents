from autogen import GroupChat, GroupChatManager
from designer_functions import *
from agents import *



def norag_chat(design_prblem: str):
    reset_agents()
    groupchat = GroupChat(
        agents=[designer, designer_expert, cad_coder, reviewer,],
        messages=[],
        max_round=12,
        speaker_selection_method="round_robin",
        # speaker_selection_method="auto",
        allow_repeat_speaker=False,
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the designer as this is the user proxy agent.
    designer.initiate_chat(
        manager,
        message=design_prblem,
    )

prompt = input("Enter your design problem: ")
norag_chat(prompt)