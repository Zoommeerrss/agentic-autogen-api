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

# CORREÇÃO: Tirado de dentro do 'if' para garantir que as variáveis sempre carreguem
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

# LM Server endpoints carregados dinamicamente do seu .env
LM_SERVER_V1 = os.getenv('LM_SERVER_V1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Modelos do LM Studio (Multi-Model Session)
LM_MODEL_LORE = os.getenv('LM_MODEL_LORE')
LM_MODEL_ARTIST = os.getenv('LM_MODEL_ARTIST')

# Garante que as pastas de saída existam no seu projeto
output_dir = current_dir.parent / "output"
images_dir = output_dir / "images"
images_dir.mkdir(parents=True, exist_ok=True)


def desenhar_e_salvar_quadro(prompt_ingles: str, nome_arquivo_png: str) -> str:
    """
    Consome a API local do Stable Diffusion Forge que você instalou.
    Transforma as ideias ampliadas do MagicPrompt em arte manga física.
    """
    url_forge_api = "http://127.0.0"
    caminho_salvamento = images_dir / nome_arquivo_png

    # Configuração calibrada para o modelo Animagine XL (estilo Mangá em P&B)
    payload = {
        "prompt": f"masterpiece, dark fantasy manga style, black and white lineart, highly detailed ink sketch, severe crosshatching, {prompt_ingles}",
        "negative_prompt": "color, photo, realistic, lowres, bad anatomy, blurry, low quality",
        "steps": 28,
        "cfg_scale": 7,
        "width": 832,   # Formato excelente para visualização de quadrinho
        "height": 1216, # Formato vertical tradicional de página
        "sampler_name": "Euler a"
    }

    try:
        print(f"\n🎨 [FORGE] Solicitando ilustração local para o quadro: {nome_arquivo_png}...")
        response = requests.post(url_forge_api, json=payload, timeout=90)

        if response.status_code == 200:
            result = response.json()
            # O Forge envia uma lista de strings em Base64 na chave 'images'
            image_base64 = result['images'][0]
            image_bytes = base64.b64decode(image_base64)

            with open(caminho_salvamento, 'wb') as f:
                f.write(image_bytes)

                return f"Sucesso! Ilustração salva localmente em: {caminho_salvamento}"
        else:
            return f"Erro na API do Forge: {response.text}"

    except Exception as e:
        return f"Falha ao conectar no Forge: {str(e)}. Certifique-se de que o terminal do Forge está ativo com --api."


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
        print(f"AVISO: Arquivo de prompt {nome_arquivo} não encontrado em {caminho_completo}. Usando prompt genérico.")
        return "Você é um assistente prestativo."


config_lore = {
    "config_list": [{
        "model": LM_MODEL_LORE,
        "base_url": LM_SERVER_V1,
        "api_key": OPENAI_API_KEY,
        "temperature": 0.7
    }],
    "cache_seed": None,
}

config_artist = {
    "config_list": [{
        "model": LM_MODEL_ARTIST,
        "base_url": LM_SERVER_V1,
        "api_key": OPENAI_API_KEY,
        "temperature": 0.5  # Temperatura ligeiramente mais baixa para o criador de prompts manter foco estrutural
    }],
    "cache_seed": None,
}

lore_master = autogen.AssistantAgent(
    name="Lore_Master",
    llm_config=config_lore,
    system_message=carrega_prompt("lore_master.md")
)

artist_agent = autogen.AssistantAgent(
    name="Artist_Agent",
    llm_config=config_artist,
    system_message=carrega_prompt("artist_agent.md")
)

image_generator = autogen.UserProxyAgent(
    name="Image_Generator_Agent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config={"work_dir": str(output_dir), "use_docker": False},
    system_message="Você é o braço executor de arte. Sua única tarefa é pegar os prompts em inglês do Artist_Agent e chamar a função 'desenhar_e_salvar_quadro'."
)

# AJUSTE: Vinculado à inteligência principal do Hermes para consolidação de texto
archivist_agent = autogen.AssistantAgent(
    name="Archivist_Agent",
    llm_config=config_lore,
    system_message=(
        "Você é o arquivista final do projeto. Seu papel é coletar a história em português criada pelo Lore_Master, "
        "reunir com as referências visuais e usar a função 'salvar_capitulo_manga' para gravar o arquivo final. "
        "Assim que salvar, finalize com a palavra 'FIM'."
    )
)

user_proxy = autogen.UserProxyAgent(
    name="Autor",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=2,
    is_termination_msg=lambda x: "FIM" in x.get("content", "").upper()
)

autogen.agentutils.register_function(
    desenhar_e_salvar_quadro,
    caller=artist_agent,
    executor=image_generator,
    name="desenhar_e_salvar_quadro",
    description="Gera uma imagem real estilo mangá localmente a partir de um prompt ampliado em inglês."
)

autogen.agentutils.register_function(
    salvar_capitulo_manga,
    caller=archivist_agent,
    executor=image_generator,
    name="salvar_capitulo_manga",
    description="Grava o arquivo final do capítulo no formato Markdown na máquina local."
)

groupchat = autogen.GroupChat(
    agents=[user_proxy, lore_master, artist_agent, image_generator, archivist_agent],
    messages=[],
    max_round=12
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=config_lore)

if __name__ == "__main__":
    ideia_manga = (
        "Crie um mangá sobre um jovem ferreiro que descobre uma espada "
        "amaldiçoada por um dragão antigo em um reino medieval tomado pela névoa."
    )

    print("Iniciando a esteira 100% local e automatizada de Mangá...")
    user_proxy.initiate_chat(manager, message=ideia_manga)
