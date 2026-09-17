# 📑 Guia Completo de Instalação e Troubleshooting: Stable Diffusion WebUI Forge (Linux)

Este guia consolida os procedimentos de instalação local e as resoluções para os erros mais comuns de ambiente, dependências e carregamento de modelos encontrados ao configurar o Forge para atuar como a API local de geração de imagens integrada ao ecossistema de agentes AutoGen e ao LM Studio.

O Forge foi escolhido por consumir muito menos VRAM (memória da placa de vídeo) e ser ideal para rodar em paralelo com seus agentes.

---

## 📌 Índice Geral
1. [📋 Pré-requisitos do Sistema](#-pré-requisitos-do-sistema)
2. [🛠️ Passo 1: Clonar o Repositório do Forge](#️-passo-1-clonar-o-repositório-do-forge)
3. [🚀 Passo 2: Inicialização e Ativação da API](#-passo-2-inicialização-e-ativação-da-api)
4. [🛑 3. Resolução de Problemas (Troubleshooting)](#-3-resolução-de-problemas-troubleshooting)
   - [3.1 Erro de Permissão Negada ou Arquivo Não Encontrado (`Permission Denied` / `cannot execute`)](#31-erro-de-permissão-negada-ou-arquivo-não-encontrado-permission-denied--cannot-execute)
   - [3.2 Falha ao Compilar Dependências C++ (`scikit-image`, `Pillow`, `Unknown Compiler`)](#32-falha-ao-compilar-dependências-c-scikit-image-pillow-unknown-compiler)
   - [3.3 Erro de tamanho de tipo do NumPy (`ValueError: numpy.dtype size changed`)](#33-erro-de-tamanho-de-tipo-do-numpy-valueerror-numpydtype-size-changed)
   - [3.4 Modelo Incompleto, Corrompido ou Erros de Download com wget (`AssertionError`)](#34-modelo-incompleto-corrompido-ou-erros-de-download-com-wget-assertionerror)
   - [3.5 A API externa não consegue conectar ao Forge (`ConnectionRefusedError`)](#35-a-api-externa-não-consegue-conectar-ao-forge-connectionrefusederror)

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
./webui-user.sh --api --listen --port 7860
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

### 3.1 Erro de Permissão Negada ou Arquivo Não Encontrado (`Permission Denied` / `cannot execute`)

#### 🔍 Sintoma
Ao tentar rodar `./webui-user.sh`, o terminal retorna `-bash: ./webui-user.sh: Permission denied` ou `-bash: ./webui-user.sh: cannot execute: required file not found`.

#### 💡 Causa Raiz
1. O script clonado veio sem permissão de execução no sistema de arquivos do Linux.
2. O arquivo possui quebras de linha ocultas no formato do Windows (CRLF) em vez do formato Linux (LF), o que quebra a leitura do interpretador Bash.

#### 🛠️ Resolução
Conceda a permissão correta e converta o arquivo para o formato Linux usando o utilitário `dos2unix`:

```bash
# 1. Instale o conversor de formatos
sudo apt update && sudo apt install -y dos2unix

# 2. Conceda permissão de execução aos scripts principais
chmod +x webui-user.sh webui.sh

# 3. Remova a formatação oculta do Windows
dos2unix webui-user.sh webui.sh
```

---

### 3.2 Falha ao Compilar Dependências C++ (`scikit-image`, `Pillow`, `Unknown Compiler`)

#### 🔍 Sintoma
Durante a instalação automatizada, o pip trava ao coletar `scikit-image` ou `Pillow` exibindo erros como `ERROR: Unknown compiler(s)`, `Python dependency not found` ou falhas brutas de sintaxe geradas pelo Cython/Meson.

#### 💡 Causa Raiz
No **Python 3.12** (padrão de distribuições mais recentes como o Ubuntu 24.04), pacotes de IA legados cujas versões estão "travadas" no repositório tentam compilar código-fonte C++ nativo do zero. O processo falha se o sistema não possuir os compiladores adequados ou bibliotecas de imagem (`libjpeg`, `zlib`) e se as sintaxes do código forem incompatíveis com as novas versões de compilação.

#### 🛠️ Resolução
Instale a árvore de compiladores do Linux, as dependências de desenvolvimento do Python/Imagens e force o uso de versões modernas e pré-compiladas (Wheels) compatíveis com o Python 3.12:

```bash
# 1. Instale compiladores, pacotes de desenvolvimento do Python e bibliotecas de imagem
sudo apt update && sudo apt install -y build-essential python3-dev pkg-config libjpeg-dev zlib1g-dev libtiff5-dev libfreetype6-dev libwebp-dev libopenjp2-7-dev libgif-dev

# 2. Ative o ambiente virtual do Forge manualmente
source venv/bin/activate

# 3. Atualize as ferramentas base do pip e instale versões estáveis pré-compiladas
pip install --upgrade pip setuptools wheel
pip install scikit-image==0.22.0
pip install --upgrade Pillow

# 4. Ajuste o arquivo de requerimentos para evitar que o Forge tente reinstalar as versões antigas quebradas
# Altere as linhas de "==" para ">=" usando o seu editor (ex: nano requirements_versions.txt)
# Modifique para: scikit-image>=0.21.0  e  Pillow>=9.5.0

# 5. Saia do ambiente virtual
deactivate
```

---

### 3.3 Erro de tamanho de tipo do NumPy (`ValueError: numpy.dtype size changed`)

#### 🔍 Sintoma
O terminal exibe o erro fatal durante a inicialização:
```text
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject
```

#### 💡 Causa Raiz
O instalador automatizado baixou o moderno **NumPy v2.x**, mas as extensões gráficas internas do Forge (como `scikit-image` e o gerenciador do `ControlNet`) dependem da estrutura binária clássica da ramificação **NumPy 1.x**. O choque de versões causa corrupção de memória em runtime.

#### 🛠️ Resolução
Faça o downgrade forçado do pacote matemático dentro do ambiente virtual para travar na árvore anterior:

```bash
# 1. Ative o ambiente virtual interno do Forge
source venv/bin/activate

# 2. Force a reinstalação travando na versão estável anterior
pip install "numpy<2.0.0" --force-reinstall

# 3. Caso necessário, force a reinstalação do scikit-image para realinhamento binário
pip install --force-reinstall scikit-image

# 4. Saia do ambiente virtual
deactivate
```
*(Nota: Avisos secundários do pip sobre o pacote `opencv-contrib-python` preferir o NumPy 2.x podem ser ignorados com segurança; o Forge exige o NumPy 1.x para funcionar).*

---

### 3.4 Modelo Incompleto, Corrompido ou Erros de Download com wget (`AssertionError`)

#### 🔍 Sintoma
O Forge inicia, mas exibe erros repetidos de asserção apontando para o arquivo do modelo ou o download via `wget`/`curl` falha repetidamente, gera arquivos corrompidos de poucos kilobytes ou apresenta erro de travamento. O console do Forge acusa: `You do not have any model!`.

#### 💡 Causa Raiz
Servidores do Hugging Face utilizam múltiplos redirecionamentos de CDN que frequentemente quebram utilitários de download direto como o `wget` quando manipulando arquivos binários massivos (como pesos de ~6.5 GB). Além disso, baixar atualizações manuais do CLI (`pip install -U`) fora de uma versão fixa gera quebra de dependências com o `transformers` e o `tokenizers`.

#### 🛠️ Resolução
A forma mais robusta de baixar modelos grandes no Ubuntu sem corrupção é utilizando o gerenciador oficial da API deles (`huggingface-cli`) cravado na versão compatível com o Forge.

```bash
# 1. Entre no diretório do projeto e ative o ambiente virtual
cd /home/emerzoom/deploy/stable-diffusion-webui-forge/
source venv/bin/activate

# 2. Garanta a instalação da versão estável do SDK (Evita conflitos de tokenizers/transformers)
pip install "huggingface_hub==0.26.2" --force-reinstall

# 3. Baixe o arquivo .safetensors injetando-o diretamente na pasta final (Desativando Links Simbólicos)
huggingface-cli download cagliostrolab/animagine-xl-3.1 animagine-xl-3.1.safetensors --local-dir /home/wsl/stable-diffusion-webui-forge/models/Stable-diffusion/ --local-dir-use-symlinks False

# 4. Desative a VENV após o download atingir 100%
deactivate
```

---

### 3.5 A API externa não consegue conectar ao Forge (`ConnectionRefusedError`)

#### 🔍 Sintoma
O script Python dos agentes do AutoGen dispara erros do tipo `requests.exceptions.ConnectionError: HTTPConnectionPool... Connection refused`.

#### 💡 Causa Raiz
O Forge foi iniciado de forma isolada para navegação local por padrão, travando o acesso de chamadas externas de código ou scripts Python em outras portas de rede.

#### 🛠️ Resolução
Sempre inicialize o servidor injetando as flags **`--api`** (libera os endpoints JSON que os agentes consomem) e **`--listen`** (permite que o servidor ouça chamadas internas de rede). 

Para placas de vídeo com menos de 8GB de VRAM, recomenda-se adicionar a flag --medvram para otimização de memória:

```bash
./webui-user.sh --api --listen --port 7860 --medvram
```

