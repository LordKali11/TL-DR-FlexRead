@echo off
title NZZ Flex Read Server
echo Starting Neue Zurcher Zeitung Web App...
cd /d "%~dp0"
python serve.py
pause
