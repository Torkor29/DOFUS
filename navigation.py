import pyautogui
import time
import random
import os

class Navigation:
    def __init__(self):
        print("Module Navigation initialisé (Mode Rapide sans OCR).")

    def get_direction(self, current_map, target_map):
        cur_x, cur_y = current_map
        tar_x, tar_y = target_map

        if tar_x > cur_x: return "DROITE"
        elif tar_x < cur_x: return "GAUCHE"
        elif tar_y < cur_y: return "HAUT" 
        elif tar_y > cur_y: return "BAS"
        return None

    def get_grid_points(self, direction, steps=5):
        screen_w, screen_h = pyautogui.size()
        game_h = screen_h
        game_w = int(game_h * (4/3))
        
        if game_w > screen_w:
            game_w = screen_w
            game_h = int(game_w * (3/4))
            offset_x = 0
            offset_y = (screen_h - game_h) // 2
        else:
            offset_x = (screen_w - game_w) // 2
            offset_y = 0

        points = []
        margin_game = 20 
        ui_bottom = 150 
        
        min_x = offset_x + margin_game
        max_x = offset_x + game_w - margin_game
        min_y = offset_y + margin_game
        max_y = offset_y + game_h - ui_bottom

        usable_h = max_y - min_y
        usable_w = max_x - min_x

        if direction == "DROITE":
            step_y = usable_h // steps
            for i in range(steps):
                points.append((max_x, min_y + (i * step_y) + (step_y // 2)))
        elif direction == "GAUCHE":
            step_y = usable_h // steps
            for i in range(steps):
                points.append((min_x, min_y + (i * step_y) + (step_y // 2)))
        elif direction == "HAUT":
            step_x = usable_w // steps
            for i in range(steps):
                points.append((min_x + (i * step_x) + (step_x // 2), min_y))
        elif direction == "BAS":
            step_x = usable_w // steps
            for i in range(steps):
                points.append((min_x + (i * step_x) + (step_x // 2), max_y))
        
        points = [(int(x), int(y)) for x, y in points]
        if points:
            mid = len(points) // 2
            center_point = points.pop(mid)
            random.shuffle(points)
            points.insert(0, center_point)
        
        return points

    def get_manual_point(self, current_map, direction):
        """Vérifie s'il existe un point de clic manuel pour cette map et cette direction"""
        try:
            import json
            if os.path.exists("manual_moves.json"):
                with open("manual_moves.json", "r") as f:
                    data = json.load(f)
                
                # Clé : "x,y_DIRECTION" (ex: "12,4_DROITE")
                key = f"{current_map[0]},{current_map[1]}_{direction}"
                
                if key in data:
                    val = data[key]
                    # Format: [x, y] ou [x, y, "forced_map"]
                    point = (val[0], val[1])
                    print(f"📍 Point manuel trouvé pour {key} : {point}")
                    return point
        except Exception as e:
            print(f"Erreur lecture points manuels : {e}")
        return None

    def get_forced_next_map(self, current_map, direction):
        """Récupère la map de destination forcée si elle existe"""
        try:
            import json
            if os.path.exists("manual_moves.json"):
                with open("manual_moves.json", "r") as f:
                    data = json.load(f)
                
                key = f"{current_map[0]},{current_map[1]}_{direction}"
                if key in data:
                    val = data[key]
                    if len(val) >= 3:
                        target_str = val[2] # "10,-5"
                        try:
                            parts = target_str.split(',')
                            return [int(parts[0]), int(parts[1])]
                        except:
                            pass
        except:
            pass
        return None

    def click_point(self, point):
        if not point: return
        x, y = point
        x += random.randint(-5, 5)
        y += random.randint(-5, 5)
        print(f"Clic en {x}, {y}")
        pyautogui.moveTo(x, y, duration=random.uniform(0.3, 0.6)) 
        time.sleep(0.1)
        pyautogui.click()

    def equip_dragodinde(self):
        """Équipe la dragodinde (double-clic sur le point calibré)"""
        try:
            import json
            if os.path.exists("manual_combat.json"):
                with open("manual_combat.json", "r") as f:
                    data = json.load(f)
                    if "dd_point" in data:
                        x, y = data["dd_point"]
                        print("🐉 Équipement dragodinde...")
                        pyautogui.moveTo(x, y, duration=0.4)
                        time.sleep(0.1)
                        pyautogui.click(clicks=2, interval=0.05)
                        time.sleep(0.5)
                        return True
        except Exception as e:
            print(f"⚠️ Erreur équipement dragodinde : {e}")
        return False

    def click_fish(self, point):
        """
        Cliquer sur un poisson puis sur 'Pêcher'.
        Retourne True si le menu Pêcher a bien été trouvé, False sinon.
        """
        if not point:
            return False
        
        x, y = point
        
        # 1. Clic gauche sur le poisson
        print(f"Target poisson: {x}, {y}")
        pyautogui.moveTo(x, y, duration=random.uniform(0.3, 0.5))
        time.sleep(0.1)
        pyautogui.click()
        
        # 2. Attente ouverture menu contextuel
        time.sleep(0.6)
        
        # 3. Détection du menu "Pêcher" (plusieurs templates possibles)
        # Liste des templates à essayer dans l'ordre avec leur confiance requise
        templates_config = [
            ("pecher.png", 0.6),
            ("poissons mer.png", 0.65),  # Confiance réduite pour mieux détecter
            ("poissons rivière.png", 0.65)
        ]
        
        match = None
        found_template = None
        
        # On essaie chaque template
        for template_name, confidence in templates_config:
            template_path = os.path.join("templates", template_name)
            if not os.path.exists(template_path):
                continue
            
            try:
                # 3a. D'abord une recherche autour du clic (zone plus large pour les nouveaux templates)
                if "poissons" in template_name.lower():
                    # Zone plus large pour les menus "Poissons (mer)" et "Poissons (rivière)"
                    region = (x - 150, y - 100, 300, 200)
                else:
                    region = (x - 120, y - 80, 240, 160)
                
                match = pyautogui.locateCenterOnScreen(template_path, region=region, confidence=confidence, grayscale=False)
                if match:
                    menu_x, menu_y = match
                    # Vérification supplémentaire : le menu doit être proche du clic (max 180px pour les nouveaux templates)
                    max_dist = 180 if "poissons" in template_name.lower() else 150
                    dist = ((menu_x - x)**2 + (menu_y - y)**2)**0.5
                    if dist <= max_dist:
                        found_template = template_name
                        print(f"✅ Menu détecté via '{template_name}' (recherche locale, distance: {int(dist)}px)")
                        break
                    else:
                        match = None  # Trop loin, on ignore
            except Exception as e:
                pass
        
        # Si pas trouvé localement, on essaie globalement pour TOUS les templates (mais avec vérification de distance stricte)
        if not match:
            for template_name, confidence in templates_config:
                template_path = os.path.join("templates", template_name)
                if not os.path.exists(template_path):
                    continue
                
                try:
                    print(f"🔎 Recherche globale du menu '{template_name}' (fallback)...")
                    match = pyautogui.locateCenterOnScreen(template_path, confidence=confidence, grayscale=False)
                    if match:
                        menu_x, menu_y = match
                        # Vérification stricte : le menu doit être dans une zone raisonnable (max 200px)
                        dist = ((menu_x - x)**2 + (menu_y - y)**2)**0.5
                        if dist <= 200:
                            found_template = template_name
                            print(f"✅ Menu détecté via '{template_name}' (recherche globale, distance: {int(dist)}px)")
                            break
                        else:
                            match = None
                except Exception as e:
                    pass
        
        if not match:
            print("⛔ Aucun menu 'Pêcher' détecté, on passe au prochain spot.")
            return False
        
        menu_x, menu_y = match
        # Ajustement : on descend légèrement le clic car le template peut correspondre au titre du menu
        # plutôt qu'au bouton "Pêcher" lui-même
        click_y = menu_y + 8  # +8 pixels vers le bas pour viser le bouton "Pêcher"
        print(f"👇 Pêche : {menu_x}, {click_y} (menu détecté, ajusté)")
        pyautogui.moveTo(menu_x, click_y, duration=random.uniform(0.2, 0.4))
        time.sleep(0.1)
        pyautogui.click()
        return True

    def check_levelup(self):
        """Vérifie si un popup de niveau est présent et appuie sur Entrée"""
        if not os.path.exists("templates"): return

        # On cherche des images contenant 'level', 'up', 'popup' ou 'ok'
        keywords = ['level', 'up', 'popup', 'ok']
        template_files = [f for f in os.listdir("templates") if any(k in f.lower() for k in keywords) and f.endswith(('.png', '.jpg', '.jpeg'))]
        
        for tmpl in template_files:
            path = os.path.join("templates", tmpl)
            try:
                # Recherche sur tout l'écran (le popup est souvent au milieu)
                # Confidence 0.7 pour être souple
                if pyautogui.locateOnScreen(path, confidence=0.7):
                    print(f"🎉 POPUP DÉTECTÉ ({tmpl}) ! Validation automatique.")
                    pyautogui.press('enter')
                    time.sleep(1.0) # On laisse le temps au popup de disparaître
                    return True
            except:
                pass
        return False
