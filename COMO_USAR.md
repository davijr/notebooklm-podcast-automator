# 🎙️ NotebookLM Podcast Automator - Guia de Uso

## 🚀 Execução Rápida

### Usando o Script PowerShell (Recomendado):

```powershell
# Interface completa (NotebookLM + Spotify)
.\run_streamlit.ps1

# Apenas NotebookLM
.\run_streamlit.ps1 -Interface notebooklm

# Apenas Spotify
.\run_streamlit.ps1 -Interface spotify

# Em porta personalizada
.\run_streamlit.ps1 -Port 8505
```

### Usando comandos diretos:

```powershell
# Interface unificada
$env:PYTHONPATH = "src"; python -m uv run streamlit run src/notebooklm_automator/streamlit_app.py

# Apenas NotebookLM
$env:PYTHONPATH = "src"; python -m uv run streamlit run src/notebooklm_automator/notebooklm_streamlit_app.py

# Apenas Spotify
$env:PYTHONPATH = "src"; python -m uv run streamlit run src/notebooklm_automator/spotify_streamlit_app.py
```

## ⚠️ Pré-requisitos para NotebookLM

### Opção 1: Chromium do Playwright (RECOMENDADO) 🆕

A **nova opção** mais fácil e confiável:
- ✅ Marque **"Use Playwright Chromium"** na interface
- ✅ Não precisa configurar Chrome manualmente
- ✅ Funciona automaticamente!

### Opção 2: Chrome com Debugging (Método Original)

Se preferir usar o Chrome instalado no sistema:

```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=./chrome-user-data --window-size=1280,800
```

## 🌐 Interfaces Disponíveis

- **http://localhost:8501** - Interface unificada (padrão)
- **http://localhost:8502** - Se a porta 8501 estiver ocupada
- **http://localhost:8503** - NotebookLM apenas
- **http://localhost:8504** - Spotify apenas

## 📋 Como Usar

1. **Prepare o ambiente:**
   - Execute o Chrome com debugging (para NotebookLM)
   - Execute uma das interfaces acima

2. **Na interface web:**
   - Cole URLs de websites ou YouTube
   - Configure opções (porta CDP, Jina Reader, etc.)
   - Clique em "Processar URLs"
   - Acompanhe o progresso em tempo real

3. **Para Spotify:**
   - Faça login na sua conta Spotify for Podcasters
   - Configure metadados do podcast
   - Faça upload do áudio gerado pelo NotebookLM

## 🔧 Solução de Problemas

- **ModuleNotFoundError:** Certifique-se de estar usando `$env:PYTHONPATH = "src"`
- **Erro CDP "Connecting to Chrome on CDP port: 9222":** Veja o arquivo `SOLUCAO_CDP.md` para instruções detalhadas
- **Chrome connection failed:** Verifique se o Chrome está rodando com `--remote-debugging-port=9222`
- **Porta ocupada:** Use uma porta diferente com `--server.port XXXX`

## 📚 Documentação Completa

Veja: https://github.com/davijr/notebooklm-podcast-automator 