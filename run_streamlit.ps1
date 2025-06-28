# NotebookLM Podcast Automator - Scripts de Execução
# Baseado na documentação: https://github.com/davijr/notebooklm-podcast-automator

param(
    [ValidateSet("unified", "notebooklm", "spotify")]
    [string]$Interface = "unified",
    [int]$Port = 8501,
    [switch]$SkipChrome = $false
)

function Start-ChromeWithDebug {
    Write-Host "🔧 Verificando Chrome..." -ForegroundColor Cyan
    
    # Verificar se Chrome já está rodando com debugging
    $chromeWithDebug = netstat -an | findstr "9222"
    if ($chromeWithDebug) {
        Write-Host "✅ Chrome já está rodando com debugging na porta 9222" -ForegroundColor Green
        return
    }
    
    # Fechar instâncias existentes do Chrome
    $chromeProcesses = Get-Process chrome -ErrorAction SilentlyContinue
    if ($chromeProcesses) {
        Write-Host "⏹️  Fechando instâncias existentes do Chrome..." -ForegroundColor Yellow
        $chromeProcesses | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    
    # Verificar se Chrome está instalado
    $chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
    if (-not (Test-Path $chromePath)) {
        Write-Host "❌ Chrome não encontrado em: $chromePath" -ForegroundColor Red
        Write-Host "   Por favor, instale o Google Chrome ou ajuste o caminho no script." -ForegroundColor White
        return
    }
    
    # Iniciar Chrome com debugging
    Write-Host "🚀 Iniciando Chrome com debugging..." -ForegroundColor Green
    $chromeArgs = @(
        "--remote-debugging-port=9222",
        "--user-data-dir=./chrome-user-data",
        "--window-size=1280,800",
        "--no-first-run",
        "--no-default-browser-check"
    )
    
    # Criar diretório para dados do usuário se não existir
    if (-not (Test-Path "./chrome-user-data")) {
        New-Item -ItemType Directory -Path "./chrome-user-data" -Force | Out-Null
    }
    
    try {
        $process = Start-Process -FilePath $chromePath -ArgumentList $chromeArgs -PassThru
        Start-Sleep -Seconds 3
        
        # Verificar se a porta está ativa
        $attempts = 0
        do {
            $portActive = netstat -an | findstr "9222"
            if ($portActive) {
                Write-Host "✅ Chrome iniciado com debugging na porta 9222!" -ForegroundColor Green
                Write-Host "🌐 Agora faça login no Google e acesse NotebookLM se necessário" -ForegroundColor Cyan
                return
            }
            Start-Sleep -Seconds 1
            $attempts++
        } while ($attempts -lt 10)
        
        Write-Host "⚠️  Chrome iniciado, mas debugging pode não estar ativo" -ForegroundColor Yellow
        Write-Host "   Se tiver problemas, tente executar manualmente:" -ForegroundColor White
        Write-Host "   `"$chromePath`" --remote-debugging-port=9222 --user-data-dir=./chrome-user-data" -ForegroundColor Gray
        
    } catch {
        Write-Host "❌ Erro ao iniciar Chrome: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Tente executar manualmente:" -ForegroundColor White
        Write-Host "   `"$chromePath`" --remote-debugging-port=9222 --user-data-dir=./chrome-user-data" -ForegroundColor Gray
    }
}

Write-Host "🚀 Iniciando NotebookLM Podcast Automator..." -ForegroundColor Green

# Iniciar Chrome com debugging se necessário
if (-not $SkipChrome -and ($Interface -eq "unified" -or $Interface -eq "notebooklm")) {
    Start-ChromeWithDebug
    Write-Host ""
}

# Configurar PYTHONPATH
$env:PYTHONPATH = "src"

# Definir qual interface executar
switch ($Interface) {
    "unified" {
        Write-Host "📱 Interface Unificada (NotebookLM + Spotify)" -ForegroundColor Yellow
        $AppFile = "src/notebooklm_automator/streamlit_app.py"
        break
    }
    "notebooklm" {
        Write-Host "🎙️ Interface NotebookLM" -ForegroundColor Blue
        $AppFile = "src/notebooklm_automator/notebooklm_streamlit_app.py"
        break
    }
    "spotify" {
        Write-Host "🎵 Interface Spotify" -ForegroundColor Magenta
        $AppFile = "src/notebooklm_automator/spotify_streamlit_app.py"
        break
    }
}

Write-Host "🌐 A interface será aberta em: http://localhost:$Port" -ForegroundColor Cyan

if (-not $SkipChrome -and ($Interface -eq "unified" -or $Interface -eq "notebooklm")) {
    Write-Host ""
    Write-Host "💡 DICA: Na primeira execução, faça login no Google no Chrome que foi aberto" -ForegroundColor Green
    Write-Host "   automaticamente para acessar o NotebookLM." -ForegroundColor White
}

Write-Host ""

# Executar o Streamlit
python -m uv run streamlit run $AppFile --server.port $Port 