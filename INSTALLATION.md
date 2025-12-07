# 📦 Guide d'Installation - Machine Virtuelle

Guide complet pour installer le bot Dofus sur une machine virtuelle.

## 🔧 Prérequis

- **Python 3.8 ou supérieur** (recommandé : Python 3.10 ou 3.11)
- **Windows 10/11** (ou Linux avec interface graphique)
- **Git** (pour cloner le repository)

---

## 📥 Étape 1 : Cloner le Repository

```bash
git clone https://github.com/Torkor29/DOFUS.git
cd DOFUS
```

---

## 🐍 Étape 2 : Installer Python (si pas déjà installé)

### Sur Windows :
1. Télécharger Python depuis [python.org](https://www.python.org/downloads/)
2. **IMPORTANT** : Cocher "Add Python to PATH" lors de l'installation
3. Vérifier l'installation :
```bash
python --version
```

### Sur Linux :
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

## 📦 Étape 3 : Installer les Dépendances

### Option 1 : Installation directe (recommandé)

```bash
pip install -r requirements.txt
```

### Option 2 : Installation avec environnement virtuel (recommandé pour éviter les conflits)

**Sur Windows :**
```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

**Sur Linux :**
```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## 📋 Liste des Packages Installés

Le fichier `requirements.txt` installe automatiquement :

- **opencv-python** (≥4.8.0) : Traitement d'images et vision par ordinateur
- **numpy** (≥1.24.0) : Calculs numériques
- **pyautogui** (≥0.9.54) : Automatisation de la souris/clavier
- **pillow** (≥10.0.0) : Manipulation d'images
- **ultralytics** (≥8.0.0) : Framework YOLO pour l'IA (détection d'objets)
- **customtkinter** (≥5.2.0) : Interface graphique moderne
- **pyyaml** (≥6.0) : Lecture/écriture de fichiers YAML

---

## ✅ Étape 4 : Vérifier l'Installation

Vérifier que tous les packages sont bien installés :

```bash
python -c "import cv2; import numpy; import pyautogui; import PIL; import ultralytics; import customtkinter; import yaml; print('✅ Tous les packages sont installés !')"
```

Si tu vois "✅ Tous les packages sont installés !", c'est bon !

---

## 🚀 Étape 5 : Lancer le Bot

### Sur Windows :
```bash
python gui.py
```

Ou double-cliquer sur `Lancer_Bot.bat`

### Sur Linux :
```bash
python3 gui.py
```

---

## ⚠️ Problèmes Courants

### Erreur "pip n'est pas reconnu"

**Solution :**
- Réinstaller Python en cochant "Add Python to PATH"
- Ou utiliser `python -m pip` au lieu de `pip`

### Erreur lors de l'installation d'ultralytics

**Solution :**
```bash
pip install --upgrade pip
pip install ultralytics
```

### Erreur avec opencv-python

**Solution :**
```bash
pip uninstall opencv-python
pip install opencv-python
```

### Erreur "No module named 'tkinter'" (Linux)

**Solution :**
```bash
sudo apt install python3-tk
```

### Erreur avec customtkinter (affichage)

**Solution :**
```bash
pip install --upgrade customtkinter
```

---

## 📝 Notes Importantes

1. **Premier lancement** : Le modèle YOLO de base (`yolov8n.pt`) sera téléchargé automatiquement (~6 MB)
2. **Temps d'installation** : Comptez 5-10 minutes selon votre connexion internet
3. **Espace disque** : Environ 500 MB pour tous les packages + modèles
4. **Résolution d'écran** : Le bot fonctionne mieux avec une résolution fixe (éviter de redimensionner la fenêtre)

---

## 🔄 Mise à Jour des Packages

Pour mettre à jour tous les packages :

```bash
pip install --upgrade -r requirements.txt
```

---

## 🗑️ Désinstallation

Si tu veux désinstaller tous les packages :

```bash
pip uninstall -r requirements.txt -y
```

---

## 💡 Astuce : Environnement Virtuel

**Pourquoi utiliser un environnement virtuel ?**
- Évite les conflits avec d'autres projets Python
- Permet d'avoir des versions spécifiques de packages
- Facilite la gestion des dépendances

**Pour désactiver l'environnement virtuel :**
```bash
deactivate
```

---

## ✅ Checklist d'Installation

- [ ] Python 3.8+ installé
- [ ] Repository cloné
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Vérification réussie (commande de test)
- [ ] Bot lancé avec succès (`python gui.py`)

---

**Besoin d'aide ?** Ouvre une issue sur GitHub : https://github.com/Torkor29/DOFUS/issues

