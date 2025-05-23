from langgraph.graph import END, StateGraph, START

from models.state import architect_code_review_graph_state
from models.core_models import code_generation_model, reviewer_evaluation_model
    
class architect_code_review_workflow():
    def __init__(self, llm, prompts, max_iterations = 3, send_update = None, reflect = False):
        self.llm = llm
        self.prompts = prompts
        self.max_iterations = max_iterations
        self.reflect = reflect
        self.compiled_workflow = None
        self.send_update = send_update

    def compile(self):
        workflow = StateGraph(architect_code_review_graph_state)

        # Define the nodes
        workflow.add_node("architect", self.architect)  # high level design
        workflow.add_node("engineer", self.engineer)  # generate code
        workflow.add_node("review", self.review)  # review code agains requirements and design

        # Build graph
        workflow.add_edge(START, "architect")
        workflow.add_edge("architect", "engineer")
        workflow.add_edge("engineer", "review")
        workflow.add_conditional_edges(
            "review",
            self.decide_to_finish,
            {
                "end": END,
                "engineer": "engineer",
            },
        )
        self.compiled_workflow = workflow.compile()
        return self.compiled_workflow

    async def architect(self, state: architect_code_review_graph_state):
        print("ARCHITECTING SOLUTION")

        # State
        messages = state["messages"]
        iterations = state["iterations"]

        if self.send_update:
            await self.send_update("ARCHITECTING SOLUTION")

        if iterations == 0:
            initial_prompt = self.prompts["architect_prompt"]
            messages = initial_prompt + messages

        # Architect's response
        response = self.llm.invoke(messages)

        if self.send_update:
            await self.send_update("ARCHITECT WROTE SPECS")

        # Append the architect's response to the conversation
        messages += [
            (
                "developer",
                f"{response.text()}"
            )
        ]

        # Return state
        return {"messages": messages, "iterations": iterations, "specs": response}
    
    async def engineer(self, state: architect_code_review_graph_state):
        print("ENGINEERING CODE")

        # State
        messages = state["messages"]
        iterations = state["iterations"]
        confidence_score = state["confidence_score"]

        if confidence_score < 70 and iterations >= 1:
            messages += self.prompts["engineer_retry_prompt"]
            if self.send_update:
                await self.send_update("RETRYING SOLUTION")
        else:
            messages += self.prompts["engineer_prompt"]
            if self.send_update:
                await self.send_update("ENGINEERING CODE")
        
        # Engineer's response
        structured_output_llm = self.llm.with_structured_output(code_generation_model)
        response = structured_output_llm.invoke(messages)

        if self.send_update:
            await self.send_update("ENGINEER GENERATED CODE")

        # Append the engineer's response to the conversation
        messages += [
            (
                "developer",
                f"Here's my comments and description about the code: {response.engineer_comments}. \n Here's the code: {response.code}"
            )
        ]

        # Return state
        return {"generation": response.code, "messages": messages, "iterations": iterations}
    
    async def review(self, state: architect_code_review_graph_state):
        print("REVIEWING CODE")

        # State
        messages = state["messages"]
        iterations = state["iterations"]
        generation = state["generation"]
        requirements = state["requirements"]
        specs = state["specs"]
        confidence_score = state["confidence_score"]

        if self.send_update:
            await self.send_update("REVIEWING CODE")

        hydrated_reviewer_prompt = self.prompts["reviewer_prompt"][0][1]
        hydrated_reviewer_prompt = hydrated_reviewer_prompt.replace("---code---", str(generation)).replace("---requirements---", str(requirements)).replace("---specs---", str(specs))
        messages += [
            (
                "system",
                hydrated_reviewer_prompt
            )
        ]

        # Reviewer's response
        structured_output_llm = self.llm.with_structured_output(reviewer_evaluation_model)
        response = structured_output_llm.invoke(messages)

        if self.send_update:
            await self.send_update("CODE REVIEW FINISHED")

        # Append the reviewer's response to the conversation
        messages += [
            (
                "developer",
                f"Here's my comments and description about the code: {response.reviewer_comments}. \n Here's the confidence score: {response.confidence_score}"
            )
        ]

        # Increment
        iterations += 1
        return {"confidence_score": response.confidence_score, "iterations": iterations}

    async def decide_to_finish(self, state: architect_code_review_graph_state):
        confidence_score = state["confidence_score"]
        iterations = state["iterations"]

        if iterations == self.max_iterations:
            print("UNSUCCESSFUL END")
            if self.send_update:
                await self.send_update("UNSUCCESSFUL END")
            return "end"
        
        if iterations < self.max_iterations and confidence_score < 70:
            print("RE-TRYING")
            if self.send_update:
                await self.send_update("RE-TRYING")
            return "engineer"
        
        if confidence_score >= 70:
            print("SUCCESSFUL END")
            if self.send_update:
                await self.send_update("SUCCESSFUL END")
            return "end"
        
        


        




