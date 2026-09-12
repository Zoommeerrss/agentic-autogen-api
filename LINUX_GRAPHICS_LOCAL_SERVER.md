📑 Guia de Instalação Local: Stable Diffusion WebUI Forge (Linux)

Este guia é focado exclusivamente na instalação e ativação da API do Stable Diffusion WebUI Forge no seu ambiente Linux. 

O Forge foi escolhido por consumir muito menos VRAM (memória da placa de vídeo) e ser ideal para rodar em paralelo com seus agentes do AutoGen e o LM Studio.

📋 Pré-requisitos do Sistema

Certifique-se de que sua máquina possui os pacotes essenciais instalados. 
Abra o terminal e execute:

```bash
sudo apt update
sudo apt install wget git python3 python3-venv libgl1 libglib2.0-0 -y
```

🛠️ Passo 1: Clonar o Repositório do Forge

Vamos centralizar a instalação dentro da sua pasta padrão de deploys (~/deploy):

```bash
# 1. Navegue para o seu diretório de deploys
cd ~/deploy

# 2. Clone o repositório oficial do Forge
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git

# 3. Acesse a pasta do projeto
cd stable-diffusion-webui-forge
```

📦 Passo 2: Baixar o Modelo Estilo Mangá (Checkpoint)

Para que o gerador saiba desenhar no estilo Mangá Sombrio / Medieval, você precisa de um modelo baseado em SDXL. 
Vamos baixar o Animagine XL 3.1, que possui um traço de anime/mangá limpo e de altíssima performance.
Execute os comandos abaixo para baixar o arquivo diretamente na pasta correta:

```bash
# 1. Entre na pasta dedicada aos modelos de difusão
cd models/Stable-diffusion/

# 2. Faça o download do arquivo de modelo (.safetensors)
wget -O animagineXL.safetensors https://huggingface.co

# 3. Volte para a raiz do projeto do Forge
cd ../../
```

🚀 Passo 3: Inicialização e Ativação da API para os Agentes

**Esta é a etapa crucial**. 
Para que o seu Image_Generator_Agent em Python consiga enviar comandos ao Forge, o servidor precisa ser iniciado com o parâmetro de API ativado (--api).
Execute o script de inicialização do Linux:

```bash
./webui.sh --api --listen --port 7860
```

⏳ **Nota da primeira execução**: O Forge criará um ambiente virtual interno (venv) e baixará bibliotecas pesadas de Inteligência Artifical (como o PyTorch). 
Este processo pode levar de 5 a 15 minutos dependendo da sua velocidade de internet e hardware. 
**Não feche o terminal**.
Quando a instalação terminar, o terminal exibirá a seguinte mensagem de sucesso: 

```bash
textRunning on local URL: http://127.0.0.1:7860
```


💡 Parâmetros Extras de Performance (Opcional)
Se a sua placa de vídeo (GPU) possuir pouca memória VRAM (menor que 8GB) e você notar travamentos, encerre o servidor (Ctrl + C) e reinicie-o forçando a otimização de memória baixa:

```bash
./webui.sh --api --listen --port 7860 --lowvram
```

O seu gerador de imagens está pronto e aguardando requisições na porta 7860. 
Deixe este terminal rodando em segundo plano e você poderá disparar o seu script app_manga.py.

