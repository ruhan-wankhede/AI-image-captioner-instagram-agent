from typing import List, Dict, Any, Annotated, Literal
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model
from prompts import Prompts
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.types import Command, interrupt

load_dotenv()


class State(BaseModel):
    initial_caption: str = ""
    captions: List[str] = []
    messages: Annotated[list, add_messages] = []
    selected_caption: str = ""


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
        """graph.add_node("generate_captions", self._generate_captions_step)
        graph.add_node("human_decision", self._handle_human_decision_step)
        graph.add_node("upload", self._upload_step)
        graph.add_node("regenerate", self._regenerate_captions_step)
        graph.add_node("edit", self._edit_caption_step)
        graph.set_entry_point("generate_captions")
        graph.add_edge("generate_captions", "human_decision")
        graph.add_edge("regenerate", "human_decision")
        graph.add_edge("edit", "upload")
        graph.add_edge("upload", END)"""
        graph.add_node("generate_captions", self._generate_captions_step)
        graph.add_node("request_human_input", self._request_human_input_step)
        graph.add_node("handle_human_response", self._handle_human_response_step)
        graph.add_node("upload", self._upload_step)
        graph.add_node("regenerate", self._regenerate_captions_step)
        graph.add_node("edit", self._edit_caption_step)

        graph.set_entry_point("generate_captions")

        graph.add_edge("generate_captions", "request_human_input")
        graph.add_edge("request_human_input", "handle_human_response")
        graph.add_edge("handle_human_response", "upload")
        graph.add_edge("handle_human_response", "regenerate")
        graph.add_edge("handle_human_response", "edit")
        graph.add_edge("edit", "upload")
        graph.add_edge("upload", END)
        return graph.compile()

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
            print(response.captions)
            return {"captions": response.captions, "messages": messages}
        except Exception as e:
            print(e)
            return {"captions": [], "messages": []}

    """def _handle_human_decision_step(self, state: State) -> Command[Literal["upload", "regenerate", "edit"]]:
        while True:
            # Ask human for a decision
            human_review = interrupt({
                "question": "What would you like to do with these captions?",
                "instructions": "Reply with:\n - The index of a caption (e.g. `0`, `1`)\n - `edit: <your caption>` to provide your own\n - `regen: <any specifications>` to regenerate options",
                "captions": state.captions
            })

            user_action, user_data = human_review

            if user_action == "select":
                try:
                    index = int(user_data)
                    state.selected_caption = state.captions[index]
                    print(state.selected_caption)
                    return Command(goto="upload", update=state)
                except (ValueError, IndexError):
                    print("invalid input try again")
                    continue  # Retry loop

            elif user_action == "edit":
                if isinstance(user_data, str) and user_data.strip():
                    state.selected_caption = user_data.strip()
                    print("selected caption: " + state.selected_caption)
                    return Command(goto="edit")
                else:
                    print("invalid input try again")
                    continue  # Retry loop

            elif user_action == "regen":
                state.messages.append(HumanMessage(content=f"Provide more captions and keep in mind {user_data.strip()}"))
                print("regenerated captions")
                print(state.messages)
                return Command(goto="regenerate", update=state)

            # If none match, loop again for valid input"""

    def _request_human_input_step(self, state: State) -> Any:
        yield interrupt({
            "question": "What would you like to do with these captions?",
            "instructions": "Reply with:\n - The index of a caption (e.g. `0`, `1`)\n - `edit: <your caption>` to provide your own\n - `regen: <any specifications>` to regenerate options",
            "captions": state.captions
        })

    def _handle_human_response_step(self, state: State, tool_input: str) -> Command[Literal["upload", "regenerate", "edit"]]:
        user_input = tool_input.strip()

        if user_input.isdigit():
            index = int(user_input)
            if 0 <= index < len(state.captions):
                state.selected_caption = state.captions[index]
                return Command(goto="upload", update=state)

        elif user_input.lower().startswith("edit:"):
            custom = user_input[5:].strip()
            if custom:
                state.selected_caption = custom
                return Command(goto="edit", update=state)

        elif user_input.lower().startswith("regen:"):
            new_prompt = user_input[6:].strip()
            state.messages.append(HumanMessage(content=f"Please regenerate captions with this in mind: {new_prompt}"))
            return Command(goto="regenerate", update=state)

        # If input doesn't match any valid pattern, re-ask
        return Command(goto="request_human_input")

    def _regenerate_captions_step(self, state: State) -> Dict[str, Any]:
        pass

    def _edit_caption_step(self, state: State) -> Dict[str, Any]:
        pass

    def _upload_step(self, state: State) -> Dict[str, Any]:
        pass

    def run(self, raw_caption: str) -> State:
        initial_state = State(initial_caption=raw_caption)

        # Step 1: Start the workflow
        next_state = self.workflow.invoke(initial_state)

        # Step 2: Handle interruption
        while next_state.get("status") == "interrupted":
            tool_call = next_state.get("tool_calls", [{}])[0]
            prompt = tool_call.get("args", {})

            print("\n🚦 Human Review Needed:")
            print("📝 Question:", prompt.get("question"))
            print("📋 Instructions:", prompt.get("instructions"))
            captions = prompt.get("captions", [])
            for idx, cap in enumerate(captions):
                print(f"{idx}: {cap}")

            # Step 3: Get user response (simulate frontend input)
            user_reply = input("\n💬 Your response: ")

            # Step 4: Resume graph
            next_state = self.workflow.resume(state=next_state["state"], value=user_reply)

        # Step 5: Return final state once completed
        return State(**next_state)


if __name__ == "__main__":
    from basic_caption import generate_caption

    workflow = Workflow()
    print("AI image caption generator")
    result = workflow.run(generate_caption("lebron.jpg"))
