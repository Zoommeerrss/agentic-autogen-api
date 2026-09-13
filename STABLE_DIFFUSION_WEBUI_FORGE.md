# 📑 Guia Completo de Instalação e Troubleshooting: Stable Diffusion WebUI Forge (Linux)

Este guia consolida os procedimentos de instalação local e as resoluções para os erros mais comuns de ambiente, dependências e carregamento de modelos encontrados ao configurar o Forge para atuar como a API local de geração de imagens integrada ao ecossistema de agentes AutoGen e ao LM Studio.

O Forge foi escolhido por consumir muito menos VRAM (memória da placa de vídeo) e ser ideal para rodar em paralelo com seus agentes.

---

## 📌 Índice Geral
1. [📋 Pré-requisitos do Sistema](#-pré-requisitos-do-sistema)
2. [🛠️ Passo 1: Clonar o Repositório do Forge](#️-passo-1-clonar-o-repositório-do-forge)
3. [🚀 Passo 2: Inicialização e Ativação da API](#-passo-2-inicialização-e-ativação-da-api)
4. [🛑 3. Resolução de Problemas (Troubleshooting)](#-3-resolução-de-problemas-troubleshooting)
   - [3.1 Incompatibilidade de Versão do Python e falha no build do CLIP](#31-incompatibilidade-de-versão-do-python-e-falha-no-build-do-clip)
   - [3.2 Erro de tamanho de tipo do NumPy (`ValueError: numpy.dtype size changed`)](#32-erro-de-tamanho-de-tipo-do-numpy-valueerror-numpydtype-size-changed)
   - [3.3 Modelo Incompleto, Corrompido ou Erros de Download com wget (`AssertionError`)](#33-modelo-incompleto-corrompido-ou-erros-de-download-com-wget-assertionerror)
   - [3.4 A API externa não consegue conectar ao Forge (`ConnectionRefusedError`)](#34-a-api-externa-não-consegue-conectar-ao-forge-connectionrefusederror)
   - [3.5 Avisos de TCMalloc, Dependências Omitidas e Cache](#35-avisos-de-tcmalloc-dependências-omitidas-e-cache)
   - [3.6 Problemas com o OpenAI CLIP](#36-problemas-com-o-openai-clip)

---

## 📋 Pré-requisitos do Sistema

Certifique-se de que sua máquina possui os pacotes essenciais instalados. Abra o terminal e execute:

```bash
sudo apt update
sudo apt install wget git python3 python3-venv libgl1 libglib2.0-0 -y
```

---

## 🛠️ Passo 1: Clonar o Repositório do Forge

Vamos centralizar a instalação dentro da sua pasta padrão de deploys (`/home/emerzoom/deploy`):

```bash
# 1. Navegue para o seu diretório de deploys
cd /home/emerzoom/deploy

# 2. Clone o repositório oficial do Forge
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git

# 3. Acesse a pasta do projeto
cd stable-diffusion-webui-forge
```

---

## 🚀 Passo 2: Inicialização e Ativação da API para os Agentes

> ⚠️ **Esta é a etapa crucial**: Para que o seu `Image_Generator_Agent` em Python consiga enviar comandos ao Forge, o servidor precisa ser iniciado com o parâmetro de API ativado (`--api`).

Execute o script de inicialização do Linux:

```bash
./webui.sh --api --listen --port 7860
```

### ⏳ Nota da primeira execução
O Forge criará um ambiente virtual interno (`venv`) e baixará bibliotecas pesadas de Inteligência Artificial (como o PyTorch). 
* Este processo pode levar de **5 a 15 minutos** dependendo da sua velocidade de internet e hardware. 
* **Não feche o terminal.**

Quando a instalação terminar, o terminal exibirá a seguinte mensagem de sucesso: 

```text
Running on local URL: http://127.0.0.1:7860
```

---

## 🛑 3. Resolução de Problemas (Troubleshooting)

### 3.1 Incompatibilidade de Versão do Python e falha no build do CLIP

#### 🔍 Sintoma
O script de inicialização do Forge falha no meio do processo com mensagens de erro como `ModuleNotFoundError: No module named 'pkg_resources'` ou falha ao compilar rodas (*wheels*) de pacotes como `clip`, `scikit-image` ou `scipy` através do compilador C++ (`pythran`/`ninja`).

#### 💡 Causa Raiz
O Forge e o ecossistema de difusão clássico **não possuem suporte estável ao Python 3.12+**. Versões novas do Python removeram ferramentas de empacotamento antigas que bibliotecas de IA legadas exigem para compilar o código-fonte nativo no Linux.

#### 🛠️ Resolução
Forçar a criação do ambiente virtual utilizando explicitamente o **Python 3.10** (a versão homologada para Stable Diffusion):

1. Instale o interpretador correto no sistema:
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa -y
   sudo apt update
   sudo apt install python3.10 python3.10-venv python3.10-dev -y
   ```
2. Delete a pasta do ambiente virtual quebrado dentro do Forge:
   ```bash
   rm -rf /home/emerzoom/deploy/stable-diffusion-webui-forge/venv
   ```
3. Recrie a sandbox travada na versão correta do Python:
   ```bash
   python3.10 -m venv /home/emerzoom/deploy/stable-diffusion-webui-forge/venv
   ```

---

### 3.2 Erro de tamanho de tipo do NumPy (`ValueError: numpy.dtype size changed`)

#### 🔍 Sintoma
O terminal exibe o erro fatal durante a inicialização:
```text
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject
```

#### 💡 Causa Raiz
O instalador baixou o **NumPy v2.x**, mas as extensões gráficas internas do Forge (como `scikit-image` e o gerenciador do `ControlNet`) dependem da estrutura binária clássica do **NumPy 1.x**. O choque de versões causa corrupção de memória em runtime.

#### 🛠️ Resolução
Fazer o downgrade forçado do pacote matemático para a última versão estável da árvore anterior (`1.26.4`):

```bash
# 1. Ative o ambiente virtual interno do Forge
source /home/emerzoom/deploy/stable-diffusion-webui-forge/venv/bin/activate

# 2. Force a reinstalação travando na versão estável
pip install "numpy<2.0.0" --force-reinstall

# 3. Saia do ambiente virtual
deactivate
```
*(Nota: Avisos do pip sobre o pacote `opencv-contrib-python` preferir o NumPy 2.x podem ser ignorados com segurança; o Forge exige o NumPy 1.x para funcionar).*

---

### 3.3 Modelo Incompleto, Corrompido ou Erros de Download com wget (`AssertionError`)

#### 🔍 Sintoma
O Forge inicia, mas exibe erros repetidos de asserção apontando para o arquivo do modelo ou o download via `wget`/`curl` falha repetidamente, gera arquivos corrompidos de poucos kilobytes ou apresenta erro de travamento. O console do Forge acusa: `You do not have any model!`.

#### 💡 Causa Raiz
Servidores do Hugging Face utilizam múltiplos redirecionamentos de CDN que frequentemente quebram utilitários de download direto como o `wget` quando manipulando arquivos binários massivos (como pesos de ~6.5 GB). Além disso, baixar atualizações manuais do CLI (`pip install -U`) fora de uma versão fixa gera quebra de dependências com o `transformers` e o `tokenizers`.

#### 🛠️ Resolução
A forma mais robusta de baixar modelos grandes no Ubuntu sem corrupção é utilizando o gerenciador oficial da API deles (`huggingface-cli`) cravado na versão compatível com o Forge.

*(Nota: O link base original do repositório é https://huggingface.co)*

```bash
# 1. Entre no diretório do projeto e ative o ambiente virtual
cd /home/emerzoom/deploy/stable-diffusion-webui-forge/
source venv/bin/activate

# 2. Garanta a instalação da versão estável do SDK (Evita conflitos de tokenizers/transformers)
pip install "huggingface_hub==0.26.2" --force-reinstall

# 3. Baixe o arquivo .safetensors injetando-o diretamente na pasta final (Desativando Links Simbólicos)
huggingface-cli download cagliostrolab/animagine-xl-3.1 animagine-xl-3.1.safetensors --local-dir /home/emerzoom/deploy/stable-diffusion-webui-forge/models/Stable-diffusion/ --local-dir-use-symlinks False

# 4. Desative a VENV após o download atingir 100%
deactivate
```

---

### 3.4 A API externa não consegue conectar ao Forge (`ConnectionRefusedError`)

#### 🔍 Sintoma
O script Python dos agentes do AutoGen dispara erros do tipo `requests.exceptions.ConnectionError: HTTPConnectionPool... Connection refused`.

#### 💡 Causa Raiz
O Forge foi iniciado de forma isolada para navegação local por padrão, travando o acesso de chamadas externas de código ou scripts Python em outras portas de rede.

#### 🛠️ Resolução
Sempre inicialize o servidor injetando as flags **`--api`** (libera os endpoints JSON que os agentes consomem) e **`--listen`** (permite que o servidor ouça chamadas internas de rede). Se a sua placa de vídeo possuir pouca VRAM (menor que 8GB), inclua também a flag opcional `--lowvram`.

*Atenção: A flag `--medvram-sdxl` foi descontinuada nas versões recentes do Forge. O gerenciamento de VRAM agora é dinâmico e automático baseado no seu hardware (ex: GTX 1660 Ti).*

```bash
cd /home/emerzoom/deploy/stable-diffusion-webui-forge
./webui.sh --api --listen --port 7860 --skip-python-version-check
```

---

### 3.5 Avisos de TCMalloc, Dependências Omitidas e Cache

#### 🟢 Warning do pacote TCMalloc
Se o terminal exibir `Cannot locate TCMalloc. Do you have tcmalloc or google-perftool installed...`, instale as ferramentas de otimização de memória do Google para melhorar o uso de CPU:
```bash
sudo apt update && sudo apt install libgoogle-perftools4 libtcmalloc-minimal4 -y
```

#### 🟢 Ausência da biblioteca `joblib`
Caso o ambiente acuse falta dessa dependência primária durante a execução do ecossistema, force a instalação manual por dentro da VENV:
```bash
cd /home/emerzoom/deploy/stable-diffusion-webui-forge/
source venv/bin/activate

# Instala a dependência em falta
pip install joblib

deactivate
```

#### 🟢 Limpeza profunda de Cache (Problemas persistentes)
Se o Forge continuar apresentando comportamentos estranhos em chamadas consecutivas da API, limpe os bancos de dados temporários e o cache de memória:
```bash
cd /home/emerzoom/deploy/stable-diffusion-webui-forge/
rm -rf cache/*
rm -rf cache/
rm -f cache.db cache.db-journal

# Verifique o estado final dos modelos carregados
ls -lh models/Stable-diffusion/
```

---

### 3.6 Problemas com o OpenAI CLIP

#### 🔍 Sintoma
Erros ou avisos no terminal que mencionam problemas no carregamento, tokenização ou ausência de módulos associados ao CLIP da OpenAI.

#### 🛠️ Resolução
Caso o ambiente do seu Forge reclame do CLIP, ative o ambiente virtual e execute a instalação forçada das dependências de processamento de texto e o repositório oficial do CLIP:

```bash
cd /home/emerzoom/deploy/stable-diffusion-webui-forge/
source venv/bin/activate

pip install ftfy regex tqdm
pip install git+https://github.com/openai/CLIP.git

deactivate
```
