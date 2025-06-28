# 🔧 Solução para Erro de CDP (Chrome DevTools Protocol)

## ❌ Problema
Erro: "Connecting to Chrome on CDP port: 9222..." - Chrome não está rodando com debugging

## ✅ Solução Completa

### **Método 1: Manual (Mais Confiável)**

1. **Feche TODAS as instâncias do Chrome:**
   - Feche todas as janelas do Chrome
   - Abra o Gerenciador de Tarefas (Ctrl+Shift+Esc)
   - Procure por processos "Google Chrome" e finalize todos

2. **Abra o Prompt de Comando como Administrador:**
   - Pressione Win+R
   - Digite: `cmd`
   - Pressione Ctrl+Shift+Enter (para abrir como admin)

3. **Execute este comando no CMD:**
   ```cmd
   cd /d "C:\dev\workspace_mygithub\notebooklm-podcast-automator"
   
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\dev\workspace_mygithub\notebooklm-podcast-automator\chrome-user-data --window-size=1280,800
   ```

4. **Verifique se funcionou:**
   - O Chrome deve abrir
   - Abra outro terminal PowerShell
   - Execute: `netstat -an | findstr 9222`
   - Deve mostrar: `TCP 0.0.0.0:9222 0.0.0.0:0 LISTENING`

### **Método 2: Script PowerShell (Alternativo)**

Se o método 1 não funcionar, tente:

```powershell
# 1. Feche todas as instâncias do Chrome
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Aguarde 3 segundos
Start-Sleep -Seconds 3

# 3. Inicie Chrome com debugging
cmd /c 'start "Chrome Debug" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\dev\workspace_mygithub\notebooklm-podcast-automator\chrome-user-data --window-size=1280,800'

# 4. Aguarde 5 segundos
Start-Sleep -Seconds 5

# 5. Verifique se funcionou
netstat -an | findstr 9222
```

### **Método 3: Porta Alternativa**

Se a porta 9222 não funcionar, tente outras portas:

```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --user-data-dir=C:\dev\workspace_mygithub\notebooklm-podcast-automator\chrome-user-data --window-size=1280,800
```

E no Streamlit, configure a porta 9223 na interface.

## 🚀 Após Chrome Iniciar com Debugging

1. **Faça login no Google** (se necessário)
2. **Acesse:** https://notebooklm.google.com
3. **Execute o Streamlit:**
   ```powershell
   .\run_streamlit.ps1 -SkipChrome
   ```
4. **Na interface Streamlit:**
   - Configure CDP Port: 9222 (ou a porta que funcionou)
   - Cole suas URLs
   - Clique em "Run Automation"

## 🔍 Verificações de Troubleshooting

### Verificar se Chrome está com debugging:
```powershell
netstat -an | findstr 9222
# Deve mostrar: TCP 0.0.0.0:9222 0.0.0.0:0 LISTENING
```

### Verificar processos do Chrome:
```powershell
Get-Process chrome | Select-Object Name, Id, CommandLine
```

### Testar conexão CDP:
```powershell
Invoke-WebRequest -Uri "http://localhost:9222/json" -UseBasicParsing
# Deve retornar JSON com informações das abas
```

## ⚠️ Possíveis Problemas

1. **Firewall/Antivírus:** Pode bloquear a porta 9222
2. **Chrome já aberto:** Feche todas as instâncias primeiro
3. **Permissões:** Execute como administrador
4. **Porta ocupada:** Tente outra porta (9223, 9224, etc.)

## 💡 Dica Final

Se nada funcionar, use este comando direto no CMD como Admin:

```cmd
taskkill /im chrome.exe /f
timeout 3
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\dev\workspace_mygithub\notebooklm-podcast-automator\chrome-user-data --window-size=1280,800
```

Isso força o fechamento e reabertura do Chrome com debugging. 