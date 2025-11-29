import os
import time
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.messages import trim_messages, HumanMessage
from langchain.chat_models import init_chat_model
from shared_store import url_time
from tools import (
    get_rendered_html, download_file, post_request,
    run_code, add_dependencies, ocr_image_tool, transcribe_audio, encode_image_to_base64
)

load_dotenv()

# Environment configuration
EMAIL = os.getenv("EMAIL")
SECRET = os.getenv("SECRET")

# Execution limits
RECURSION_LIMIT = 5000
MAX_TOKENS = 60000


# Define agent state structure
class AgentState(TypedDict):
    """State container for agent messages with automatic message aggregation."""
    messages: Annotated[List, add_messages]


# Available tool functions for agent
TOOLS = [
    run_code, get_rendered_html, download_file,
    post_request, add_dependencies, ocr_image_tool, transcribe_audio, encode_image_to_base64
]


# Initialize language model with rate limiting
rate_limiter = InMemoryRateLimiter(
    requests_per_second=4 / 60,  # 4 requests per minute
    check_every_n_seconds=1,
    max_bucket_size=4
)

llm = init_chat_model(
    model_provider="google_genai",
    model="gemini-2.5-flash",
    rate_limiter=rate_limiter
).bind_tools(TOOLS)


# System instructions for the agent
SYSTEM_PROMPT = f"""
You are an autonomous task-solving agent designed to process and solve quiz challenges.

Core responsibilities:
1. Retrieve content from each provided URL
2. Parse instructions, extract required parameters, and identify submission endpoints
3. Accurately solve presented challenges (utilize available tools as needed)
4. Submit solutions exclusively to the specified submission endpoint
5. Process subsequent URLs until task chain completes, then output END

Operational guidelines:
- Always use the "encode_image_to_base64" tool for image encoding (do NOT write custom code)
- Never fabricate or modify URLs or parameter fields
- Preserve complete endpoint paths without truncation
- Validate all server responses before proceeding
- Continue until all tasks are completed
- Leverage tools for web scraping, file operations, OCR, transcription, and code execution
- Include required credentials:
    email = {EMAIL}
    secret = {SECRET}
"""


# Recovery node for malformed tool calls
def handle_malformed_node(state: AgentState):
    """
    Handles invalid JSON generation by prompting the agent to retry.
    
    When the LLM produces malformed tool call JSON, this node injects
    a corrective message into the conversation to trigger a retry.
    """
    print("--- DETECTED MALFORMED JSON. ASKING AGENT TO RETRY ---")
    return {
        "messages": [
            {
                "role": "user", 
                "content": "SYSTEM ERROR: Your last tool call was Malformed (Invalid JSON). Please rewrite the code and try again. Ensure you escape newlines and quotes correctly inside the JSON."
            }
        ]
    }


# Main agent execution node
def agent_node(state: AgentState):
    """
    Core agent logic with timeout handling and context management.
    
    Enforces time limits per task and manages conversation context to prevent
    token overflow. Injects timeout instructions when necessary.
    """
    # Check elapsed time for current task
    current_timestamp = time.time()
    active_url = os.getenv("url")
    
    # Retrieve stored timestamp (safe access to prevent crashes)
    stored_timestamp = url_time.get(active_url) 
    offset_value = os.getenv("offset", "0")

    if stored_timestamp is not None:
        stored_timestamp = float(stored_timestamp)
        elapsed = current_timestamp - stored_timestamp

        # Enforce timeout limits
        if elapsed >= 180 or (offset_value != "0" and (current_timestamp - float(offset_value)) > 90):
            print(f"Timeout exceeded ({elapsed}s) — instructing LLM to purposely submit wrong answer.")

            timeout_message = """
            You have exceeded the time limit for this task (over 180 seconds).
            Immediately call the `post_request` tool and submit a WRONG answer for the CURRENT quiz.
            """

            # Create human message with timeout instruction
            timeout_instruction = HumanMessage(content=timeout_message)

            # Invoke LLM with timeout directive
            llm_response = llm.invoke(state["messages"] + [timeout_instruction])
            return {"messages": [llm_response]}

    # Trim conversation history to prevent token overflow
    trimmed_conversation = trim_messages(
        messages=state["messages"],
        max_tokens=MAX_TOKENS,
        strategy="last",
        include_system=True,
        start_on="human",
        token_counter=llm, 
    )
    
    # Verify human message exists in trimmed context
    contains_human_message = any(msg.type == "human" for msg in trimmed_conversation)
    
    if not contains_human_message:
        print("WARNING: Context was trimmed too far. Injecting state reminder.")
        # Restore context with current URL
        ongoing_url = os.getenv("url", "Unknown URL")
        context_reminder = HumanMessage(content=f"Context cleared due to length. Continue processing URL: {ongoing_url}")
        
        # Append reminder to trimmed conversation
        trimmed_conversation.append(context_reminder)

    print(f"--- INVOKING AGENT (Context: {len(trimmed_conversation)} items) ---")
    
    # Invoke language model with trimmed context
    llm_response = llm.invoke(trimmed_conversation)

    return {"messages": [llm_response]}


# Routing logic for graph execution flow
def route(state):
    """
    Determines next node based on agent's last message.
    
    Routes to:
    - handle_malformed: If tool call JSON is invalid
    - tools: If valid tool calls are present
    - END: If agent outputs completion signal
    - agent: Otherwise, continue reasoning loop
    """
    last_message = state["messages"][-1]
    
    # Check for malformed tool call errors
    if "finish_reason" in last_message.response_metadata:
        if last_message.response_metadata["finish_reason"] == "MALFORMED_FUNCTION_CALL":
            return "handle_malformed"

    # Check for tool invocations
    tool_invocations = getattr(last_message, "tool_calls", None)
    if tool_invocations:
        print("Route → tools")
        return "tools"

    # Check for completion signal
    message_content = getattr(last_message, "content", None)
    if isinstance(message_content, str) and message_content.strip() == "END":
        return END

    if isinstance(message_content, list) and len(message_content) and isinstance(message_content[0], dict):
        if message_content[0].get("text", "").strip() == "END":
            return END

    print("Route → agent")
    return "agent"


# Build execution graph
graph = StateGraph(AgentState)

# Register graph nodes
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(TOOLS))
graph.add_node("handle_malformed", handle_malformed_node)

# Define static edges (deterministic transitions)
graph.add_edge(START, "agent")
graph.add_edge("tools", "agent")
graph.add_edge("handle_malformed", "agent")

# Define conditional edges (dynamic routing based on state)
graph.add_conditional_edges(
    "agent", 
    route,
    {
        "tools": "tools",
        "agent": "agent",
        "handle_malformed": "handle_malformed",
        END: END
    }
)

# Compile graph into executable application
app = graph.compile()


# Entry point for agent execution
def run_agent(url: str):
    """
    Initiates agent execution with system prompt and starting URL.
    
    Creates initial conversation state and invokes the compiled graph
    with recursion limit configuration.
    """
    # Initialize conversation with system prompt and user input
    initial_state = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": url}
    ]

    # Execute graph with recursion protection
    app.invoke(
        {"messages": initial_state},
        config={"recursion_limit": RECURSION_LIMIT}
    )

    print("Tasks completed successfully!")