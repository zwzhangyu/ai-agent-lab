import json
import os
import pkgutil
import importlib
import re
from datetime import datetime
from pathlib import Path

import tiktoken
from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv
from openai import OpenAI

from tools.base_tool import BaseTool
from utils.message import Message

# Load environment variables from project root .env
load_dotenv(Path(__file__).resolve().parents[3] / '.env', override=True)
os.environ['NO_PROXY'] = '*'
colorama_init(autoreset=True)


class ReActAgent:
    """A ReAct (Reasoning + Acting) AI Agent built from scratch without any framework.

    The agent operates in a loop of Thought → Action → PAUSE → Observation,
    iteratively refining its response until a Final Answer is produced.
    """

    def __init__(self):
        # Initialize LLM client (DashScope OpenAI-compatible API)
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = os.getenv("LLM_MODEL", "qwen-max")

        # Conversation history
        self.messages = []

        # Load prompt templates
        prompts_dir = Path(__file__).parent / "prompts"
        with open(prompts_dir / "system_prompt.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        with open(prompts_dir / "summary_prompt.txt", "r", encoding="utf-8") as f:
            self.summary_prompt = f.read()

        # Register tools dynamically from the tools/ directory
        self.tools = {}
        self.register_tools()

        # Iteration control
        self.current_iteration = 0
        self.max_iterations = 10

        # Memory management
        self.messages_to_summarize = 3
        self.max_messages_tokens = 1000
        self.llm_max_tokens = 2000
        self.old_chats_summary = ""

        # Tokenizer for token counting
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    # ------------------------------------------------------------------
    # Tool Registration
    # ------------------------------------------------------------------

    def register_tools(self):
        """Dynamically discover and register all tools from the tools/ directory."""
        tool_modules = [name for _, name, _ in pkgutil.iter_modules(["tools"])]

        for module_name in tool_modules:
            try:
                module = importlib.import_module(f"tools.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseTool) and attr is not BaseTool:
                        tool_instance = attr()
                        self.tools[tool_instance.name.lower()] = tool_instance
            except Exception as e:
                print(f"[ERROR] Failed to register tool {module_name}: {e}")

    def get_tools(self):
        """Return a formatted string of available tools and their descriptions."""
        tools_str = ""
        for name, tool in self.tools.items():
            tools_str += f"- {name}: {tool.description}\n"
        return tools_str

    # ------------------------------------------------------------------
    # LLM Interaction
    # ------------------------------------------------------------------

    def get_llm_response(self, prompt):
        """Send the full message history along with the system prompt to the LLM."""
        messages = [{"role": "system", "content": prompt}]
        for msg in self.messages:
            messages.append({"role": msg["role"], "content": str(msg["content"])})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.llm_max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: Failed to get LLM response - {str(e)}"

    # ------------------------------------------------------------------
    # Token Management
    # ------------------------------------------------------------------

    def num_tokens_from_text(self, text):
        """Count the number of tokens in a text string."""
        return len(self.encoding.encode(str(text)))

    def num_tokens_from_messages(self, messages):
        """Count the total number of tokens in a list of messages."""
        return sum(self.num_tokens_from_text(msg["content"]) for msg in messages)

    # ------------------------------------------------------------------
    # Memory Management
    # ------------------------------------------------------------------

    def get_indices(self, chat_history):
        """Extracts the start and end indices of the first N user messages to summarize."""
        user_indices = [i for i, msg in enumerate(chat_history) if msg["role"] == "user"]

        if len(user_indices) <= self.messages_to_summarize:
            return None

        start_index = user_indices[0]
        end_index = user_indices[self.messages_to_summarize]

        return start_index, end_index

    def summarize_old_chats(self, chats):
        """Summarizes old chat history and returns a concise summary."""
        prompt = self.summary_prompt.format(chats=chats)
        messages = [{"role": "system", "content": prompt}]

        try:
            raw_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.llm_max_tokens,
            )
            response = raw_response.choices[0].message.content
            return response.strip() if response else "No response from LLM"
        except Exception as e:
            print(f"Error during summarization: {e}")
            return "No response from LLM"

    def memory_management(self, chat_history):
        """Manages memory by summarizing and deleting old chat history when token limits are exceeded."""
        try:
            user_messages = [msg for msg in chat_history if msg["role"] == "user"]
            if len(user_messages) > self.messages_to_summarize and self.num_tokens_from_messages(chat_history) > self.max_messages_tokens:
                indices = self.get_indices(chat_history)
                if indices:
                    start_index, end_index = indices
                    chats = chat_history[start_index:end_index]
                    new_summary = self.summarize_old_chats(chats)
                    print(f"##### Tokens used by the old messages: {self.num_tokens_from_messages(chats)}")
                    if new_summary != "No response from LLM":
                        print(f"##### Tokens used by the new summary: {self.num_tokens_from_text(new_summary)}")
                        self.old_chats_summary = f"{self.old_chats_summary} {new_summary}".strip()
                        print("##### Old messages summary : ", self.old_chats_summary)
                        del self.messages[start_index:end_index]
        except Exception as e:
            print(f"An error occurred during memory management: {e}")

    # ------------------------------------------------------------------
    # Message Helpers
    # ------------------------------------------------------------------

    def add_message(self, role, content):
        """Add a message to the conversation history."""
        self.messages.append(Message(role, str(content)))

    # ------------------------------------------------------------------
    # Core ReAct Loop
    # ------------------------------------------------------------------

    def think(self):
        """Core reasoning step: increment iteration, call LLM, parse and execute actions."""
        self.current_iteration += 1

        if self.current_iteration > self.max_iterations:
            print(f"\n{Fore.YELLOW}Reached maximum iterations. Stopping.{Style.RESET_ALL}")
            self.add_message(
                "assistant",
                "I'm sorry, but I couldn't find a satisfactory answer within the allowed number of iterations.",
            )
            return

        # Build system prompt with available tools and current date
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = self.system_prompt.format(tools=self.get_tools(), date=current_date)

        # Inject old chat summary if available
        if self.old_chats_summary:
            prompt += f"\n\nOld messages summary:\n{self.old_chats_summary}"

        # Get LLM response
        response = self.get_llm_response(prompt)
        self.add_message("assistant", response)

        # Display the thought
        self.format_output(response)

        # Parse and execute any action in the response
        self.determine_action(response)

    def determine_action(self, response):
        """Parse the LLM response to find and execute an Action, or stop if Final Answer is found."""
        if "Final Answer:" in response:
            return

        action_start = response.find("Action:")

        if action_start == -1:
            print(f"{Fore.YELLOW}No action or final answer found in the response.{Style.RESET_ALL}")
            return

        action_line = response[action_start:].split("\n")[0].strip()
        action_parts = action_line.replace("Action:", "").strip().split(":", 1)

        if len(action_parts) < 2:
            print(f"{Fore.RED}Error: Action format is incorrect: {action_line}{Style.RESET_ALL}")
            return

        tool_name = action_parts[0].strip().lower()
        query = action_parts[1].strip()

        # Special handling for calculator (JSON format)
        if tool_name == "calculator":
            try:
                json_data = json.loads(query)
                if "operation" not in json_data:
                    print(f"{Fore.RED}Error: Missing 'operation' in calculator JSON: {query}{Style.RESET_ALL}")
                    return
                query = json.dumps(json_data)
            except json.JSONDecodeError:
                print(f"{Fore.RED}Error: Invalid JSON input for calculator: {query}{Style.RESET_ALL}")
                return

        self.execute_action(tool_name, query)

    def execute_action(self, tool_name, query):
        """Execute the specified tool and feed the observation back into the reasoning loop."""
        tool = self.tools.get(tool_name)

        if tool:
            result = tool.run(query)
            observation = f"Observation: {tool_name} tool output: {result}"
            self.add_message("system", observation)

            print(f"{Fore.CYAN}\n[SYSTEM]:{Style.RESET_ALL} {observation}\n")

            # Recursively re-enter the reasoning loop
            self.think()
        else:
            error_msg = f"Error: Tool '{tool_name}' not found"
            print(f"\n{Fore.RED}{error_msg}{Style.RESET_ALL}")
            self.add_message("system", error_msg)
            self.think()

    # ------------------------------------------------------------------
    # Output Formatting
    # ------------------------------------------------------------------

    def format_output(self, response):
        """Format output with colors for better readability in the terminal."""
        response = re.sub(r"Final Answer:", f"{Fore.RED}\n[FINAL ANSWER]:{Style.RESET_ALL}", response)
        response = re.sub(r"Action:", f"{Fore.YELLOW}\n[ACTION]:{Style.RESET_ALL}", response)
        response = re.sub(r"PAUSE", f"{Fore.MAGENTA}\n[PAUSE]:{Style.RESET_ALL}", response)

        print(f"{Fore.GREEN}\n[ASSISTANT]:{Style.RESET_ALL} {response}\n")

    # ------------------------------------------------------------------
    # Public Interface
    # ------------------------------------------------------------------

    def run(self, query):
        """Run the agent with a user query through the full ReAct loop."""
        self.current_iteration = 0
        self.add_message("user", query)

        # Perform memory management before starting the reasoning loop
        self.memory_management(self.messages)

        # Start the ReAct loop
        self.think()

        # Extract and return the final answer
        final_answer = ""
        for msg in reversed(self.messages):
            if "Final Answer:" in msg["content"]:
                final_answer = msg["content"].split("Final Answer:")[-1].strip()
                break

        return final_answer if final_answer else "I couldn't find an answer."

    def reset(self):
        """Reset the agent's conversation history and state."""
        self.messages = []
        self.current_iteration = 0
        self.old_chats_summary = ""


# ------------------------------------------------------------------
# CLI Entry Point
# ------------------------------------------------------------------

if __name__ == "__main__":
    agent = ReActAgent()

    print(f"{Fore.GREEN}{'=' * 60}")
    print(f"  ReAct Agent - Interactive Mode")
    print(f"  Type 'quit' or 'exit' to stop.")
    print(f"  Type 'reset' to clear conversation history.")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")

    while True:
        try:
            query = input(f"{Fore.BLUE}User: {Style.RESET_ALL}").strip()
            if not query:
                continue
            if query.lower() in ("quit", "exit"):
                print("Goodbye!")
                break
            if query.lower() == "reset":
                agent.reset()
                print(f"{Fore.YELLOW}Conversation history cleared.{Style.RESET_ALL}")
                continue

            answer = agent.run(query)
            print(f"\n{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Final Answer: {answer}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}\n")
