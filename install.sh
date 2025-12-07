#!/bin/bash

echo "========================================"
echo "  Installation du Bot Dofus"
echo "========================================"
echo ""

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python3 n'est pas installé"
    echo ""
    echo "Installez Python3 avec :"
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-pip"
    exit 1
fi

echo "[OK] Python détecté"
python3 --version
echo ""

# Installer tkinter si nécessaire (Linux)
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "[INFO] Installation de python3-tk..."
    sudo apt install -y python3-tk
fi

# Mettre à jour pip
echo "[1/3] Mise à jour de pip..."
python3 -m pip install --upgrade pip --user
echo ""

# Installer les dépendances
echo "[2/3] Installation des dépendances..."
echo "Cela peut prendre quelques minutes..."
python3 -m pip install --user -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERREUR] Erreur lors de l'installation des dépendances"
    exit 1
fi
echo ""

# Vérifier l'installation
echo "[3/3] Vérification de l'installation..."
python3 -c "import cv2; import numpy; import pyautogui; import PIL; import ultralytics; import customtkinter; import yaml; print('✅ Tous les packages sont installés !')"
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERREUR] Certains packages ne sont pas correctement installés"
    exit 1
fi
echo ""

echo "========================================"
echo "  Installation terminée avec succès !"
echo "========================================"
echo ""
echo "Tu peux maintenant lancer le bot avec :"
echo "  python3 gui.py"
echo ""

