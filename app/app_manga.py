import os
import sys
import base64
import autogen
import requests
from pathlib import Path
from dotenv import load_dotenv

# 1. ENCONTRA OS DIRETÓRIOS E CONFIGURA O PATH
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
    Consome a API local do Stable Diffusion Forge.
    Transforma as ideias ampliadas em arte manga física.
    """
    url_forge_api = "http://localhost:7860/sdapi/v1/txt2img"
    caminho_salvamento = images_dir / nome_arquivo_png

    # Adicionado cabeçalho explícito para APIs locais robustas
    headers = {"Content-Type": "application/json"}

    payload = {
        "prompt": f"masterpiece, dark fantasy manga style, black and white lineart, highly detailed ink sketch, severe crosshatching, {prompt_ingles}",
        "negative_prompt": "color, photo, realistic, lowres, bad anatomy, blurry, low quality, sketch, duplicate",
        "steps": 28,
        "cfg_scale": 7.0,
        "width": 832,
        "height": 1216,
        "sampler_name": "Euler a"
    }

    try:
        print(f"\n🎨 [FORGE] Solicitando ilustração local para o quadro: {nome_arquivo_png}...")
        response = requests.post(url_forge_api, json=payload, headers=headers, timeout=120)

        if response.status_code == 200:
            result = response.json()
            if 'images' in result and len(result['images']) > 0:
                image_base64 = result['images'][0]
                image_bytes = base64.b64decode(image_base64)

                with open(caminho_salvamento, 'wb') as f:
                    f.write(image_bytes)
                    return f"Sucesso! Ilustração salva localmente em: {caminho_salvamento}"
            else:
                return "Erro: Resposta do Forge válida, mas a lista de imagens veio vazia."
        else:
            return f"Erro na API do Forge (Status {response.status_code}): {response.text}"

    except Exception as e:
        return f"Falha ao conectar no Forge: {str(e)}. Certifique-se de que o Forge está ativo com --api."


def salvar_capitulo_manga(titulo_capitulo: str, conteudo_markdown: str) -> str:
    """
    Tool que o arquivista vai executar para salvar a lore final na sua máquina.
    """
    try:
        nome_arquivo = f"{titulo_capitulo.lower().replace(' ', '_')}.md"
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
        "temperature": 0.5 # Reduzido levemente para melhorar a precisão em chamadas de função locais
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
    max_consecutive_auto_reply=10, # Expandido para comportar a iteração de execução contínua
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

# Registro das Ferramentas com escopos corrigidos
autogen.register_function(
    desenhar_e_salvar_quadro,
    caller=artist_agent,
    executor=image_generator,
    name="desenhar_e_salvar_quadro",
    description="Gera um arquivo de imagem real estilo mangá localmente a partir de um prompt em inglês."
)

autogen.register_function(
    salvar_capitulo_manga,
    caller=archivist_agent,
    executor=image_generator,
    name="salvar_capitulo_manga",
    description="Grava o arquivo final do capítulo no formato Markdown na máquina local."
)

# CORREÇÃO: Vinculação de fluxo dinâmico auto-gerenciado para modelos locais
groupchat = autogen.GroupChat(
    agents=[user_proxy, lore_creator, artist_agent, image_generator, archivist_agent],
    messages=[],
    max_round=25,
    speaker_selection_method="auto" # 'auto' permite ao orquestrador chavear para o executor correto após chamadas de tools
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=config_hermes)

if __name__ == "__main__":
    ideia_manga = (
        "Crie um mangá sobre um jovem ferreiro que descobre uma espada "
        "amaldiçoada por um dragão antigo em um reino medieval tomado pela névoa."
    )

    print("\n🚀 [AUTO-MANGA] Iniciando a esteira 100% local e automatizada...")
    user_proxy.initiate_chat(manager, message=ideia_manga)
