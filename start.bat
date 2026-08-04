@echo off
chcp 65001 > nul
echo ==================================================
echo 🚀 Запуск «Карта Подій Світловодськ» (Cloudflare HTTPS)
echo ==================================================
echo.

start "Cloudflare Tunnel" .\cloudflared.exe tunnel --url http://localhost:8080
python run.py

pause
