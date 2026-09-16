# 🚀 Instalação do LM Studio no Ubuntu 24.04 LTS (WSL)

Este guia prático documenta o passo a passo completo para instalar e executar o **LM Studio** dentro do ambiente **WSL (Windows Subsystem for Linux)** rodando **Ubuntu 24.04 (Noble Numbat)**, incluindo soluções para erros de dependências de interface gráfica e restrições de sandbox.

---

## 🛠️ Passo a Passo da Instalação

### 1. Atualizar o Sistema e Instalar o FUSE
O LM Studio é distribuído para Linux no formato AppImage, que requer a biblioteca `libfuse2` para ser montado no sistema.
```bash
sudo apt update && sudo apt install libfuse2 -y
```

### 2. Baixar o LM Studio
Crie ou acesse a sua pasta de Downloads e baixe a versão estável para Linux:
```bash
cd ~/Downloads
wget https://lmstudio.ai
```
*(Nota: Certifique-se de usar a URL da versão mais recente disponível no site oficial se necessário).*

### 3. Dar Permissão de Execução
```bash
chmod +x LM-Studio-*.AppImage
```

### 4. Extrair o AppImage (Correção de Sandbox)
O Ubuntu e o WSL possuem restrições estritas de segurança para o Sandbox do Chrome/Electron embutido no LM Studio. Para evitar falhas, extraia o conteúdo e ajuste as permissões do componente:
```bash
./LM-Studio-*.AppImage --appimage-extract
cd squashfs-root
sudo chown root chrome-sandbox && sudo chmod 4755 chrome-sandbox
```

---

## 🔍 Troubleshooting (Resolução de Problemas)

### Erro 1: `No such file or directory` ao tentar rodar `./lmstudio`
* **Causa:** O executável principal dentro da pasta extraída possui um hífen no nome (`lm-studio`) ou deve ser chamado pelo script padrão do AppImage.
* **Solução:** Utilize o nome correto do arquivo:
  ```bash
  ./lm-studio --no-sandbox
  ```
  *(Ou use `./AppRun --no-sandbox` se preferir o atalho unificado).*

### Erro 2: `error while loading shared libraries: libnss3.so`
* **Causa:** O WSL vem sem nenhuma biblioteca de interface gráfica (GUI) instalada por padrão.
* **Solução:** Instalar o ecossistema gráfico básico do Chromium/X11.

### Erro 3: `E: Package 'libasound2' has no installation candidate`
* **Causa:** No Ubuntu 24.04 (Noble Numbat), os pacotes de biblioteca de 64 bits foram renomeados com o sufixo `t64` devido à transição do ano 2038.
* **Solução (Comando definitivo de dependências para Ubuntu 24.04):**
  Instale todas as bibliotecas necessárias utilizando os nomes atualizados do sistema:
  ```bash
  sudo apt update && sudo apt install -y libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2t64
  ```

---

## 🚀 Como Inicializar Corretamente no WSL

Após instalar todas as dependências do Ubuntu 24.04, navegue até a pasta extraída e execute o aplicativo **desativando o sandbox nativo** (essencial para o funcionamento estável dentro do WSLg):

```bash
cd ~/Downloads/squashfs-root
./lm-studio --no-sandbox
```

---

## ⚡ Próximos Passos Recomendados

1. **Ativar o WSLg:** Certifique-se de que o seu Windows 11 está atualizado para que a interface gráfica do Linux (WSLg) renderize a tela do aplicativo automaticamente no seu desktop Windows.
2. **Configuração de GPU:** Por padrão, o LM Studio no WSL rodará modelos usando apenas o processador (CPU). Caso possua uma placa de vídeo dedicada (NVIDIA/AMD), instale os drivers de GPU adequados dentro do subsistema Linux para habilitar a aceleração por hardware (CUDA/ROCm).
