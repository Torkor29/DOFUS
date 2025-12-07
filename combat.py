import cv2
import numpy as np
import pyautogui
import time
import os
import json

class Combat:
    def __init__(self):
        print("⚔️ Module Combat initialisé.")
        self.last_pa_img = None
        self.in_combat = False
        self.last_known_player_pos = None
        self.player_model = None
        self.mobs_model = None
        self._load_player_model()
        self._load_mobs_model()

    def check_combat_start(self, debug=False):
        """
        Vérifie si un combat a commencé ou s'est terminé.
        debug: Si True, affiche des logs détaillés pour comprendre pourquoi ça ne détecte pas.
        """
        if debug:
            print("   [DEBUG] Vérification état combat...")
        
        # Détection du bouton "Prêt" avec plusieurs tentatives
        pret_pos = None
        
        # Essayer avec différentes confiances et modes
        for conf in [0.5, 0.6, 0.7]:
            # Essayer sans grayscale d'abord (le bouton est orange/coloré)
            pret_pos = self._find_template("pret.png", confidence=conf, grayscale=False)
            if pret_pos:
                if debug:
                    print(f"   [DEBUG] ✅ Bouton Prêt trouvé (confiance {conf}, couleur)")
                print(f"⚔️ Combat détecté (Bouton Prêt, confiance {conf}) ! Préparation...")
                break
            # Si pas trouvé, essayer avec grayscale (au cas où)
            pret_pos = self._find_template("pret.png", confidence=conf, grayscale=True)
            if pret_pos:
                if debug:
                    print(f"   [DEBUG] ✅ Bouton Prêt trouvé (confiance {conf}, grayscale)")
                print(f"⚔️ Combat détecté (Bouton Prêt, confiance {conf}, grayscale) ! Préparation...")
                break
        
        if debug and not pret_pos:
            print("   [DEBUG] ❌ Bouton Prêt non trouvé (vérifier que pret.png existe dans templates/)")
        
        if pret_pos and not self.in_combat:
            self.equip_drop_weapon()
            print("⚔️ Clic sur 'Prêt' pour lancer le combat.")
            pyautogui.click(pret_pos)
            time.sleep(1.0)
            print("⏳ Attente démarrage combat (3s)...")
            time.sleep(3.0)
            print("⏳ Attente supplémentaire pour laisser le mob jouer en premier (5s)...")
            time.sleep(5.0)
            self.in_combat = True
            return True
        
        # Vérification si on est déjà en combat (PA/PM visibles)
        # Même si on n'a pas vu le bouton "Prêt", si on voit les icônes PA/PM, on est en combat
        has_pa_pm = self._has_pa_pm_icons()
        if has_pa_pm and not self.in_combat:
            if debug:
                print("   [DEBUG] ✅ Icônes PA/PM détectées -> Combat en cours (démarrage manqué)")
            print("⚔️ Combat détecté via icônes PA/PM ! (Le bot a manqué le début)")
            self.in_combat = True
            return True
        
        # Détection fin de combat
        fermer_pos = self._find_template("fermer_combat.png", confidence=0.8)
        if debug:
            if fermer_pos:
                print("   [DEBUG] ✅ Bouton Fermer trouvé")
            else:
                print("   [DEBUG] ❌ Bouton Fermer non trouvé")
        
        if fermer_pos and not self._has_pa_pm_icons():
            if self.in_combat:
                print("✅ Fin de combat détectée (Bouton Fermer) ! Clic...")
                pyautogui.click(fermer_pos)
                time.sleep(1.0)
                self.equip_fishing_weapon()
                self.in_combat = False
            return False
        
        if debug:
            print(f"   [DEBUG] État actuel : in_combat={self.in_combat}, has_pa_pm={has_pa_pm}")
        
        return self.in_combat

    def handle_combat_turn(self):
        if not self.in_combat: return False

        if self._find_template("fermer_combat.png", confidence=0.8) and not self._has_pa_pm_icons():
            print("✅ Combat terminé.")
            self.check_combat_start()
            return False

        print("⚡ Tour de combat...")
        
        target = self._get_manual_point("target_point")
        spell = self._get_manual_point("spell_point")
        pa_point = self._get_manual_point("ap_point") 
        
        if not target or not spell:
            print("⚠️ Points de combat non calibrés.")
            return True

        # 1. Vérification Portée / Déplacement
        can_attack = True
        if pa_point:
            can_attack = self._can_attack(spell, target, pa_point)

        if not can_attack:
            print("🚶 Hors de portée ! Tentative de déplacement...")
            moved = self._move_towards_target(target)
            if moved:
                time.sleep(2.5)
                if pa_point:
                    self._can_attack(spell, target, pa_point) # Juste pour log l'info
        
        # 2. Attaque
        try:
            with open("bot_settings.json", "r") as f:
                settings = json.load(f)
                spell_count = int(settings.get("combat_spell_count", 3))
        except: spell_count = 3

        print(f"⚔️ Lancement des sorts ({spell_count} fois)...")
        for i in range(spell_count):
            if self._find_template("fermer_combat.png", confidence=0.8): break
            pyautogui.click(spell)
            time.sleep(0.6)
            pyautogui.click(target)
            pyautogui.moveRel(0, -150) 
            time.sleep(1.8)

        # 3. Fin tour
        passer_pos = self._find_template("passer_tour.png", confidence=0.7)
        if passer_pos:
            print("⌛ Fin du tour (Clic Passer).")
            pyautogui.click(passer_pos)
            pyautogui.moveTo(100, 100)
        else:
            print("⌛ Fin du tour (F1).")
            pyautogui.press('f1')

        print("💤 Attente du prochain tour...")
        time.sleep(4.0)
        return True

    # ------------------------------------------------------------------
    # DÉTECTION ROBUSTE PERSONNAGE
    # ------------------------------------------------------------------
    def _load_player_model(self):
        """Charge le modèle YOLO pour la détection du personnage si disponible."""
        try:
            from ultralytics import YOLO
            player_model_path = os.path.abspath("runs/player/train/weights/best.pt")
            if os.path.exists(player_model_path):
                self.player_model = YOLO(player_model_path)
                print("✅ Modèle IA (Personnage) chargé avec succès.")
            else:
                # Chercher dans les sous-dossiers
                possible_paths = []
                if os.path.exists("runs/player"):
                    for root, dirs, files in os.walk("runs/player"):
                        if "best.pt" in files:
                            possible_paths.append(os.path.join(root, "best.pt"))
                if possible_paths:
                    self.player_model = YOLO(possible_paths[-1])
                    print(f"✅ Modèle IA (Personnage) chargé : {possible_paths[-1]}")
                else:
                    print("ℹ️  Modèle YOLO personnage non trouvé. Utilisation des templates/rond rouge.")
        except Exception as e:
            print(f"⚠️  Impossible de charger le modèle YOLO personnage : {e}")
            self.player_model = None

    def _load_mobs_model(self):
        """Charge le modèle YOLO pour la détection des mobs si disponible."""
        try:
            from ultralytics import YOLO
            mobs_model_path = os.path.abspath("runs/mobs/train/weights/best.pt")
            if os.path.exists(mobs_model_path):
                self.mobs_model = YOLO(mobs_model_path)
                print("✅ Modèle IA (Mobs) chargé avec succès.")
            else:
                # Chercher dans les sous-dossiers
                possible_paths = []
                if os.path.exists("runs/mobs"):
                    for root, dirs, files in os.walk("runs/mobs"):
                        if "best.pt" in files:
                            possible_paths.append(os.path.join(root, "best.pt"))
                if possible_paths:
                    self.mobs_model = YOLO(possible_paths[-1])
                    print(f"✅ Modèle IA (Mobs) chargé : {possible_paths[-1]}")
                else:
                    print("ℹ️  Modèle YOLO mobs non trouvé. Utilisation de la détection par couleur (cercles bleus).")
        except Exception as e:
            print(f"⚠️  Impossible de charger le modèle YOLO mobs : {e}")
            self.mobs_model = None

    def _get_player_position(self):
        """
        Trouve le personnage. Stratégie multi-niveaux :
        0. YOLO (priorité absolue si disponible)
        1. Templates (DD/Perso multi-angles)
        2. Tracking (si template perdu)
        3. Recherche globale rond rouge (dernier recours)
        """
        print("🔍 Détection Position Personnage...")
        
        # 0. YOLO (Priorité absolue si disponible)
        if self.player_model:
            try:
                screenshot = pyautogui.screenshot()
                img_np = np.array(screenshot)
                # Seuil de confiance augmenté à 0.35 pour plus de précision (moins de faux positifs)
                # Vous pouvez ajuster entre 0.2 (plus de détections) et 0.5 (plus strict)
                results = self.player_model(img_np, conf=0.35, verbose=False)
                
                for r in results:
                    boxes = r.boxes
                    if len(boxes) > 0:
                        # Prendre la détection avec la plus haute confiance
                        best_box = boxes[0]
                        x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
                        center_x = int((x1 + x2) / 2)
                        center_y = int((y1 + y2) / 2)
                        confidence = float(best_box.conf[0].cpu().numpy())
                        
                        print(f"   ✅ YOLO : Personnage détecté en ({center_x}, {center_y}) avec confiance {confidence:.2f}")
                        self.last_known_player_pos = (center_x, center_y)
                        self._save_debug_player_position((center_x, center_y), None)
                        return (center_x, center_y)
            except Exception as e:
                print(f"   ⚠️ Erreur détection YOLO : {e}")
        
        # Liste élargie avec toutes les variantes de noms possibles
        # Priorité aux templates du personnage sous différents angles (8 directions + face/dos)
        templates = [
            # Templates personnage (multi-angles - 8 directions)
            "player_face.png", "player_dos.png", 
            "player_left.png", "player_right.png",
            "player_top.png", "player_bottom.png",
            "player_top_right.png", "player_top_left.png",
            "player_bottom_right.png", "player_bottom_left.png",
            # Template personnage (ancien système, compatibilité)
            "player_template.png",
            # Templates Dragodinde
            "DD DOS.png", "DD FACE.png", "DD COTE.png",
            "dd_dos.png", "dd_face.png", "dd_cote.png",
            "dd dos.png", "dd face.png", "dd cote.png"
        ]
        
        detected_template_pos = None
        
        # 1. RECHERCHE TEMPLATE (La plus fiable)
        print("   🔍 Recherche des templates personnage...")
        templates_tested = 0
        templates_found_list = []
        
        for t_name in templates:
            path = os.path.join("templates", t_name)
            if not os.path.exists(path):
                continue
            
            templates_tested += 1
            
            # On tente avec plusieurs niveaux de confiance
            # On commence strict (0.8) et on descend jusqu'à 0.4 pour être sûr de trouver
            # On teste aussi avec grayscale=True au cas où
            for conf in [0.8, 0.7, 0.6, 0.5, 0.4]:
                try:
                    # Essayer d'abord sans grayscale (couleurs)
                    pos = pyautogui.locateCenterOnScreen(path, confidence=conf, grayscale=False)
                    if pos:
                        detected_template_pos = pos
                        print(f"   ✅ Template '{t_name}' trouvé (confiance {conf}, couleur) en {pos}")
                        templates_found_list.append((t_name, conf, pos))
                        break # Sort de la boucle conf
                except Exception as e:
                    pass
                
                # Si pas trouvé, essayer avec grayscale
                try:
                    pos = pyautogui.locateCenterOnScreen(path, confidence=conf, grayscale=True)
                    if pos:
                        detected_template_pos = pos
                        print(f"   ✅ Template '{t_name}' trouvé (confiance {conf}, grayscale) en {pos}")
                        templates_found_list.append((t_name, conf, pos))
                        break # Sort de la boucle conf
                except Exception as e:
                    pass
            
            if detected_template_pos: 
                break # Sort de la boucle templates dès qu'on en trouve un
        
        # DEBUG : Afficher un résumé
        print(f"   📊 Templates testés : {templates_tested}/{len(templates)}")
        if not detected_template_pos:
            print(f"   ❌ AUCUN template détecté malgré {templates_tested} templates testés !")
            print(f"   💡 Vérifie que les templates correspondent bien à l'écran actuel")

        final_pos = None

        if detected_template_pos:
            # Template trouvé ! On utilise DIRECTEMENT sa position, point final
            print(f"   ✅ Template trouvé ! Position utilisée directement : {detected_template_pos}")
            final_pos = detected_template_pos
            
            # DEBUG : Screenshot de la zone détectée
            self._save_debug_player_position(final_pos, detected_template_pos)
        
        # 2. TRACKING (Si template perdu)
        elif self.last_known_player_pos:
            print(f"   🕵️ Template perdu. Recherche rond rouge près de dernière pos : {self.last_known_player_pos}")
            circle_pos = self._find_red_circle_near_position(self.last_known_player_pos, search_radius=250)
            if circle_pos:
                print(f"   ✅ Retrouvé via tracking : {circle_pos}")
                final_pos = circle_pos

        # 3. RECHERCHE GLOBALE (Dernier recours, strict)
        # On cherche le rond rouge mais SANS privilégier une zone spécifique
        # Le personnage peut être n'importe où sur la map
        if not final_pos:
            print("   ⚠️ Aucun template trouvé ! Recherche globale rond rouge (Dernier recours)...")
            w, h = pyautogui.size()
            region = (int(w*0.05), int(h*0.05), int(w*0.9), int(h*0.75))
            # Ne pas privilégier une zone spécifique, utiliser uniquement la circularité et la taille
            final_pos = self._detect_red_circle_cv2(region, offset=(region[0], region[1]), sort_by_dist_to=None)
            
            if final_pos:
                print(f"   ⚠️ Rond rouge trouvé via recherche globale : {final_pos}")
                print(f"   ⚠️ ATTENTION : Aucun template n'a été trouvé, cette détection peut être incorrecte !")

        if final_pos:
            self.last_known_player_pos = final_pos
            # DEBUG : Screenshot même si pas de template (détection globale)
            if not detected_template_pos:
                self._save_debug_player_position(final_pos, None)
            return final_pos
        else:
            print("   ❌ Échec total détection personnage.")
            return None
    
    def _save_debug_player_position(self, final_pos, template_pos=None):
        """Sauvegarde un screenshot de debug montrant où le bot détecte le personnage"""
        try:
            if not os.path.exists("debug_combat"):
                os.makedirs("debug_combat")
            
            import PIL.Image
            import PIL.ImageDraw
            
            # Prendre un screenshot d'une zone autour de la position détectée
            x, y = final_pos
            debug_size = 300  # Zone de 300x300 pixels
            region = (
                max(0, int(x) - debug_size//2),
                max(0, int(y) - debug_size//2),
                debug_size,
                debug_size
            )
            
            screenshot = pyautogui.screenshot(region=region)
            img = screenshot.copy()
            draw = PIL.ImageDraw.Draw(img)
            
            # Dessiner un cercle rouge au centre (position détectée)
            center_x = debug_size // 2
            center_y = debug_size // 2
            radius = 10
            draw.ellipse(
                [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                outline="red",
                width=3
            )
            # Ligne croix pour marquer précisément
            draw.line([center_x - 15, center_y, center_x + 15, center_y], fill="red", width=2)
            draw.line([center_x, center_y - 15, center_x, center_y + 15], fill="red", width=2)
            
            # Si on a aussi la position du template, la marquer en vert
            if template_pos:
                template_x, template_y = template_pos
                template_rel_x = template_x - region[0]
                template_rel_y = template_y - region[1]
                if 0 <= template_rel_x < debug_size and 0 <= template_rel_y < debug_size:
                    draw.ellipse(
                        [template_rel_x - 8, template_rel_y - 8, template_rel_x + 8, template_rel_y + 8],
                        outline="green",
                        width=2
                    )
            
            # Sauvegarder avec timestamp
            import time
            timestamp = int(time.time())
            debug_path = f"debug_combat/player_pos_{timestamp}.png"
            img.save(debug_path)
            print(f"   📸 DEBUG : Screenshot sauvegardé : {debug_path}")
            print(f"   📍 Position détectée marquée en ROUGE au centre de l'image")
            if template_pos:
                print(f"   📍 Position template marquée en VERT")
        except Exception as e:
            print(f"   ⚠️ Erreur sauvegarde debug : {e}")
    
    def _save_debug_move_destination(self, player_pos, dest_pos, enemy_pos):
        """Sauvegarde un screenshot de debug montrant le déplacement prévu"""
        try:
            if not os.path.exists("debug_combat"):
                os.makedirs("debug_combat")
            
            import PIL.Image
            import PIL.ImageDraw
            
            # Prendre un screenshot d'une zone qui englobe perso, destination et ennemi
            px, py = player_pos
            dx, dy = dest_pos
            ex, ey = enemy_pos
            
            # Calculer la zone englobante
            min_x = min(px, dx, ex) - 100
            max_x = max(px, dx, ex) + 100
            min_y = min(py, dy, ey) - 100
            max_y = max(py, dy, ey) + 100
            
            region = (
                max(0, int(min_x)),
                max(0, int(min_y)),
                int(max_x - min_x),
                int(max_y - min_y)
            )
            
            screenshot = pyautogui.screenshot(region=region)
            img = screenshot.copy()
            draw = PIL.ImageDraw.Draw(img)
            
            # Ajuster les coordonnées relatives à la région
            px_rel = px - region[0]
            py_rel = py - region[1]
            dx_rel = dx - region[0]
            dy_rel = dy - region[1]
            ex_rel = ex - region[0]
            ey_rel = ey - region[1]
            
            # Dessiner le personnage en ROUGE
            draw.ellipse([px_rel - 15, py_rel - 15, px_rel + 15, py_rel + 15], outline="red", width=3)
            draw.line([px_rel - 20, py_rel, px_rel + 20, py_rel], fill="red", width=2)
            draw.line([px_rel, py_rel - 20, px_rel, py_rel + 20], fill="red", width=2)
            
            # Dessiner la destination en VERT
            draw.ellipse([dx_rel - 12, dy_rel - 12, dx_rel + 12, dy_rel + 12], outline="green", width=3)
            draw.line([dx_rel - 18, dy_rel, dx_rel + 18, dy_rel], fill="green", width=2)
            draw.line([dx_rel, dy_rel - 18, dx_rel, dy_rel + 18], fill="green", width=2)
            
            # Dessiner l'ennemi en BLEU
            draw.ellipse([ex_rel - 10, ey_rel - 10, ex_rel + 10, ey_rel + 10], outline="blue", width=2)
            
            # Ligne du perso vers la destination
            draw.line([px_rel, py_rel, dx_rel, dy_rel], fill="yellow", width=2)
            
            # Sauvegarder avec timestamp
            import time
            timestamp = int(time.time())
            debug_path = f"debug_combat/move_dest_{timestamp}.png"
            img.save(debug_path)
            print(f"   📸 DEBUG : Screenshot déplacement sauvegardé : {debug_path}")
            print(f"   🔴 ROUGE = Position perso détectée")
            print(f"   🟢 VERT = Point de clic (destination)")
            print(f"   🔵 BLEU = Ennemi le plus proche")
            print(f"   🟡 JAUNE = Ligne de déplacement")
        except Exception as e:
            print(f"   ⚠️ Erreur sauvegarde debug déplacement : {e}")

    def _find_red_circle_near_position(self, center, search_radius=150):
        cx, cy = center
        left = max(0, int(cx - search_radius))
        top = max(0, int(cy - search_radius))
        region = (left, top, search_radius*2, search_radius*2)
        result = self._detect_red_circle_cv2(region, offset=(left, top))
        if result:
            print(f"   🔴 Rond rouge trouvé près de {center} : {result}")
        else:
            print(f"   ⚠️ Aucun rond rouge trouvé dans un rayon de {search_radius}px autour de {center}")
        return result

    def _detect_red_circle_cv2(self, region, offset=(0,0), sort_by_dist_to=None):
        try:
            if not os.path.exists("debug_combat"): os.makedirs("debug_combat")
            img = pyautogui.screenshot(region=region)
            img_np = np.array(img)
            hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            
            # Plages de rouge larges
            lower1, upper1 = np.array([0, 60, 60]), np.array([15, 255, 255])
            lower2, upper2 = np.array([165, 60, 60]), np.array([180, 255, 255])
            mask = cv2.bitwise_or(cv2.inRange(hsv, lower1, upper1), cv2.inRange(hsv, lower2, upper2))
            
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.dilate(mask, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            candidates = []
            debug_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Critères stricts basés sur tes logs (3300px)
                if 1000 < area < 8000:
                    perimeter = cv2.arcLength(cnt, True)
                    if perimeter == 0: continue
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    cv2.drawContours(debug_img, [cnt], -1, (0, 255, 255), 1)

                    # Forme ronde exigée (>0.6)
                    if circularity > 0.60:
                        M = cv2.moments(cnt)
                        if M["m00"] == 0: continue
                        cx = int(M["m10"] / M["m00"]) + offset[0]
                        cy = int(M["m01"] / M["m00"]) + offset[1]
                        
                        candidates.append({'pos': (cx, cy), 'area': area, 'circ': circularity})
                        cv2.circle(debug_img, (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])), 5, (0, 255, 0), -1)

            cv2.imwrite("debug_combat/last_detection.jpg", debug_img)
            
            if not candidates: return None
            
            # Tri
            if sort_by_dist_to:
                px, py = sort_by_dist_to
                candidates.sort(key=lambda c: (c['pos'][0]-px)**2 + (c['pos'][1]-py)**2)
            else:
                # Score mixant circularité et taille idéale
                candidates.sort(key=lambda c: c['circ'] + (1.0 - abs(c['area']-3500)/3500.0), reverse=True)
            
            return candidates[0]['pos']
        except: return None

    # ------------------------------------------------------------------
    # UTILITAIRES & ARMES
    # ------------------------------------------------------------------
    def equip_drop_weapon(self):
        pt = self._get_manual_point("weapon_drop_point")
        if pt:
            print("🗡️ Équipement arme de drop...")
            pyautogui.doubleClick(pt)
            time.sleep(0.5)

    def equip_fishing_weapon(self):
        pt = self._get_manual_point("weapon_fish_point")
        if pt:
            print("🎣 Ré-équipement canne à pêche...")
            pyautogui.doubleClick(pt)
            time.sleep(0.5)

    def _find_template(self, name, confidence=0.7, grayscale=True):
        path = os.path.join("templates", name)
        if not os.path.exists(path):
            # Log silencieux si template manquant (normal pour certains)
            return None
        try:
            result = pyautogui.locateCenterOnScreen(path, confidence=confidence, grayscale=grayscale)
            return result
        except Exception as e:
            # Log silencieux pour les erreurs de pyautogui (template pas trouvé = normal)
            return None

    def _get_manual_point(self, key_name):
        try:
            if os.path.exists("manual_combat.json"):
                with open("manual_combat.json", "r") as f:
                    data = json.load(f)
                    if key_name == "pa_point" and "ap_point" in data: return tuple(data["ap_point"])
                    if key_name in data: return tuple(data[key_name])
        except: pass
        return None
    
    def _has_pa_pm_icons(self):
        return bool(self._find_template("icon_pa.png") or self._find_template("icon_pm.png"))

    def _can_attack(self, spell, target, pa_point):
        before = self._capture_pa_zone(pa_point)
        print("Test de portée...")
        pyautogui.click(spell)
        time.sleep(0.3)
        pyautogui.click(target)
        time.sleep(1.5) 
        after = self._capture_pa_zone(pa_point)
        if self._are_images_identical(before, after):
            print("❌ Hors de portée (PA inchangés)")
            pyautogui.rightClick() 
            return False
        print("✅ En portée")
        return True

    def _capture_pa_zone(self, point):
        x, y = point
        return pyautogui.screenshot(region=(int(x-15), int(y-15), 30, 30))

    def _are_images_identical(self, img1, img2):
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        diff = cv2.absdiff(arr1, arr2)
        return (np.count_nonzero(diff) / diff.size) < 0.01

    def _get_case_size(self):
        try:
            if os.path.exists("manual_combat.json"):
                with open("manual_combat.json", "r") as f:
                    return int(json.load(f).get("case_size_pixels", 55))
        except: return 55

    def _move_towards_target(self, target_coords):
        player_pos = self._get_player_position()
        if not player_pos:
            print("❌ Impossible de se déplacer : Position perso inconnue.")
            return False
            
        enemies = self._find_enemy_blue_circles()
        if not enemies:
            print("❌ Impossible de se déplacer : Aucun ennemi détecté.")
            return False
            
        px, py = player_pos
        closest = min(enemies, key=lambda e: (e[0]-px)**2 + (e[1]-py)**2)
        ex, ey = closest
        
        print(f"📍 Perso: {player_pos}, Ennemi: {closest}")
        
        dx = ex - px
        dy = ey - py
        dist = (dx**2 + dy**2)**0.5
        
        if dist < 20: return False 
        
        case_size = self._get_case_size()
        print(f"   📏 Taille case utilisée : {case_size}px")
        
        # AMÉLIORATION : Calculer la case de destination sur la grille
        # Au lieu de cliquer sur un point arbitraire, on calcule quelle case
        # est la meilleure pour se rapprocher de l'ennemi
        
        # Direction normalisée vers l'ennemi
        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
        else:
            return False
        
        # Calculer le nombre de cases à parcourir (max 1 case à la fois)
        # On veut se déplacer d'exactement 1 case vers l'ennemi
        move_dist = case_size
        
        # Calculer le point de destination en pixels
        step_x = int(dir_x * move_dist)
        step_y = int(dir_y * move_dist)
        dest_x = px + step_x
        dest_y = py + step_y
        
        # AMÉLIORATION : Aligner le point sur la grille de combat
        # Les cases de combat sont alignées sur une grille, on doit cliquer
        # sur le centre d'une case, pas n'importe où
        
        # Calculer la position relative du personnage dans sa case
        # On suppose que le personnage est au centre de sa case
        # On aligne la destination sur la grille en arrondissant au multiple de case_size le plus proche
        # Mais on part du centre de la case du personnage
        
        # Position de la case du personnage (arrondie)
        player_case_x = (px // case_size) * case_size + case_size // 2
        player_case_y = (py // case_size) * case_size + case_size // 2
        
        # Calculer la case de destination (1 case dans la direction de l'ennemi)
        dest_case_x = player_case_x + step_x
        dest_case_y = player_case_y + step_y
        
        # Aligner sur le centre de la case de destination
        dest_case_center_x = (dest_case_x // case_size) * case_size + case_size // 2
        dest_case_center_y = (dest_case_y // case_size) * case_size + case_size // 2
        
        # Utiliser le centre de la case comme point de clic
        final_dest_x = dest_case_center_x
        final_dest_y = dest_case_center_y
        
        print(f"🏃 Déplacement calculé :")
        print(f"   - Case personnage : ({player_case_x}, {player_case_y})")
        print(f"   - Case destination : ({final_dest_x}, {final_dest_y})")
        print(f"   - Distance : {move_dist}px (1 case)")
        
        # DEBUG : Screenshot du point de destination
        self._save_debug_move_destination(player_pos, (final_dest_x, final_dest_y), closest)
        
        pyautogui.moveTo(final_dest_x, final_dest_y)
        time.sleep(0.2)
        pyautogui.click()
        print("✅ Clic déplacement effectué sur le centre de la case.")
        return True

    def _find_enemy_blue_circles(self):
        """
        Trouve les ennemis. Stratégie multi-niveaux :
        1. YOLO Mobs (priorité si disponible)
        2. Détection par couleur (cercles bleus - fallback)
        """
        # 1. YOLO Mobs (Priorité si disponible)
        if self.mobs_model:
            try:
                screen_w, screen_h = pyautogui.size()
                search_w = screen_w - 200
                search_h = screen_h - 180
                region = (0, 0, search_w, search_h)
                
                screenshot = pyautogui.screenshot(region=region)
                img_np = np.array(screenshot)
                results = self.mobs_model(img_np, conf=0.35, verbose=False)
                
                enemies = []
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        center_x = int((x1 + x2) / 2) + region[0]
                        center_y = int((y1 + y2) / 2) + region[1]
                        confidence = float(box.conf[0].cpu().numpy())
                        enemies.append((center_x, center_y))
                        print(f"   ✅ YOLO Mobs : Ennemi détecté en ({center_x}, {center_y}) avec confiance {confidence:.2f}")
                
                if enemies:
                    return enemies
            except Exception as e:
                print(f"   ⚠️ Erreur détection YOLO Mobs : {e}")
        
        # 2. Fallback : Détection par couleur (cercles bleus)
        screen_w, screen_h = pyautogui.size()
        search_w = screen_w - 200
        search_h = screen_h - 180
        region = (0, 0, search_w, search_h)
        try:
            img = pyautogui.screenshot(region=region)
            img_np = np.array(img)
            hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            lower_blue = np.array([100, 100, 100])
            upper_blue = np.array([140, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            enemies = []
            for cnt in contours:
                if 200 < cv2.contourArea(cnt) < 50000:
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"]) + region[0]
                        cy = int(M["m01"] / M["m00"]) + region[1]
                        enemies.append((cx, cy))
            if enemies:
                print(f"   🔵 Détection couleur : {len(enemies)} ennemi(s) trouvé(s)")
            return enemies
        except: return []
