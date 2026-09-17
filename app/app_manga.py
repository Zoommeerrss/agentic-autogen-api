import os
import sys
import base64
import autogen
import requests
import json
import time
from urllib import request, parse
from pathlib import Path
from dotenv import load_dotenv
import gc
import torch

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

LM_SERVER_V1 = os.getenv('LM_SERVER_V1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LM_MODEL_LORE = os.getenv('LM_MODEL_LORE')
DIFFUSION_SERVER = os.getenv('DIFFUSION_SERVER')

output_dir = current_dir.parent / "output"
images_dir = output_dir / "images"
images_dir.mkdir(parents=True, exist_ok=True)
    
def desenhar_e_salvar_quadro(prompt_ingles: str, nome_arquivo_png: str) -> str:
    """
    Consome a API local do Stable Diffusion WebUI Forge (porta 7860).
    """    
    
    if not nome_arquivo_png.lower().endswith(".png"):
        nome_arquivo_png = f"{nome_arquivo_png}.png"

    caminho_final_salvamento = images_dir / nome_arquivo_png

    payload = {
        "prompt": f"masterpiece, dark fantasy manga style, black and white lineart, highly detailed ink sketch, severe crosshatching, {prompt_ingles}",
        "negative_prompt": "color, photo, realistic, lowres, bad anatomy, blurry, low quality, sketch, duplicate",
        "seed": 42,
        "steps": 20, 
        "cfg_scale": 7.0,
        "width": 512,
        "height": 512,
        "sampler_name": "Euler a",  
        "scheduler": "Automatic",
        "override_settings": {
            "sd_model_checkpoint": "Counterfeit-V3.0_fp16.safetensors"
        },
        "tiling": False,
        "restore_faces": False
    }

    try:
        print(f"\n⚡ [FORGE API] Enviando requisição para renderizar quadro: {nome_arquivo_png}...")
        
        # Retornado ao seu padrão original estrito
        url_api = f"http://{DIFFUSION_SERVER}/sdapi/v1/txt2img"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url_api, data=data, headers={"Content-Type": "application/json"})
        
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            if "images" in result and len(result["images"]) > 0:
                imagem_base64 = result["images"][0]
                
                with open(caminho_final_salvamento, "wb") as f:
                    f.write(base64.b64decode(imagem_base64))
                
                return f"Sucesso! Imagem gerada e salva localmente em: {caminho_final_salvamento}"
            else:
                return "Falha: A API do Forge respondeu, mas não retornou nenhuma imagem no payload."

    except Exception as e:
        return f"Falha ao conectar no Forge: {str(e)}. Certifique-se de iniciar o Forge com a flag '--api' ativa em {DIFFUSION_SERVER}."

def salvar_capitulo_manga(titulo_capitulo: str, conteudo_markdown: str) -> str:
    """
    Tool que o arquivista executa para salvar a lore.
    """
    try:
        arquivos_existentes = list(output_dir.glob("capitulo_*.md"))
        proximo_numero = len(arquivos_existentes) + 1
        nome_arquivo = f"capitulo_{proximo_numero}.md"
        caminho_final = output_dir / nome_arquivo

        with open(caminho_final, "w", encoding="utf-8") as file:
            file.write(conteudo_markdown)
            return f"Capítulo salvo com sucesso em: {caminho_final}"
            
    except Exception as e:
        return f"Erro ao arquivar capítulo: {str(e)}"

def carrega_prompt(nome_arquivo):
    caminho_completo = current_dir.parent / "prompts" / nome_arquivo
    try:
        with open(caminho_completo, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Você é um assistente prestativo participante de uma equipe de criação de mangás."

config_hermes = {
    "config_list": [{
        "model": LM_MODEL_LORE,
        "base_url": LM_SERVER_V1,
        "api_key": OPENAI_API_KEY,
        "temperature": 0.5 
    }],
    "cache_seed": None,
}

config_manager = {
    "config_list": [{
        "model": LM_MODEL_LORE,
        "base_url": LM_SERVER_V1,
        "api_key": OPENAI_API_KEY,
        "temperature": 0.0
    }],
    "cache_seed": None,
}

lore_creator = autogen.AssistantAgent(
    name="Lore_Creator",
    llm_config=config_hermes,
    system_message=carrega_prompt("lore_creator.md")
)

artist_agent = autogen.AssistantAgent(
    name="Artist_Agent",
    llm_config=config_hermes,
    system_message=carrega_prompt("artist_agent.md")
)

image_generator = autogen.UserProxyAgent(
    name="Image_Generator_Agent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=15, 
    code_execution_config={"work_dir": str(output_dir), "use_docker": False},
    system_message=carrega_prompt("image_generator.md"),
    default_auto_reply="Resultado da execução processado. Archivist_Agent, prossiga com o próximo passo ou envie 'FIM' caso terminei."
)

archivist_agent = autogen.AssistantAgent(
    name="Archivist_Agent",
    llm_config=config_hermes,
    system_message=carrega_prompt("archivist_agent.md")
)

user_proxy = autogen.UserProxyAgent(
    name="Autor",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    is_termination_msg=lambda x: "FIM" in x.get("content", "").upper(),
    code_execution_config={
        "use_docker": False 
    }
)

# Registro das funções utilizando o escopo correto do framework
autogen.agentchat.register_function(
    salvar_capitulo_manga,
    caller=archivist_agent,
    executor=image_generator,
    name="salvar_capitulo_manga",
    description="Grava o arquivo final contendo toda a história e TODOS os prompts projetados antes de desenhar."
)

autogen.agentchat.register_function(
    desenhar_e_salvar_quadro,
    caller=archivist_agent,
    executor=image_generator,
    name="desenhar_e_salvar_quadro",
    description="Gera uma imagem real no Forge a partir de um prompt específico pós-planejamento."
)

# Fluxo obrigatório linear estrito
allowed_transitions = {
    user_proxy: [lore_creator],
    lore_creator: [artist_agent],
    artist_agent: [archivist_agent],
    archivist_agent: [image_generator],
    image_generator: [archivist_agent]
}

groupchat = autogen.GroupChat(
    agents=[user_proxy, lore_creator, artist_agent, archivist_agent, image_generator],
    messages=[],
    max_round=40, 
    speaker_selection_method="auto",
    allowed_or_disallowed_speaker_transitions=allowed_transitions,
    speaker_transitions_type="allowed"
)

manager = autogen.GroupChatManager(
    groupchat=groupchat, 
    llm_config=config_manager,
    system_message=(
        "Você é o coordenador do grupo. Siga o fluxo linear restrito: "
        "Autor -> Lore_Creator -> Artist_Agent -> Archivist_Agent -> Image_Generator_Agent. "
        "Sempre que Archivist_Agent gerar chamadas de ferramentas, passe a vez estritamente para o Image_Generator_Agent."
    ),
    is_termination_msg=lambda x: "FIM" in x.get("content", "").upper()
)

if __name__ == "__main__":
    ideia_manga = (
        "Crie um mangá sobre um jovem ferreiro que descobre uma espada "
        "amaldiçoada por um dragão antigo em um reino medieval tomado pela névoa."
    )

    print("\n🚀 [AUTO-MANGA] Iniciando a esteira 100% local e automatizada...")
    user_proxy.initiate_chat(manager, message=ideia_manga)
