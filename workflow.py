from typing import List, Dict, Any, Annotated, Literal

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model
from prompts import Prompts
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


class State(BaseModel):
    initial_caption: str = ""
    captions: List[str] = []
    messages: Annotated[list, add_messages] = []
    selected_caption: str = ""
    decision: str = ""


class CaptionList(BaseModel):
    """List of appropriate captions for the user"""
    captions: List[str] = []


class Workflow:
    def __init__(self):
        self.llm = init_chat_model("mistralai:mistral-large-2411")
        self.prompts = Prompts()
        self.workflow = self._build_workflow()
        self.thread_config = {"configurable": {"thread_id": "1"}}

    def _build_workflow(self):
        # TODO: add instagram api call as a tool
        checkpointer = MemorySaver()
        graph = StateGraph(State)
        graph.add_node("generate_captions", self._generate_captions_step)
        graph.add_node("human_decision", self._handle_human_decision_step)
        graph.add_node("upload", self._upload_step)
        graph.add_node("regenerate", self._regenerate_captions_step)
        graph.add_node("edit", self._edit_caption_step)
        graph.set_entry_point("generate_captions")
        graph.add_edge("generate_captions", "human_decision")
        graph.add_edge("regenerate", "human_decision")
        graph.add_conditional_edges(
            "human_decision",
            lambda state: state.decision,
            {"edit": "edit", "regenerate": "regenerate", "upload": "upload", "end": END}
        )
        graph.add_edge("edit", "upload")
        graph.add_edge("upload", END)
        return graph.compile(checkpointer=checkpointer)

    def _generate_captions_step(self, state: State) -> Dict[str, Any]:
        llm = self.llm.with_structured_output(CaptionList)
        messages: list[SystemMessage | HumanMessage | AIMessage] = [
            SystemMessage(content=self.prompts.CAPTION_GENERATION_SYSTEM),
            HumanMessage(content=self.prompts.caption_user(state.initial_caption)),
        ]

        try:
            #get response as a list of 5 captions
            response = llm.invoke(messages)
            messages.append(AIMessage(content=f"Captions are: \n{response.captions}"))
            return {"captions": response.captions, "messages": messages}
        except Exception as e:
            print(e)
            return {"captions": [], "messages": []}

    def _handle_human_decision_step(self, state: State) -> Dict[str, Any]:
        # Ask human for a decision
        human_review = interrupt({
                "question": "What would you like to do with these captions?",
                "instructions": "Reply with:\n - The index of a caption (e.g. `0`, `1`)\n - `edit: <your caption>` to provide your own\n - `regen: <any specifications>` to regenerate options",
                "captions": state.captions
        })
        return human_review

    def _handle_human_input(self, state: dict) -> Command:
        print("What would you like to do with these captions?")
        print("Reply with:\n - The index of a caption (e.g. `0`, `1`)\n - `edit: <your caption>` to provide your own\n - `regen: <any specifications>` to regenerate options")

        captions = state["captions"]
        if captions:
            print("\n📷 Suggested Captions:")
            for idx, caption in enumerate(captions):
                print(f"  [{idx}] {caption}")
        else:
            print("No Captions Generated, an error occurred.\n please try again later.")
            return Command(resume={"decision": "end"})

        # Loop until valid input is given
        while True:
            user_reply = input("\n💬 Your response: ").strip()
            action = ""
            value = ""
            # Option 1: Index of caption (e.g., "0", "1", etc.)
            if user_reply.isdigit():
                index = int(user_reply)
                if 0 <= index < len(captions):
                    action = "upload"
                    value = user_reply
                    break
                else:
                    print("❌ Invalid index. Try again.")

            # Option 2: Edit (starts with "edit:")
            elif user_reply.lower().startswith("edit:"):
                caption = user_reply[5:].strip()
                if caption:
                    action = "edit"
                    value = caption
                    break
                else:
                    print("❌ Empty edit text. Try again.")

            # Option 3: Regenerate (starts with "regen:")
            elif user_reply.lower().startswith("regen:"):
                prompt = user_reply[6:].strip()
                if prompt:
                    action = "regenerate"
                    value = prompt
                    break
                else:
                    print("❌ Empty regenerate instruction. Try again.")

            else:
                print("❌ Unrecognized input. Try again using a valid format.")

        return Command(resume={"decision": action, "selected_caption": value})

    def _regenerate_captions_step(self, state: State) -> Dict[str, Any]:
        llm = self.llm.with_structured_output(CaptionList)
        messages = state.messages
        messages.append(HumanMessage(content=self.prompts.regenerate_captions_user(state.selected_caption)))

        try:
            #get response as a list of 5 captions
            response = llm.invoke(messages)
            return {"captions": response.captions, "messages": messages}
        except Exception as e:
            print(e)
            return {"captions": [], "messages": []}

    def _edit_caption_step(self, state: State) -> Dict[str, Any]:
        pass

    def _upload_step(self, state: State) -> Dict[str, Any]:
        pass

    def run(self, raw_caption: str) -> State:
        initial_state = State(initial_caption=raw_caption)
        next_state = self.workflow.invoke(initial_state, config=self.thread_config)
        while "__interrupt__" in next_state:
            next_state = self.workflow.invoke(self._handle_human_input(next_state), config=self.thread_config)

        return State(**next_state)


if __name__ == "__main__":
    from basic_caption import generate_caption

    workflow = Workflow()
    print("AI image caption generator")
    result = workflow.run(generate_caption("lebron.jpg"))
    print(result.decision)
    print(result.selected_caption)
