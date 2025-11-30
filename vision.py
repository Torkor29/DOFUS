import cv2
import numpy as np
import pyautogui
import os
import time
from ultralytics import YOLO

class Vision:
    def __init__(self):
        # Charger le modèle YOLO entraîné
        # On utilise le chemin relatif standard de YOLOv8
        model_path = os.path.abspath("runs/detect/train/weights/best.pt")
        
        if not os.path.exists(model_path):
            # Fallback si jamais le chemin est différent (parfois runs\detect\train2...)
            print(f"Attention: Modèle non trouvé à {model_path}")
            # On essaye de trouver le dernier 'best.pt' manuellement
            possible_paths = []
            for root, dirs, files in os.walk("runs"):
                if "best.pt" in files:
                    possible_paths.append(os.path.join(root, "best.pt"))
            
            if possible_paths:
                model_path = possible_paths[-1] # Prendre le plus récent (souvent le dernier dossier créé)
                print(f"Modèle trouvé à : {model_path}")
            else:
                raise FileNotFoundError("Impossible de trouver le fichier best.pt. Avez-vous lancé train.py ?")
            
        self.model = YOLO(model_path)
        print("Modèle IA (Soleil) chargé avec succès.")
        
        self.fish_model = None

    def load_fish_model(self):
        """Charge le modèle spécifique pour la pêche si ce n'est pas déjà fait."""
        if self.fish_model is not None:
            return

        fish_model_path = os.path.abspath("runs/fish/train/weights/best.pt")
        if not os.path.exists(fish_model_path):
            print(f"Attention: Modèle poisson non trouvé à {fish_model_path}")
            return

        self.fish_model = YOLO(fish_model_path)
        print("Modèle IA (Poisson) chargé avec succès.")

    def _remove_duplicates(self, points, distance_threshold=60):
        """Supprime les points trop proches les uns des autres pour éviter de cliquer 2 fois au même endroit"""
        if not points: return []
        
        unique_points = []
        for p in points:
            is_duplicate = False
            for up in unique_points:
                # Calcul distance euclidienne
                dist = ((p[0] - up[0])**2 + (p[1] - up[1])**2)**0.5
                if dist < distance_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_points.append(p)
        return unique_points

    def get_manual_fish_points(self, current_map_str):
        """Récupère les points manuels de pêche pour une map donnée"""
        try:
            import json
            if os.path.exists("manual_fishing.json"):
                with open("manual_fishing.json", "r") as f:
                    data = json.load(f)
                
                if current_map_str in data:
                    print(f"🎣 Points de pêche manuels trouvés pour {current_map_str} !")
                    return [tuple(p) for p in data[current_map_str]]
        except Exception as e:
            print(f"Erreur lecture points pêche manuels : {e}")
        return None

    def find_fish(self, current_map_coords=None):
        """
        Détecte les poissons sur l'écran.
        Retourne une liste de points (x, y) où cliquer.
        """
        # 1. Vérification points manuels (Priorité Absolue)
        if current_map_coords:
            map_str = f"{current_map_coords[0]},{current_map_coords[1]}"
            manual_points = self.get_manual_fish_points(map_str)
            if manual_points:
                print(f"🎯 Utilisation EXCLUSIVE des {len(manual_points)} points manuels.")
                return manual_points

        self.load_fish_model()
        if self.fish_model is None:
            print("Impossible de chercher des poissons : modèle non chargé.")
            return []

        img = self.take_screenshot()
        
        # Seuil de confiance TRES BAS (0.10) pour être sûr de ne rien rater
        results = self.fish_model(img, conf=0.10, verbose=False)
        
        fish_points = []
        
        # Création dossier debug si inexistant (Chemin absolu pour être sûr)
        debug_dir = os.path.abspath("debug_fish")
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
            
        # Sauvegarde de l'image avec les détections pour debug
        # On utilise plot() qui dessine les boîtes sur l'image
        annotated_frame = results[0].plot()
        timestamp = int(time.time())
        save_path = os.path.join(debug_dir, f"fish_check_{timestamp}.jpg")
        cv2.imwrite(save_path, annotated_frame)
        print(f"📸 Analyse sauvegardée : {save_path}")
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # print(f"Poisson détecté en ({center_x}, {center_y})")
                fish_points.append((center_x, center_y))
        
        # Nettoyage des doublons
        cleaned_points = self._remove_duplicates(fish_points)
        print(f"Poissons détectés : {len(fish_points)} -> Après nettoyage : {len(cleaned_points)}")
        
        return cleaned_points

    def take_screenshot(self):
        """Prend une capture d'écran et la convertit pour OpenCV"""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def find_sun(self, direction):
        """
        Cherche un soleil à l'aide de l'IA (YOLO).
        Filtre pour ne garder que celui qui est dans la bonne direction.
        """
        img = self.take_screenshot()
        h, w = img.shape[:2]
        
        # Inférence (Detection)
        # conf=0.4 : On accepte les détections avec 40% de confiance minimum
        results = self.model(img, conf=0.4, verbose=False)
        
        best_point = None
        max_conf = 0
        
        # On parcourt les détections
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Coordonnées de la boîte (x1, y1, x2, y2)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # Vérifier si ce soleil est dans la bonne direction
                is_valid = False
                
                # Marge plus large pour YOLO car il détecte la boite entière
                # On divise l'écran en zones logiques
                
                if direction == "DROITE":
                    # Doit être dans le tiers droit de l'écran
                    if center_x > w * 0.75: is_valid = True
                elif direction == "GAUCHE":
                    # Doit être dans le tiers gauche
                    if center_x < w * 0.25: is_valid = True
                elif direction == "HAUT":
                    # Doit être dans le tiers haut
                    if center_y < h * 0.25: is_valid = True
                elif direction == "BAS":
                    # Doit être dans le tiers bas
                    if center_y > h * 0.75: is_valid = True
                
                if is_valid:
                    print(f"Soleil détecté par IA en ({center_x}, {center_y}) [Confiance: {conf:.2f}]")
                    if conf > max_conf:
                        max_conf = conf
                        best_point = (center_x, center_y)
        
        return best_point

    def has_map_changed(self, img_before, img_after):
        """
        Compare deux screenshots pour savoir si on a changé de map.
        Retourne True si la différence est significative.
        """
        # Convertir en gris pour simplifier la comparaison
        gray_before = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY)
        gray_after = cv2.cvtColor(img_after, cv2.COLOR_BGR2GRAY)

        # Calculer la différence absolue
        diff = cv2.absdiff(gray_before, gray_after)
        
        # Compter le nombre de pixels différents (seuil de 30 pour éviter le bruit)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        changed_pixels = np.count_nonzero(thresh)
        
        total_pixels = gray_before.size
        percentage_changed = (changed_pixels / total_pixels) * 100
        
        print(f"Différence d'image : {percentage_changed:.2f}%")
        
        # Si plus de 5% de l'écran a changé, c'est probablement un chargement de map
        return percentage_changed > 5.0
