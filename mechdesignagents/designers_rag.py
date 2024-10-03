from agents import *
from typing_extensions import Annotated
from autogen import GroupChat, GroupChatManager


def call_rag_chat(design_problem : str):
    reset_agents()

    # In this case, we will have multiple user proxy agents and we don't initiate the chat
    # with RAG user proxy agent.
    # In order to use RAG user proxy agent, we need to wrap RAG agents in a function and call
    # it from other agents.
    def retrieve_content(
        message: Annotated[
            str,
            "Refined message which keeps the original meaning and can be used to retrieve content for code generation and question answering.",
        ],
        n_results: Annotated[int, "number of results"] = 3,
    ) -> str:
        designer_aid.n_results = n_results  # Set the number of results to be retrieved.
        _context = {"problem": message, "n_results": n_results}
        ret_msg = designer_aid.message_generator(designer_aid, None, _context)
        return ret_msg or message

    designer_aid.human_input_mode = "NEVER"  # Disable human input for boss_aid since it only retrieves content.

    for caller in [cad_coder, reviewer]:
        d_retrieve_content = caller.register_for_llm(
            description="retrieve content for code generation and CAD model generation", api_style="function"
        )(retrieve_content)

    for executor in [designer]:
        executor.register_for_execution()(d_retrieve_content)

    groupchat = GroupChat(
        agents=[designer, cad_coder, reviewer],
        messages=[],
        max_round=12,
        speaker_selection_method="round_robin",
        allow_repeat_speaker=False,
    )

    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the boss as this is the user proxy agent.
    designer.initiate_chat(
        manager,
        message=design_problem,
    )

def rag_chat(design_problem : str):
    reset_agents()
    groupchat = GroupChat(
        agents=[designer_aid,  cad_coder, reviewer], messages=[], max_round=12, speaker_selection_method="round_robin"
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