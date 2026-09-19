import os
import sys
import base64
import autogen
import json
import time
from urllib import request, parse
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageOps
from autogen.cache import Cache  # 💡 ADICIONE ESTA LINHA

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

def adicionar_balao_de_fala(caminho_imagem: Path, texto_dialogo: str):
    """
    Função de pós-processamento gráfico que limpa repetições do LLM,
    desenha um balão de mangá clássico e insere o diálogo por cima da imagem.
    """
    if not texto_dialogo or texto_dialogo.strip() == "":
        return

    try:
        # 🧼 TRATAMENTO DE LIMPEZA: Remove redundâncias comuns do LLM (ex: "Fubuki fala com Yuuki:")
        texto_limpo = texto_dialogo.strip()
        if ":" in texto_limpo:
            # Pega apenas o que vem depois dos dois pontos se houver descrição de fala antes
            partes = texto_limpo.split(":", 1)
            # Se o que está antes contém verbos de fala, limpa
            if any(palavra in partes[0].lower() for palavra in ["fala", "disse", "responde", "com", "para"]):
                texto_limpo = partes[1].strip()

        # Remove aspas extras que possam ter vindo no parâmetro
        texto_limpo = texto_limpo.replace('"', '').replace("'", "")

        img = Image.open(caminho_imagem).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # Tenta carregar uma fonte de quadrinhos, senão usa a padrão
        try:
            font = ImageFont.truetype("Comic_Sans_MS.ttf", 16)
        except IOError:
            font = ImageFont.load_default()

        # Configurações do texto e quebra automática de linhas (Usa o texto_limpo agora)
        largura_maxima_caracteres = 25
        palavras = texto_limpo.split()
        linhas = []
        linha_atual = ""
        
        for palavra in palavras:
            if len(linha_atual + " " + palavra) <= largura_maxima_caracteres:
                linha_atual += (" " if linha_atual else "") + palavra
            else:
                linhas.append(linha_atual)
                linha_atual = palavra
        if linha_atual:
            linhas.append(linha_atual)
            
        texto_formatado = "\n".join(linhas)

        # Calcula o tamanho do bloco de texto para dimensionar o balão
        caixa_texto = draw.textbbox((0, 0), texto_formatado, font=font)
        largura_texto = caixa_texto[2] - caixa_texto[0]
        altura_texto = caixa_texto[3] - caixa_texto[1]

        # Define a posição do balão (topo esquerdo da imagem com margem)
        margem = 20
        pad = 15
        x0 = margem
        y0 = margem
        x1 = x0 + largura_texto + (pad * 2)
        y1 = y0 + altura_texto + (pad * 2)

        # Desenha a elipse branca do balão com contorno preto (estilo mangá)
        draw.ellipse([x0, y0, x1, y1], fill="white", outline="black", width=3)
        
        # Desenha a "seta" ou cauda do balão apontando para baixo/personagem
        draw.polygon([((x0+x1)//2 - 10, y1 - 2), ((x0+x1)//2 + 10, y1 - 2), ((x0+x1)//2, y1 + 15)], fill="white", outline="black")
        draw.polygon([((x0+x1)//2 - 8, y1 - 4), ((x0+x1)//2 + 8, y1 - 4), ((x0+x1)//2, y1 + 12)], fill="white")

        # Escreve o diálogo centralizado dentro do balão
        draw.text((x0 + pad, y0 + pad), texto_formatado, fill="black", font=font)
        
        # Salva o quadrinho finalizado substituindo a imagem limpa
        final_img = img.convert("RGB")
        final_img.save(caminho_imagem, "PNG")
        print(f"🎨 [DIAGRAMAÇÃO] Balão de fala aplicado com sucesso em {caminho_imagem.name}!")
        
    except Exception as e:
        print(f"❌ Erro ao desenhar balão de fala: {str(e)}")

def desenhar_e_salvar_quadro(prompt_ingles: str, nome_arquivo_png: str, dialogo_texto: str = "") -> str:
    """
    Consome a API local do Stable Diffusion WebUI Forge e depois aplica o balão de fala clássico.
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
        url_api = f"http://{DIFFUSION_SERVER}/sdapi/v1/txt2img"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url_api, data=data, headers={"Content-Type": "application/json"})
        
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "images" in result and len(result["images"]) > 0:
                imagem_base64 = result["images"][0]
                with open(caminho_final_salvamento, "wb") as f:
                    f.write(base64.b64decode(imagem_base64))
                
                # CHAMADA CRÍTICA: Aplica o balão gráfico clássico por cima da imagem gerada
                if dialogo_texto:
                    adicionar_balao_de_fala(caminho_final_salvamento, dialogo_texto)
                
                return f"Sucesso! Imagem {nome_arquivo_png} gerada e diagramada com sucesso."
            else:
                return "Falha: A API do Forge respondeu, mas não retornou nenhuma imagem no payload."
    except Exception as e:
        return f"Falha ao conectar no Forge: {str(e)}."

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
        "temperature": 0.4
    }],
    "cache_seed": None,
    "timeout": 1200,
}

config_manager = {
    "config_list": [{
        "model": LM_MODEL_LORE,
        "base_url": LM_SERVER_V1,
        "api_key": OPENAI_API_KEY,
        "temperature": 0.0
    }],
    "cache_seed": None,
    "timeout": 1200,
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
    max_consecutive_auto_reply=25, 
    code_execution_config={"work_dir": str(output_dir), "use_docker": False},
    system_message=carrega_prompt("image_generator.md"),
    default_auto_reply="Resultado da execução processado pelo executor. Archivist_Agent, prossiga com a próxima chamada de ferramenta ou envie 'FIM' se encerrou."
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
    code_execution_config={"use_docker": False}
)

autogen.agentchat.register_function(
    salvar_capitulo_manga,
    caller=archivist_agent,
    executor=image_generator,
    name="salvar_capitulo_manga",
    description="Grava o arquivo final contendo toda a história estruturada por páginas e diálogos."
)

autogen.agentchat.register_function(
    desenhar_e_salvar_quadro,
    caller=archivist_agent,
    executor=image_generator,
    name="desenhar_e_salvar_quadro",
    description="Gera a imagem no Forge recebendo o prompt em inglês, o nome do arquivo png E o texto de diálogo do balão para diagramação."
)

def custom_speaker_selection(last_speaker, groupchat):
    messages = groupchat.messages
    if not messages:
        return lore_creator
        
    last_msg = messages[-1]
    
    if "tool_calls" in last_msg or last_speaker == archivist_agent:
        if "tool_calls" in last_msg:
            return image_generator
            
    if last_speaker == image_generator:
        return archivist_agent
        
    if last_speaker == user_proxy:
        return lore_creator
    elif last_speaker == lore_creator:
        return artist_agent
    elif last_speaker == artist_agent:
        return archivist_agent
        
    return "auto"

groupchat = autogen.GroupChat(
    agents=[user_proxy, lore_creator, artist_agent, archivist_agent, image_generator],
    messages=[],
    max_round=60,
    speaker_selection_method=custom_speaker_selection
)

manager = autogen.GroupChatManager(
    groupchat=groupchat, 
    llm_config=config_manager,
    system_message=carrega_prompt("manager.md"),
    is_termination_msg=lambda x: "FIM" in x.get("content", "").upper()
)

if __name__ == "__main__":
    ideia_manga = (
        "Crie o CAPÍTULO 1 de um mangá sobre um jovem ferreiro chamado Yuuki que descobre uma espada "
        "amaldiçoada por um dragão antigo em um reino medieval tomado pela névoa. Yuuki se torna um herói, doma o dragão e se casa com a princesa Fubuki, uma moça encantadora e com um corpo extremamente sexy e ardente."
        "Foque apenas no primeiro capítulo detalhadamente."
    )

    print("\n🚀 [AUTO-MANGA] Iniciando a esteira 100% local e automatizada...")
    print("\n💾 [CACHE] Inicializando cache em disco para otimização de tokens...")
    
    with Cache.disk(cache_seed=42) as cache:
        user_proxy.initiate_chat(
            manager, 
            message=ideia_manga,
            cache=cache  # 💡 PASSE O OBJETO DE CACHE AQUI
        )
