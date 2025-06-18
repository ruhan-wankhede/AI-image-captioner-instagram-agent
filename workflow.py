from typing import List, Dict, Any, Annotated
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from prompts import Prompts
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()


class State(BaseModel):
    initial_caption: str = ""
    captions: List[str] = []
    messages: Annotated[list, add_messages] = []


class CaptionList(BaseModel):
    """List of appropriate captions for the user"""
    captions: List[str] = []


class Workflow:
    def __init__(self):
        self.llm = init_chat_model("mistralai:mistral-large-2411")
        self.prompts = Prompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        # TODO: add instagram api call as a tool
        graph = StateGraph(State)
        graph.add_node("generate_captions", self._generate_captions_step)
        graph.set_entry_point("generate_captions")
        graph.add_edge("generate_captions", END)
        return graph.compile()

    def _generate_captions_step(self, state: State) -> Dict[str, Any]:
        llm = self.llm.with_structured_output(CaptionList)
        messages = [
            SystemMessage(content=self.prompts.CAPTION_GENERATION_SYSTEM),
            HumanMessage(content=self.prompts.caption_user(state.initial_caption)),
        ]

        try:
            #get response as a list of 5 captions
            response = llm.invoke(messages)
            return {"captions": response.captions, "messages": messages}
        except Exception as e:
            print(e)
            return {"captions": [], "messages": []}

    def run(self, raw_caption: str) -> State:
        initial_state = State(initial_caption=raw_caption)
        final_state = self.workflow.invoke(initial_state)
        return State(**final_state)


if __name__ == "__main__":
    from basic_caption import generate_caption

    workflow = Workflow()
    print("AI image caption generator")
    result = workflow.run(generate_caption("lebron.jpg"))
    print(result.initial_caption)
    print(result.captions)
    print(result.messages)
