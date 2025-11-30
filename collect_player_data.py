import cv2
import numpy as np
import pyautogui
import time
import os
from datetime import datetime
import threading

class PlayerDataCollector:
    def __init__(self):
        self.is_collecting = False
        self.stop_event = threading.Event()
        
    def detect_red_circle_bbox(self, img_np):
        """
        Détecte le rond rouge autour du personnage et retourne une bounding box YOLO.
        Retourne (x_center, y_center, width, height) normalisés entre 0 et 1, ou None si non trouvé.
        """
        h, w = img_np.shape[:2]
        hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        
        # Plages de rouge (même que dans combat.py)
        lower1, upper1 = np.array([0, 60, 60]), np.array([15, 255, 255])
        lower2, upper2 = np.array([165, 60, 60]), np.array([180, 255, 255])
        mask = cv2.bitwise_or(cv2.inRange(hsv, lower1, upper1), cv2.inRange(hsv, lower2, upper2))
        
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Critères stricts : taille et circularité
            if 1000 < area < 8000:
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0: continue
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                # Forme ronde exigée (>0.6)
                if circularity > 0.60:
                    # Calculer la bounding box
                    x, y, box_w, box_h = cv2.boundingRect(cnt)
                    
                    # Étendre un peu la bbox pour inclure le personnage complet
                    margin = 20
                    x = max(0, x - margin)
                    y = max(0, y - margin)
                    box_w = min(w - x, box_w + 2*margin)
                    box_h = min(h - y, box_h + 2*margin)
                    
                    # Convertir en format YOLO (normalisé 0-1)
                    x_center = (x + box_w / 2) / w
                    y_center = (y + box_h / 2) / h
                    width = box_w / w
                    height = box_h / h
                    
                    candidates.append({
                        'bbox': (x_center, y_center, width, height),
                        'area': area,
                        'circ': circularity
                    })
        
        if not candidates:
            return None
        
        # Prendre le meilleur candidat (le plus circulaire et de taille idéale)
        candidates.sort(key=lambda c: c['circ'] + (1.0 - abs(c['area']-3500)/3500.0), reverse=True)
        return candidates[0]['bbox']
    
    def collect_images_only(self, duration_seconds=120, interval=2.0, save_dir="player_dataset/images/Personnage", callback=None):
        """
        Collecte des images SANS annotation automatique.
        duration_seconds: Durée totale de la collecte (défaut: 120s = 2 minutes)
        interval: Intervalle entre chaque capture (défaut: 2.0s)
        save_dir: Dossier de sauvegarde
        callback: Fonction appelée pour mettre à jour l'UI (message, count, total)
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self.is_collecting = True
        self.stop_event.clear()
        
        total_captures = int(duration_seconds / interval)
        count = 0
        
        if callback:
            callback(f"📸 Collecte démarrée ! {total_captures} images prévues...", 0, total_captures)
        
        start_time = time.time()
        
        try:
            while not self.stop_event.is_set() and (time.time() - start_time) < duration_seconds:
                # Capture
                screenshot = pyautogui.screenshot()
                img_np = np.array(screenshot)
                h, w = img_np.shape[:2]
                
                # Nom unique
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                base_name = f"player_{timestamp}"
                img_path = os.path.join(save_dir, f"{base_name}.jpg")
                
                # Sauvegarde de l'image (sans annotation)
                cv2.imwrite(img_path, cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR))
                
                count += 1
                
                if callback:
                    status = f"📸 [{count}/{total_captures}] Image sauvegardée"
                    callback(status, count, total_captures)
                
                # Attendre l'intervalle
                time.sleep(interval)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.is_collecting = False
            if callback:
                callback(f"✅ Collecte terminée ! {count} images capturées.", count, total_captures)
            print(f"\n✅ Collecte terminée : {count} images")
    
    def stop_collection(self):
        """Arrête la collecte en cours."""
        self.stop_event.set()
        self.is_collecting = False

if __name__ == "__main__":
    collector = PlayerDataCollector()
    print("=== COLLECTEUR DE DONNÉES PERSONNAGE ===")
    print("Démarrage dans 3 secondes...")
    print("Appuyez sur Ctrl+C pour arrêter.")
    time.sleep(3)
    collector.collect_images_only(duration_seconds=120, interval=2.0)

