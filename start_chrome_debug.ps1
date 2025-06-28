# Script para iniciar Chrome com debugging para NotebookLM
# Use este script ANTES de executar a automacao do NotebookLM

Write-Host "Iniciando Chrome com debugging..." -ForegroundColor Green

# Fechar Chrome existente
Write-Host "Fechando instancias existentes do Chrome..." -ForegroundColor Yellow
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Verificar se Chrome esta instalado
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chromePath)) {
    Write-Host "ERRO: Chrome nao encontrado!" -ForegroundColor Red
    Write-Host "Instale o Google Chrome primeiro." -ForegroundColor White
    exit 1
}

# Criar diretorio de dados do usuario
if (-not (Test-Path "./chrome-user-data")) {
    New-Item -ItemType Directory -Path "./chrome-user-data" -Force | Out-Null
}

Write-Host "Iniciando Chrome..." -ForegroundColor Cyan

# Comando para iniciar Chrome
$chromeCommand = "`"$chromePath`" --remote-debugging-port=9222 --user-data-dir=./chrome-user-data --window-size=1280,800"

# Executar usando cmd para garantir compatibilidade
cmd /c "start `"Chrome Debug`" `"$chromePath`" --remote-debugging-port=9222 --user-data-dir=./chrome-user-data --window-size=1280,800"

# Aguardar e verificar
Write-Host "Aguardando Chrome inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verificar se funcionou
$attempts = 0
do {
    $portCheck = netstat -an | findstr "9222"
    if ($portCheck) {
        Write-Host "SUCESSO! Chrome rodando com debugging na porta 9222" -ForegroundColor Green
        Write-Host ""
        Write-Host "PROXIMOS PASSOS:" -ForegroundColor Cyan
        Write-Host "1. Faca login no Google (se necessario)" -ForegroundColor White
        Write-Host "2. Acesse https://notebooklm.google.com" -ForegroundColor White
        Write-Host "3. Execute: .\run_streamlit.ps1 -SkipChrome" -ForegroundColor White
        Write-Host ""
        break
    }
    Start-Sleep -Seconds 1
    $attempts++
} while ($attempts -lt 10)

if ($attempts -eq 10) {
    Write-Host "Chrome iniciado, mas debugging pode nao estar ativo" -ForegroundColor Yellow
    Write-Host "Tente executar manualmente este comando:" -ForegroundColor White
    Write-Host "$chromeCommand" -ForegroundColor Gray
} 