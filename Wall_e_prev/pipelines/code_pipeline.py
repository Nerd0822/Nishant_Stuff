from utils import ollama_utils
from config import MODELS, MODEL_OPTIONS
from pipelines.chat_pipeline import chat
from pipelines.plan_pipeline import plan


def code(query, history):
    messages = history + [{"role": "user", "content": query}]
    res = ollama_utils.parse_to(
        model=MODELS["code_model"],
        query=query,
        stream=True,
        keep_alive=0,
        messages=messages,
        options=MODEL_OPTIONS.get("code_model"),
    )
    return ollama_utils.stream_output(res)


def execute_code_pipeline(query, history):
    
    print("--- [STAGE 1: ARCHITECTURAL PLANNING] ---")
    plan_result = plan(query=query, history=history)

    print("\n--- [STAGE 2: CODE IMPLEMENTATION] ---")
    # PRESERVE ORIGINAL REPHRASED QUERY ALONG WITH PLAN
    
    code_prompt = (
        f"Requirements & Tasks:\n{query}\n\n"
        f"Step-by-Step Implementation Strategy:\n{plan_result}\n\n"
        f"Write complete, working, production-quality code for all requirements listed above."
    )
    
    code_result = code(query=code_prompt, history=history)
    
    print("\n--- [STAGE 3: REVIEW] ---")
    review_prompt = (
        f"Requirements & Tasks:\n{query}\n\n"
        f"Step-by-Step Implementation Strategy:\n{plan_result}\n\n"
        f"code implementation:\n{code_result}\n\n"
        f"look for any edge cases or any errors in the code"
    )
    review_result = code(query=review_prompt,history=history)

    print("\n--- [STAGE 4: SOLUTION SUMMARY] ---")
    
    explain_prompt = f"Provide a brief, helpful summary of the implemented code solutions:\n\n{review_result}"
    
    return chat(query=explain_prompt, history=history)
