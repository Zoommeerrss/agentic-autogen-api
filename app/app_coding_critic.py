import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from autogen.cache import Cache

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

LM_SERVER_V1 = os.getenv('LM_SERVER_V1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or "local-token"
LM_MODEL_LORE = os.getenv('LM_MODEL_LORE')
DIFFUSION_SERVER = os.getenv('DIFFUSION_SERVER')

output_dir = current_dir.parent / "output"
images_dir = output_dir / "images"
images_dir.mkdir(parents=True, exist_ok=True)

OAI_CONFIG_LIST = os.getenv('OAI_CONFIG_LIST')

config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

def carrega_prompt(nome_arquivo):
    caminho_completo = current_dir.parent / "prompts" / nome_arquivo
    try:
        with open(caminho_completo, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Você é um assistente prestativo participante de uma equipe de criação de programas Python."

user_proxy = UserProxyAgent(
    "user",
    code_execution_config={
        "work_dir": output_dir,
        "use_docker": False,
        "last_n_messages": 1,
    },
    human_input_mode="ALWAYS",
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

engineer = AssistantAgent(
    name="Engineer",
    llm_config={"config_list": config_list},
    system_message=carrega_prompt("engineer_agent.md")
)

critic = AssistantAgent(
    name="Reviewer",
    llm_config={"config_list": config_list},
    system_message=carrega_prompt("critic_agent.md")
)

def review_code(recipient, messages, sender, config):
    return f"""
        Review and critque the following code.
        {recipient.chat_messages_for_summary(sender)[-1]['content']}
        """
    
user_proxy.register_nested_chats(
    [
        {
            "recipient": critic,
            "message": review_code,
            "summary_method": "last_msg",
            "max_turns": 1,
        }
    ],
    trigger=engineer,
)

task = """Write a snake game using Pygame."""

print("\n💾 [CACHE] Inicializando cache em disco para otimização de tokens...")

with Cache.disk(cache_seed=42) as cache:
    res = user_proxy.initiate_chat(
        recipient=engineer,
        message=task,
        max_turns=2,
        summary_method="last_msg",
        cache=cache,  # Passa o objeto de cache configurado aqui
    )