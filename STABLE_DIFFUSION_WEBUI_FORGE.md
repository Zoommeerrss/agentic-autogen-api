# 🛠️ Troubleshooting: Stable Diffusion WebUI Forge (Linux)

Este guia consolida os erros mais comuns de ambiente, dependências e carregamento de modelos encontrados ao configurar o Forge para atuar como a API local de geração de imagens integrada ao ecossistema de agentes AutoGen.

---

## 📌 Índice de Erros Comuns
1. [Incompatibilidade de Versão do Python e falha no build do CLIP](#1-incompatibilidade-de-versão-do-python-e-falha-no-build-do-clip)
2. [Erro de tamanho de tipo do NumPy (`ValueError: numpy.dtype size changed`)](#2-erro-de-tamanho-de-tipo-do-numpy-valueerror-numpydtype-size-changed)
3. [Modelo Corrompido ou Vazio (`AssertionError: is not a safetensors file`)](#3-modelo-corrompido-ou-vazio-assertionerror-is-not-a-safetensors-file)
4. [A API externa não consegue conectar ao Forge (`ConnectionRefusedError`)](#4-a-api-externa-não-consegue-conectar-ao-forge-connectionrefusederror)

---

### 1. Incompatibilidade de Versão do Python e falha no build do CLIP

#### 🔍 Sintoma
O script de inicialização do Forge falha no meio do processo com mensagens de erro como `ModuleNotFoundError: No module named 'pkg_resources'` ou falha ao compilar rodas (*wheels*) de pacotes como `clip`, `scikit-image` ou `scipy` através do compilador C++ (`pythran`/`ninja`).

#### 💡 Causa Raiz
O Forge e o ecossistema de difusão clássico **não possuem suporte estável ao Python 3.12+**. Versões novas do Python removeram ferramentas de empacotamento antigas que bibliotecas de IA legadas exigem para compilar o código fonte nativo no Linux.

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
   rm -rf ~/deploy/stable-diffusion-webui-forge/venv
   ```
3. Recrie a sandbox travada na versão correta do Python:
   ```bash
   python3.10 -m venv ~/deploy/stable-diffusion-webui-forge/venv
   ```

---

### 2. Erro de tamanho de tipo do NumPy (`ValueError: numpy.dtype size changed`)

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
source ~/deploy/stable-diffusion-webui-forge/venv/bin/activate

# 2. Force a reinstalação travando na versão estável
pip install "numpy<2.0.0" --force-reinstall

# 3. Saia do ambiente virtual
deactivate
```
*(Nota: Avisos do pip sobre o pacote `opencv-contrib-python` preferir o NumPy 2.x podem ser ignorados com segurança; o Forge exige o NumPy 1.x para funcionar).*

---

### 3. Modelo Corrompido ou Vazio (`AssertionError: is not a safetensors file`)

#### 🔍 Sintoma
O Forge inicia, mas exibe erros repetidos de asserção apontando para o arquivo do modelo e exibe o hash calculado como **`e3b0c442`**:
```text
AssertionError: .../animagineXL.safetensors is not a safetensors file
```

#### 💡 Causa Raiz
O hash `e3b0c442` é o identificador SHA-256 universal para um **arquivo com 0 bytes de tamanho**. Isso ocorre porque o comando `wget` ou `curl` baixou apenas uma página HTML de redirecionamento ou de erro do Hugging Face, em vez do arquivo binário real de ~6.5 GB.

#### 🛠️ Resolução
Excluir o arquivo fantasma e refazer o download injetando os parâmetros de redirecionamento de CDN e download direto do Hugging Face:
```bash
# 1. Acesse o diretório correto de checkpoints
cd ~/deploy/stable-diffusion-webui-forge/models/Stable-diffusion/

# 2. Remova o arquivo de 0 bytes
rm animagineXL.safetensors

# 3. Baixe o modelo forçando o parâmetro de download direto (?download=true)
wget -O animagineXL.safetensors "https://huggingface.co"
```
*(Acompanhe o terminal para certificar-se de que o tamanho do arquivo baixado está progredindo em Gigabytes).*

---

### 4. A API externa não consegue conectar ao Forge (`ConnectionRefusedError`)

#### 🔍 Sintoma
O script Python dos agentes do AutoGen dispara erros do tipo `requests.exceptions.ConnectionError: HTTPConnectionPool... Connection refused`.

#### 💡 Causa Raiz
O Forge foi iniciado de forma isolada para navegação local por padrão, travando o acesso de chamadas externas de código ou scripts Python em outras portas de rede.

#### 🛠️ Resolução
Sempre inicializar o servidor injetando as flags **`--api`** (libera os endpoints JSON que os agentes consomem) e **`--listen`** (permite que o servidor ouça chamadas internas de rede):
```bash
cd ~/deploy/stable-diffusion-webui-forge
./webui.sh --api --listen --port 7860 --skip-python-version-check
```
