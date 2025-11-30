import cv2
import numpy as np
import pyautogui
import time
import os
from datetime import datetime

def collect_images(interval=3.0, save_dir="dataset/images"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    print(f"=== COLLECTEUR D'IMAGES DOFUS ===")
    print(f"Les images seront sauvegardées dans : {save_dir}")
    print(f"Intervalle : {interval} secondes")
    print("Appuyez sur Ctrl+C dans ce terminal pour arrêter.")
    print("Démarrage dans 3 secondes...")
    time.sleep(3)
    
    count = 0
    try:
        while True:
            # Capture
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Nom unique basé sur l'heure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{save_dir}/dofus_{timestamp}.jpg"
            
            # Sauvegarde
            cv2.imwrite(filename, frame)
            count += 1
            print(f"[{count}] Image sauvegardée : {filename}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nArrêt de la collecte.")
        print(f"Total capturé : {count} images.")

if __name__ == "__main__":
    collect_images()

