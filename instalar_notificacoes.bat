@echo off
echo ========================================
echo Instalacao do Sistema de Notificacoes
echo ========================================
echo.

echo [1/3] Instalando dependencias...
pip install -r requirements_notifications.txt

echo.
echo [2/3] Criando diretorios de configuracao...
if not exist "config" mkdir config

echo.
echo [3/3] Configuracao concluida!
echo.
echo ========================================
echo Proximos Passos:
echo ========================================
echo 1. Configure as credenciais do Google Cloud Console
echo 2. Adicione variaveis de ambiente (.env):
echo    - GOOGLE_CLIENT_ID
echo    - GOOGLE_CLIENT_SECRET
echo    - SMTP_HOST, SMTP_USER, SMTP_PASSWORD
echo 3. Acesse o sistema e va em Agenda ^> Configuracoes
echo 4. Configure e-mails e autorize Google Calendar
echo 5. Execute: python notification_scheduler.py start
echo.
echo Documentacao completa: DOCS_GOOGLE_CALENDAR_NOTIFICACOES.md
echo ========================================
echo.
pause
