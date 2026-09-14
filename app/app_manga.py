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

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

LM_SERVER_V1 = os.getenv('LM_SERVER_V1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LM_MODEL_LORE = os.getenv('LM_MODEL_LORE')

output_dir = current_dir.parent / "output"
images_dir = output_dir / "images"
images_dir.mkdir(parents=True, exist_ok=True)

def desenhar_e_salvar_quadro(prompt_ingles: str, nome_arquivo_png: str) -> str:
    """
    Consome a API local do ComfyUI na abordagem oficial (urllib.request).
    Estratégia 'Dispara e Desapega': Envia o prompt para a fila da GPU e encerra o turno,
    deixando o ComfyUI renderizar e salvar o arquivo de forma assíncrona.
    """
    SERVER_ADDRESS = "127.0.0.1:8188"
    
    if not nome_arquivo_png.lower().endswith(".png"):
        nome_arquivo_png = f"{nome_arquivo_png}.png"

    # WORKFLOW API OFICIAL: Configura o nó de salvamento final para gravar direto na pasta certa
    # Usando o caminho absoluto do seu projeto para salvar nativamente sem intermediação do loop Python
    caminho_absoluto_salvamento = str(images_dir / nome_arquivo_png.replace(".png", ""))

    workflow_comfy = {
        "4": {
            "inputs": {"ckpt_name": "animagine-xl-3.1.safetensors"},
            "class_type": "CheckpointLoaderSimple"
        },
        "6": {
            "inputs": {
                "text": f"masterpiece, dark fantasy manga style, black and white lineart, highly detailed ink sketch, severe crosshatching, {prompt_ingles}",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {
                "text": "color, photo, realistic, lowres, bad anatomy, blurry, low quality, sketch, duplicate",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "5": {
            "inputs": {
                "seed": 42, 
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral", 
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["8", 0]
            },
            "class_type": "KSampler"
        },
        "8": {
            "inputs": {"width": 640, "height": 960, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        },
        "9": {
            "inputs": {"samples": ["5", 0], "vae": ["4", 2]},
            "class_type": "VAEDecode"
        },
        "10": {
            "inputs": {
                "filename_prefix": caminho_absoluto_salvamento, 
                "images": ["9", 0]
            },
            "class_type": "PreviewImage" 
        }
    }

    try:
        print(f"\n⚡ [COMFYUI API] Injetando quadro na fila de processamento: {nome_arquivo_png}...")
        
        # ABORDAGEM OFICIAL DO PORTAL: ENVIO DO PROMPT
        p = {"prompt": workflow_comfy}
        data = json.dumps(p).encode("utf-8")
        req = request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data, headers={"Content-Type": "application/json"})
        
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            prompt_id = result.get("prompt_id")
            
        # RETORNO IMEDIATO: Libera o agente técnico sem loops de timeout
        return f"Sucesso! Comando enviado para a fila do ComfyUI (ID: {prompt_id}). A imagem será gerada em segundo plano."

    except Exception as e:
        return f"Falha ao conectar no ComfyUI: {str(e)}. Certifique-se de que o ComfyUI está ativo em {SERVER_ADDRESS}."

def salvar_capitulo_manga(titulo_capitulo: str, conteudo_markdown: str) -> str:
    """
    Tool que o arquivista executa para salvar a lore.
    Nomeia o arquivo automaticamente como capitulo_1.md, capitulo_2.md, etc.
    """
    try:
        # 1. Lista todos os arquivos .md existentes na pasta output
        arquivos_existentes = list(output_dir.glob("capitulo_*.md"))
        
        # 2. Define o próximo número sequencial com base na quantidade de arquivos existentes
        proximo_numero = len(arquivos_existentes) + 1
        
        # 3. Força o padrão rígido e limpo de nomenclatura
        nome_arquivo = f"capitulo_{proximo_numero}.md"
        caminho_final = output_dir / nome_arquivo

        # 4. Grava o conteúdo físico no SSD do WSL
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
    max_consecutive_auto_reply=15, # Expandido para aguentar o lote contínuo de imagens no final
    code_execution_config={"work_dir": str(output_dir), "use_docker": False},
    system_message=carrega_prompt("image_generator.md")
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
    is_termination_msg=lambda x: "FIM" in x.get("content", "").upper()
)

autogen.register_function(
    salvar_capitulo_manga,
    caller=archivist_agent,
    executor=image_generator,
    name="salvar_capitulo_manga",
    description="Grava o arquivo final contendo toda a história e TODOS os prompts projetados antes de desenhar."
)

autogen.register_function(
    desenhar_e_salvar_quadro,
    caller=archivist_agent, # AGORA EXCLUSIVO: O arquivista executa o lote após salvar o documento completo
    executor=image_generator,
    name="desenhar_e_salvar_quadro",
    description="Gera uma imagem real no Forge a partir de um prompt específico pós-planejamento."
)

image_generator.register_function(
    function_map={
        "desenhar_e_salvar_quadro": desenhar_e_salvar_quadro,
        "salvar_capitulo_manga": salvar_capitulo_manga,
    }
)

allowed_transitions = {
    user_proxy: [lore_creator],                # O Autor só passa a bola para o criador da história
    lore_creator: [artist_agent],              # A história vai para o designer de prompts
    artist_agent: [archivist_agent],            # Os prompts vão para o arquivista compilar tudo
    archivist_agent: [image_generator],         # O arquivista chama as ferramentas (salvar_md e desenhar)
    image_generator: [archivist_agent]          # O executor devolve o sucesso sempre para o arquivista
}

groupchat = autogen.GroupChat(
    agents=[user_proxy, lore_creator, artist_agent, archivist_agent, image_generator],
    messages=[],
    max_round=35,
    speaker_selection_method="auto",
    allowed_or_disallowed_speaker_transitions=allowed_transitions, # Força o grafo de estados
    speaker_transitions_type="allowed"
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=config_hermes)

if __name__ == "__main__":
    ideia_manga = (
        "Crie um mangá sobre um jovem ferreiro que descobre uma espada "
        "amaldiçoada por um dragão antigo em um reino medieval tomado pela névoa."
    )

    print("\n🚀 [AUTO-MANGA] Iniciando a esteira 100% local e automatizada...")
    user_proxy.initiate_chat(manager, message=ideia_manga)
