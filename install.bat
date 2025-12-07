@echo off
echo ========================================
echo   Installation du Bot Dofus
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    echo IMPORTANT : Cocher "Add Python to PATH" lors de l'installation
    pause
    exit /b 1
)

echo [OK] Python detecte
python --version
echo.

REM Mettre à jour pip
echo [1/3] Mise a jour de pip...
python -m pip install --upgrade pip
echo.

REM Installer les dépendances
echo [2/3] Installation des dependances...
echo Cela peut prendre quelques minutes...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERREUR] Erreur lors de l'installation des dependances
    pause
    exit /b 1
)
echo.

REM Vérifier l'installation
echo [3/3] Verification de l'installation...
python -c "import cv2; import numpy; import pyautogui; import PIL; import ultralytics; import customtkinter; import yaml; print('✅ Tous les packages sont installes !')"
if errorlevel 1 (
    echo.
    echo [ERREUR] Certains packages ne sont pas correctement installes
    pause
    exit /b 1
)
echo.

echo ========================================
echo   Installation terminee avec succes !
echo ========================================
echo.
echo Tu peux maintenant lancer le bot avec :
echo   python gui.py
echo.
echo Ou double-cliquer sur Lancer_Bot.bat
echo.
pause

