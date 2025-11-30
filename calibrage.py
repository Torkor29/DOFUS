import pyautogui
import json
import os
import time

FILE_NAME = "manual_moves.json"

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=4)

def main():
    print("=== OUTIL DE CALIBRAGE DE DÉPLACEMENT ===")
    print("Permet de définir un clic précis pour une map difficile.")
    
    while True:
        print("\n-----------------------------------")
        map_str = input("Entrez les coordonnées de la map (ex: 12,4) ou 'q' pour quitter : ")
        if map_str.lower() == 'q': break
        
        direction = input("Entrez la direction (HAUT, BAS, GAUCHE, DROITE) : ").upper()
        if direction not in ["HAUT", "BAS", "GAUCHE", "DROITE"]:
            print("Direction invalide.")
            continue
            
        print(f"\nplacez votre souris sur le soleil/changement de map pour [{map_str}] -> {direction}.")
        print("Vous avez 5 secondes...")
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
            
        x, y = pyautogui.position()
        print(f"Point capturé : ({x}, {y})")
        
        # Clé unique : "12,4_DROITE"
        key = f"{map_str}_{direction}"
        
        data = load_data()
        data[key] = [x, y]
        save_data(data)
        
        print(f"✅ Sauvegardé ! Le bot cliquera désormais exactement en ({x}, {y}) sur la map {map_str} pour aller à {direction}.")

if __name__ == "__main__":
    main()

