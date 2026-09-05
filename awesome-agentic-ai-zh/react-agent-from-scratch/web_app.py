import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agent import ReActAgent

# Load environment variables from project root .env
load_dotenv(Path(__file__).resolve().parents[3] / '.env', override=True)
os.environ['NO_PROXY'] = '*'

# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="ReAct Agent",
    page_icon="🤖",
    layout="wide",
)

# ------------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------------

if "agent" not in st.session_state:
    st.session_state.agent = ReActAgent()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chain_of_thought" not in st.session_state:
    st.session_state.chain_of_thought = []

# ------------------------------------------------------------------
# Sidebar - Chain of Thought Panel
# ------------------------------------------------------------------

with st.sidebar:
    st.header("🧠 Chain of Thought")

    if st.button("🔄 Reset Agent", use_container_width=True):
        st.session_state.agent.reset()
        st.session_state.chat_history = []
        st.session_state.chain_of_thought = []
        st.rerun()

    st.divider()

    if st.session_state.chain_of_thought:
        for step in st.session_state.chain_of_thought:
            if step["type"] == "thought":
                st.markdown(f"🧠 **Thought:** {step['content']}")
            elif step["type"] == "action":
                st.markdown(f"🛠️ **Action:** {step['content']}")
            elif step["type"] == "pause":
                st.markdown(f"⏸️ **PAUSE**")
            elif step["type"] == "observation":
                st.markdown(f"👁️ **Observation:** {step['content']}")
            elif step["type"] == "final_answer":
                st.markdown(f"✅ **Final Answer:** {step['content']}")
            elif step["type"] == "error":
                st.markdown(f"❌ **Error:** {step['content']}")
    else:
        st.info("The agent's reasoning steps will appear here.")

# ------------------------------------------------------------------
# Main Area - Chat Panel
# ------------------------------------------------------------------

st.title("🤖 ReAct Agent from Scratch")
st.caption("A step-by-step reasoning AI agent — built without any framework.")

# Display existing chat messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])

# ------------------------------------------------------------------
# User Input
# ------------------------------------------------------------------

if query := st.chat_input("How can I help?"):
    # Display user message
    with st.chat_message("user", avatar="👩‍💼"):
        st.markdown(query)
    st.session_state.chat_history.append({"role": "user", "content": query, "avatar": "👩‍💼"})

    # Reset chain of thought for this query
    st.session_state.chain_of_thought = []

    # Configure the agent
    agent = st.session_state.agent
    agent.current_iteration = 0
    agent.add_message("user", query)
    agent.memory_management(agent.messages)

    # Build the system prompt
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = agent.system_prompt.format(tools=agent.get_tools(), date=current_date)
    if agent.old_chats_summary:
        prompt += f"\n\nOld messages summary:\n{agent.old_chats_summary}"

    final_answer = None

    # ReAct loop for the web interface
    while agent.current_iteration < agent.max_iterations:
        agent.current_iteration += 1

        # Get LLM response
        response = agent.get_llm_response(prompt)
        agent.add_message("assistant", response)

        # Parse Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|\Z)", response, re.DOTALL)
        if thought_match:
            st.session_state.chain_of_thought.append({
                "type": "thought",
                "content": thought_match.group(1).strip(),
            })

        # Check for Final Answer
        if "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
            st.session_state.chain_of_thought.append({
                "type": "final_answer",
                "content": final_answer,
            })
            break

        # Parse Action
        action_start = response.find("Action:")
        if action_start == -1:
            st.session_state.chain_of_thought.append({
                "type": "error",
                "content": "No action or final answer found.",
            })
            break

        action_line = response[action_start:].split("\n")[0].strip()
        st.session_state.chain_of_thought.append({
            "type": "action",
            "content": action_line.replace("Action:", "").strip(),
        })
        st.session_state.chain_of_thought.append({"type": "pause", "content": ""})

        # Parse action details
        action_parts = action_line.replace("Action:", "").strip().split(":", 1)
        if len(action_parts) < 2:
            st.session_state.chain_of_thought.append({
                "type": "error",
                "content": f"Action format is incorrect: {action_line}",
            })
            break

        tool_name = action_parts[0].strip().lower()
        tool_query = action_parts[1].strip()

        # Execute tool
        tool = agent.tools.get(tool_name)
        if tool:
            import json
            if tool_name == "calculator":
                try:
                    json_data = json.loads(tool_query)
                    tool_query = json.dumps(json_data)
                except json.JSONDecodeError:
                    pass

            result = tool.run(tool_query)
            observation = f"Observation: {tool_name} tool output: {result}"
            agent.add_message("system", observation)

            obs_content = str(result)
            if len(obs_content) > 300:
                obs_content = obs_content[:300] + "..."
            st.session_state.chain_of_thought.append({
                "type": "observation",
                "content": obs_content,
            })
        else:
            error_msg = f"Tool '{tool_name}' not found"
            agent.add_message("system", f"Error: {error_msg}")
            st.session_state.chain_of_thought.append({
                "type": "error",
                "content": error_msg,
            })
            break

        # Update prompt for next iteration
        prompt = agent.system_prompt.format(tools=agent.get_tools(), date=current_date)
        if agent.old_chats_summary:
            prompt += f"\n\nOld messages summary:\n{agent.old_chats_summary}"

    # Handle max iterations reached
    if final_answer is None:
        final_answer = "I'm sorry, but I couldn't find a satisfactory answer within the allowed number of iterations."
        st.session_state.chain_of_thought.append({
            "type": "error",
            "content": "Maximum iterations reached.",
        })

    # Display assistant response
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(f"**Final Answer:** {final_answer}")
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"**Final Answer:** {final_answer}",
        "avatar": "🤖",
    })

    # Force sidebar refresh
    st.rerun()
