# 🤖 Dofus Fishing Bot AI - Manager Pro

Bot intelligent pour Dofus Rétro avec interface graphique complète, navigation automatique, pêche assistée par IA, gestion de combat, et système d'entraînement YOLO personnalisé.

## 📋 Table des matières

- [Fonctionnalités principales](#-fonctionnalités-principales)
- [Installation](#-installation)
- [Configuration initiale](#-configuration-initiale)
- [Guide d'utilisation](#-guide-dutilisation)
- [Système d'annotation et entraînement IA](#-système-dannotation-et-entraînement-ia)
- [Architecture technique](#-architecture-technique)
- [Structure des fichiers](#-structure-des-fichiers)
- [Dépannage](#-dépannage)

---

## 🚀 Fonctionnalités principales

### 1. **Navigation automatique intelligente**
- Navigation automatique entre les maps selon une route définie
- Détection automatique des sorties (haut, bas, gauche, droite)
- Support de boucles infinies
- Sauvegarde et reprise de l'état du circuit
- Équipement automatique de la dragodinde au démarrage

### 2. **Pêche assistée par IA (YOLO)**
- Détection automatique des poissons avec modèle YOLO entraîné
- Clic automatique sur les spots de pêche détectés
- Gestion intelligente des temps d'attente
- Support de plusieurs types de poissons (mer, rivière)
- Collecte automatique de données pour améliorer le modèle

### 3. **Gestion de combat automatique**
- Détection automatique du début de combat
- Gestion des tours de combat
- Lancer de sorts configurable
- Détection de la position du personnage en combat
- Gestion des PA/PM
- Fermeture automatique du combat terminé

### 4. **Interface graphique complète (CustomTkinter)**
- **Tableau de bord** : Contrôle du bot, console en temps réel
- **Circuits & Routes** : Gestion de circuits personnalisés avec profils d'écran
- **Profils d'écran** : Gestion de plusieurs configurations d'écran
- **Calibrage manuel** : Outils pour calibrer les points de navigation, pêche, combat
- **Données & Map** : Visualisation et gestion des données de calibrage
- **Template Perso** : Collecte de données pour entraîner le modèle de détection du personnage
- **Annotateur Personnage** : Outil intégré d'annotation d'images pour YOLO
- **Entraînement IA** : Lancement de l'entraînement des modèles YOLO

### 5. **Système d'annotation et entraînement IA**
- **Collecte automatique** : Capture d'images du personnage toutes les 2 secondes
- **Annotateur intégré** : Interface graphique pour dessiner des bounding boxes
- **Préparation automatique** : Séparation train/validation (80/20)
- **Entraînement YOLO** : Entraînement de modèles personnalisés pour détecter le personnage
- **Gestion des datasets** : Organisation automatique des images et annotations

### 6. **Système de calibrage avancé**
- Calibrage des sorties de map (haut, bas, gauche, droite)
- Calibrage des spots de pêche par map
- Calibrage des points de combat
- Templates du personnage sous différents angles
- Support de plusieurs profils d'écran

---

## 📦 Installation

### Prérequis

- Python 3.8 ou supérieur
- Windows 10/11 (testé sur Windows)
- Dofus Rétro installé et configuré

### Étapes d'installation

1. **Cloner le repository**
```bash
git clone https://github.com/Torkor29/DOFUS.git
cd DOFUS
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

**Dépendances principales :**
- `opencv-python` : Traitement d'images et vision par ordinateur
- `numpy` : Calculs numériques
- `pyautogui` : Automatisation de la souris/clavier
- `pillow` : Manipulation d'images
- `ultralytics` : Framework YOLO pour l'IA
- `customtkinter` : Interface graphique moderne

3. **Télécharger les modèles YOLO de base**
   - Le modèle `yolov8n.pt` sera téléchargé automatiquement au premier lancement
   - Ou téléchargez-le manuellement depuis [Ultralytics](https://github.com/ultralytics/ultralytics)

4. **Lancer l'interface**
```bash
python gui.py
```

---

## ⚙️ Configuration initiale

### 1. Premier calibrage

Avant de pouvoir utiliser le bot, vous devez calibrer votre écran :

1. Ouvrez l'interface graphique
2. Allez dans **"Calibrage Manuel"**
3. Sélectionnez votre **Profil d'écran** (ou créez-en un nouveau)
4. Calibrez les éléments suivants dans l'ordre :

#### a) Navigation (Déplacement)
- Sélectionnez **"Déplacement (Map)"**
- Entrez les coordonnées de la map (ex: `12,4`)
- Choisissez la direction (DROITE, GAUCHE, HAUT, BAS)
- Cliquez sur **"DÉMARRER CALIBRAGE"**
- Placez votre souris sur le bouton de sortie dans le jeu
- Répétez pour toutes les sorties que vous utiliserez

#### b) Pêche (Spots)
- Sélectionnez **"Poissons (Spots)"**
- Entrez les coordonnées de la map
- Cliquez sur **"DÉMARRER CALIBRAGE"**
- Placez votre souris sur chaque spot de pêche
- Répétez pour toutes les maps de pêche

#### c) Combat
- Sélectionnez **"Cible Combat"** pour la position de la cible
- Sélectionnez **"Position Sort"** pour le bouton de sort
- Sélectionnez **"Zone PA"** et **"Zone PM"** si nécessaire
- Calibrez chaque élément

#### d) Templates Personnage
- Sélectionnez les différents angles (Face, Dos, Côtés, Diagonales)
- Placez votre souris sur le personnage dans le jeu
- Les templates seront sauvegardés dans `templates/`

### 2. Créer un circuit

1. Allez dans **"Circuits & Routes"**
2. Configurez :
   - **Position de départ** (X, Y)
   - **Route** : Liste des maps séparées par `;` (ex: `12,4; 11,4; 10,4`)
   - **Temps d'attente après pêche** (secondes)
   - **Pause changement de map** (secondes)
   - **Nombre de lancers de sort par tour** (combat)
   - **Boucle infinie** (oui/non)
3. Cliquez sur **"Nouveau..."** pour sauvegarder le circuit
4. Sélectionnez votre **Profil d'écran** associé

---

## 📖 Guide d'utilisation

### Lancer le bot

1. **Ouvrir l'interface**
   ```bash
   python gui.py
   ```

2. **Configurer un circuit**
   - Allez dans **"Circuits & Routes"**
   - Chargez ou créez un circuit
   - Vérifiez que le profil d'écran est correct

3. **Lancer le bot**
   - Allez dans **"Tableau de Bord"**
   - Cliquez sur **"▶ LANCER LE BOT"**
   - Basculez sur la fenêtre de Dofus dans les 3 secondes

4. **Arrêter le bot**
   - Cliquez sur **"⏹ ARRÊTER"** dans l'interface
   - Ou utilisez le raccourci clavier (si configuré)

### Reprendre un circuit

Si le bot s'arrête, vous pouvez reprendre depuis la dernière position :

1. Cliquez sur **"🔄 REPRENDRE CIRCUIT"**
2. Le bot reprendra depuis la dernière map visitée

### Gérer les circuits

- **Charger** : Charge un circuit existant dans l'éditeur
- **Nouveau** : Crée un nouveau circuit avec la configuration actuelle
- **Mettre à jour** : Met à jour le circuit sélectionné
- **Renommer** : Renomme le circuit sans perdre sa configuration
- **Supprimer** : Supprime un circuit (avec confirmation)

---

## 🎯 Système d'annotation et entraînement IA

### Workflow complet pour entraîner un modèle de détection du personnage

#### Étape 1 : Collecte de données

1. Allez dans **"Template Perso"**
2. Positionnez-vous en combat ou sur une map
3. Cliquez sur **"▶ Démarrer Collecte (2 min)"**
4. Le bot capture des screenshots toutes les 2 secondes pendant 2 minutes
5. Les images sont sauvegardées dans `player_dataset/images/`

#### Étape 2 : Déplacer les images

1. Cliquez sur **"📦 Déplacer Images vers Personnage/"**
2. Les images sont déplacées vers `player_dataset/images/Personnage/`

#### Étape 3 : Annoter les images

1. Cliquez sur **"✏️ Ouvrir Annotateur Manuel"** (ou allez dans **"Annoter Personnage"**)
2. L'annotateur s'ouvre avec toutes les images
3. Pour chaque image :
   - **Cliquez et glissez** pour dessiner une bounding box autour du personnage
   - Cliquez sur **"✅ Valider Annotation"** ou appuyez sur **Entrée**
   - Utilisez les **flèches** ou les boutons pour naviguer
4. Les annotations sont sauvegardées dans `player_dataset/images/Personnage/` au format YOLO

**Raccourcis clavier :**
- `←` / `→` : Navigation entre les images
- `Entrée` : Valider l'annotation
- Clic + Glisser : Dessiner une bounding box

#### Étape 4 : Préparer le dataset

1. Cliquez sur **"📦 Préparer Dataset (Train/Val)"**
2. Le script :
   - Copie les images annotées vers `player_dataset/train/` (80%)
   - Copie les images annotées vers `player_dataset/validation/` (20%)
   - Crée le fichier `player_dataset/data.yaml` (configuration YOLO)
   - **Conserve les originaux** dans `Personnage/`

#### Étape 5 : Entraîner le modèle

1. Cliquez sur **"🚀 Lancer Entraînement YOLO"**
2. L'entraînement démarre (peut prendre plusieurs minutes)
3. Le modèle entraîné est sauvegardé dans `runs/player/train/weights/best.pt`

### Structure des fichiers après annotation

```
player_dataset/
├── images/
│   └── Personnage/          ← Images annotées (ORIGINAUX)
│       ├── image1.jpg
│       ├── image1.txt       ← Annotations YOLO
│       ├── image2.jpg
│       └── image2.txt
├── train/
│   ├── images/              ← 80% des images (COPIÉES)
│   └── labels/              ← 80% des annotations (COPIÉES)
├── validation/
│   ├── images/              ← 20% des images (COPIÉES)
│   └── labels/              ← 20% des annotations (COPIÉES)
└── data.yaml                ← Configuration YOLO
```

### Format des annotations YOLO

Chaque fichier `.txt` contient une ligne par objet détecté :
```
class_id x_center y_center width height
```

Exemple :
```
0 0.512345 0.456789 0.123456 0.234567
```

- Toutes les valeurs sont normalisées entre 0 et 1
- `class_id` : 0 pour "personnage"
- `x_center, y_center` : Centre de la bounding box
- `width, height` : Largeur et hauteur de la bounding box

---

## 🏗️ Architecture technique

### Modules principaux

#### `main.py`
- Point d'entrée principal du bot
- Gestion de la boucle principale
- Coordination entre navigation, pêche et combat
- Sauvegarde/chargement de l'état du circuit

#### `gui.py`
- Interface graphique complète (CustomTkinter)
- Gestion de tous les menus et vues
- Intégration de l'annotateur
- Contrôle du bot (start/stop)

#### `vision.py`
- Détection d'objets avec YOLO
- Détection des poissons
- Détection du personnage
- Traitement d'images (OpenCV)

#### `navigation.py`
- Calcul des directions (haut, bas, gauche, droite)
- Génération de points de clic pour la navigation
- Gestion des déplacements entre maps
- Équipement de la dragodinde

#### `combat.py`
- Détection du début/fin de combat
- Gestion des tours de combat
- Lancer de sorts
- Détection de la position du personnage

#### `annotate_player.py`
- Annotateur d'images pour YOLO
- Interface graphique avec Canvas Tkinter
- Dessin de bounding boxes
- Sauvegarde au format YOLO

#### `collect_player_data.py`
- Collecte automatique de screenshots
- Capture d'images à intervalles réguliers
- Sauvegarde organisée des images

#### `prepare_player_dataset.py`
- Préparation du dataset pour YOLO
- Séparation train/validation (80/20)
- Création du fichier `data.yaml`
- Copie des images et annotations

#### `train_player.py`
- Entraînement du modèle YOLO
- Configuration des hyperparamètres
- Sauvegarde du modèle entraîné

### Technologies utilisées

- **YOLO (Ultralytics)** : Détection d'objets par IA
- **OpenCV** : Traitement d'images
- **PyAutoGUI** : Automatisation de la souris/clavier
- **CustomTkinter** : Interface graphique moderne
- **PIL/Pillow** : Manipulation d'images
- **NumPy** : Calculs numériques

---

## 📁 Structure des fichiers

```
DOFUS/
├── gui.py                      # Interface graphique principale
├── main.py                     # Point d'entrée du bot
├── vision.py                   # Détection IA (YOLO)
├── navigation.py               # Navigation automatique
├── combat.py                   # Gestion de combat
├── annotate_player.py          # Annotateur d'images (standalone)
├── collect_player_data.py      # Collecte de données
├── prepare_player_dataset.py   # Préparation dataset YOLO
├── train_player.py             # Entraînement modèle personnage
├── train_fish.py               # Entraînement modèle poissons
├── requirements.txt            # Dépendances Python
├── README.md                   # Ce fichier
│
├── templates/                  # Templates d'images pour matching
│   ├── pret.png
│   ├── pecher.png
│   ├── player_face.png
│   └── ...
│
├── player_dataset/             # Dataset pour entraîner le modèle personnage
│   ├── images/
│   │   └── Personnage/        # Images annotées (originaux)
│   ├── train/                  # 80% des images (copiées)
│   ├── validation/            # 20% des images (copiées)
│   └── data.yaml               # Configuration YOLO
│
├── runs/                       # Résultats d'entraînement YOLO
│   ├── player/
│   │   └── train/
│   │       └── weights/
│   │           └── best.pt     # Modèle entraîné personnage
│   └── fish/
│       └── train/
│           └── weights/
│               └── best.pt     # Modèle entraîné poissons
│
├── bot_settings.json           # Paramètres du bot
├── circuits.json               # Circuits sauvegardés
├── screen_profiles.json        # Profils d'écran
├── manual_moves.json           # Calibrages navigation
├── manual_fishing.json         # Calibrages pêche
└── manual_combat.json          # Calibrages combat
```

---

## 🔧 Dépannage

### Le bot ne détecte pas les poissons

1. **Vérifier que le modèle est entraîné**
   - Le fichier `runs/fish/train/weights/best.pt` doit exister
   - Si absent, entraînez le modèle avec `train_fish.py`

2. **Vérifier les calibrages**
   - Allez dans **"Données & Map"**
   - Vérifiez que les spots de pêche sont bien calibrés pour chaque map

3. **Ajuster la confiance de détection**
   - Modifiez le seuil de confiance dans `vision.py` si nécessaire

### Le bot ne navigue pas correctement

1. **Vérifier les calibrages de navigation**
   - Allez dans **"Données & Map"** → Onglet "Navigation"
   - Vérifiez que toutes les sorties sont calibrées

2. **Vérifier le profil d'écran**
   - Assurez-vous que le bon profil d'écran est sélectionné
   - Les calibrages sont spécifiques à chaque résolution d'écran

3. **Recalibrer si nécessaire**
   - Allez dans **"Calibrage Manuel"**
   - Recalibrez les sorties manquantes

### Le bot ne détecte pas le combat

1. **Vérifier le template**
   - Le fichier `templates/pret.png` doit exister
   - Capturez un nouveau template si nécessaire

2. **Ajuster la confiance**
   - Le bot essaie plusieurs seuils de confiance (0.5, 0.6, 0.7)
   - Si ça ne fonctionne toujours pas, vérifiez que le template correspond bien

### L'annotateur ne charge pas les images

1. **Vérifier le chemin**
   - Les images doivent être dans `player_dataset/images/Personnage/`
   - Vérifiez que le dossier existe

2. **Vérifier les formats**
   - Formats supportés : `.jpg`, `.jpeg`, `.png`
   - Les fichiers doivent avoir des noms valides

### Erreur "pyimageX doesn't exist"

Cette erreur a été corrigée dans la version intégrée de l'annotateur. Si vous utilisez l'ancienne version standalone (`annotate_player.py`), utilisez plutôt l'annotateur intégré dans l'interface.

### Le modèle ne s'entraîne pas

1. **Vérifier les données**
   - Il faut au moins quelques images annotées
   - Vérifiez que `player_dataset/data.yaml` existe

2. **Vérifier les dépendances**
   - `ultralytics` doit être installé : `pip install ultralytics`
   - `yolov8n.pt` sera téléchargé automatiquement

3. **Vérifier les chemins**
   - Les chemins dans `data.yaml` doivent être corrects
   - Utilisez des chemins absolus si nécessaire

---

## 📝 Notes importantes

### Sécurité

- ⚠️ **Ce bot est à usage éducatif uniquement**
- ⚠️ **L'utilisation de bots peut violer les conditions d'utilisation de Dofus**
- ⚠️ **Utilisez à vos propres risques**

### Performance

- Le bot fonctionne mieux avec une résolution d'écran fixe
- Évitez de bouger la fenêtre de Dofus pendant l'exécution
- Fermez les applications gourmandes en ressources

### Amélioration continue

- Le bot s'améliore avec plus de données annotées
- Entraînez régulièrement le modèle avec de nouvelles images
- Calibrez précisément pour de meilleures performances

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir une issue pour signaler un bug
- Proposer de nouvelles fonctionnalités
- Améliorer la documentation

---

## 📄 Licence

Ce projet est fourni "tel quel", sans garantie d'aucune sorte.

---

## 👤 Auteur

**Torkor29**

- GitHub: [@Torkor29](https://github.com/Torkor29)
- Repository: [DOFUS](https://github.com/Torkor29/DOFUS)

---

## 🎉 Remerciements

- [Ultralytics](https://github.com/ultralytics/ultralytics) pour YOLO
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) pour l'interface graphique
- La communauté Dofus pour les retours et suggestions

---

**Dernière mise à jour :** Janvier 2025

**Version :** 2.0 (avec annotateur intégré et système d'entraînement complet)

