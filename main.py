import time
import json
import os
from vision import Vision
from navigation import Navigation
from combat import Combat

CIRCUIT_STATE_FILE = "circuit_state.json"

def save_circuit_state(current_pos, step_index, route_list, circuit_name=None):
    """Sauvegarde l'état actuel du circuit"""
    state = {
        "current_pos": current_pos,
        "step_index": step_index,
        "route_list": route_list,
        "circuit_name": circuit_name
    }
    try:
        with open(CIRCUIT_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        print(f"💾 État sauvegardé : Position {current_pos}, Étape {step_index+1}/{len(route_list)}")
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde état : {e}")

def load_circuit_state():
    """Charge l'état sauvegardé du circuit"""
    if not os.path.exists(CIRCUIT_STATE_FILE):
        return None
    try:
        with open(CIRCUIT_STATE_FILE, "r") as f:
            state = json.load(f)
        print(f"📂 État chargé : Position {state.get('current_pos')}, Étape {state.get('step_index', 0)+1}")
        return state
    except Exception as e:
        print(f"⚠️ Erreur chargement état : {e}")
        return None

def process_fishing_session(bot_nav, bot_combat, fish_points, stop_event, wait_time=7.5, max_wait=25.0, spell_count=3):
    """
    Gère une session de pêche complète sur une liste de points.
    wait_time: temps d'attente (sec) après chaque clic sur un poisson.
    max_wait: temps d'attente (sec) après le DERNIER poisson de la map
              (utile pour laisser finir la pêche avant de changer de map).
    spell_count: Nombre de lancers par tour (pour le combat)
    """
    if not fish_points:
        return

    print(f"🔎 {len(fish_points)} spots de pêche identifiés. Début du cycle.")
    
    for i, point in enumerate(fish_points):
        if stop_event and stop_event.is_set(): 
            return
        
        # Vérification avant chaque action si on est déjà en combat (agression immédiate)
        # On met à jour l'état de combat (détecte début/fin)
        bot_combat.check_combat_start()
        
        # Boucle tant qu'on est en combat (on ne pêche PAS tant que combat pas fini)
        if bot_combat.in_combat:
            print("⚔️ EN COMBAT ! (Confirmé)")
            # On reste dans la boucle combat tant que l'état interne dit qu'on est en combat
            while bot_combat.in_combat:
                if stop_event and stop_event.is_set(): 
                    return
                
                # On tente de jouer un tour
                bot_combat.handle_combat_turn()
                
                # On vérifie à nouveau l'état (pour détecter la fin de combat via bouton Fermer)
                bot_combat.check_combat_start()
                    
                time.sleep(0.5)
            
            print("⏩ Combat terminé. Passage au spot suivant pour sécurité.")
            continue
        
        # --- TENTATIVE UNIQUE ---
        print(f"🐟 Spot {i+1}/{len(fish_points)} : Analyse & Pêche...")
        did_fish = bot_nav.click_fish(point)
        
        if not did_fish:
            # Aucun menu "Pêcher" détecté -> le poisson a probablement disparu.
            # On attend quand même un petit délai pour ne pas enchaîner trop vite.
            print("⏩ Aucun poisson pêché sur ce spot, pause courte (2s) avant le suivant.")
            for _ in range(20):  # 2s en pas de 0.1s pour garder la réactivité à l'arrêt
                if stop_event and stop_event.is_set():
                    return
                time.sleep(0.1)
            continue
        
        # Temps d'attente : normal ou allongé si dernier poisson
        current_wait = max_wait if i == len(fish_points) - 1 else wait_time
        print(f"⏳ Attente pêche : {current_wait}s")
        steps = int(current_wait * 10)
        for _ in range(steps): 
            if stop_event and stop_event.is_set(): 
                return
            time.sleep(0.1)
            
        # Vérification si un niveau a été passé (popup bloquant)
        bot_nav.check_levelup()
            
    print("✅ Tous les spots de cette map ont été traités.")

def main(start_pos=None, route_list=None, stop_event=None, infinite_loop=False,
         fishing_wait_time=7.5, max_map_wait=25.0, spell_count=3, resume_from_state=False, circuit_name=None):
    """
    Fonction principale du bot.
    start_pos: Position de départ [x, y]
    route_list: Liste ordonnée des maps à visiter [[x1, y1], [x2, y2], ...]
    stop_event: Pour l'arrêt d'urgence
    infinite_loop: Si True, recommence la route à l'infini
    fishing_wait_time: Temps d'attente (sec) après chaque clic de pêche
    max_map_wait: Temps d'attente (sec) après le DERNIER poisson de la map avant déplacement
    spell_count: réservé pour la logique de combat (non utilisée dans cette version)
    resume_from_state: Si True, reprend depuis l'état sauvegardé
    circuit_name: Nom du circuit (pour la sauvegarde)
    """
    # Initialisation
    bot_vision = Vision()
    bot_nav = Navigation()
    bot_combat = Combat()

    print("=== BOT DOFUS RÉTRO - NAVIGATION INTELLIGENTE (YOLO AI) ===")
    print("Lancement dans 3 secondes... Basculez sur la fenêtre de jeu !")
    
    for _ in range(30):
        if stop_event and stop_event.is_set():
            print("Arrêt demandé avant le lancement.")
            return
        time.sleep(0.1)
    
    # Équipement de la dragodinde au démarrage
    bot_nav.equip_dragodinde()

    # Gestion des arguments par défaut
    if start_pos is None: current_pos = [12, 4]
    else: current_pos = list(start_pos)
        
    if route_list is None:
        # Exemple par défaut
        ROUTE = [[11, 4], [10, 4]]
    else:
        ROUTE = route_list

    # Reprendre depuis l'état sauvegardé si demandé
    start_step_index = 0
    if resume_from_state:
        saved_state = load_circuit_state()
        if saved_state:
            # Vérifier que la route correspond
            if saved_state.get("route_list") == ROUTE:
                current_pos = saved_state.get("current_pos", current_pos)
                start_step_index = saved_state.get("step_index", 0)
                print(f"🔄 Reprise depuis l'état sauvegardé : Position {current_pos}, Étape {start_step_index+1}/{len(ROUTE)}")
            else:
                print("⚠️ La route sauvegardée ne correspond pas. Démarrage normal.")

    # Liste des maps où le bot doit pêcher (toutes celles de la route sont considérées comme maps de pêche potentielle)
    FISHING_MAPS = ROUTE 

    print(f"Départ : {current_pos}")
    print(f"Route à suivre : {ROUTE}")
    print(f"Mode boucle infinie : {'OUI' if infinite_loop else 'NON'}")

    while True: # Boucle infinie potentielle
        # Pour chaque étape de la route
        for step_index, step_target in enumerate(ROUTE):
            # Si on reprend depuis un état sauvegardé, on saute les étapes déjà faites
            if step_index < start_step_index:
                continue
            target_pos = list(step_target)
            print(f"\n--- CAP SUR L'ÉTAPE {step_index+1}/{len(ROUTE)} : {target_pos} ---")

            # On réinitialise le flag de pêche au début de chaque étape si on est déjà sur une map de pêche
            fishing_done = False

            # Boucle de navigation vers l'étape courante
            while current_pos != target_pos:
                # VERIFICATION ARRET
                if stop_event and stop_event.is_set():
                    print("🛑 Arrêt du bot demandé par l'utilisateur.")
                    return

                # ⚠️ PRIORITÉ ABSOLUE : Vérifier le combat AVANT toute autre action
                bot_combat.check_combat_start(debug=True)  # Mode debug activé
                
                # Si on est en combat, on gère le combat et on ne fait RIEN d'autre
                if bot_combat.in_combat:
                    print("⚔️ EN COMBAT ! Gestion du combat en priorité...")
                    while bot_combat.in_combat:
                        if stop_event and stop_event.is_set(): 
                            return
                        bot_combat.handle_combat_turn()
                        bot_combat.check_combat_start()
                        time.sleep(0.5)
                    print("✅ Combat terminé. Reprise de la navigation.")
                    continue  # On reprend la boucle de navigation

                print(f"\n--- Actuellement en {current_pos}. Prochaine étape : {target_pos} ---")
                
                # --- PÊCHE SUR LE CHEMIN ---
                # On ne pêche que si on n'a pas déjà pêché sur CETTE map
                if list(current_pos) in [list(m) for m in FISHING_MAPS] and not fishing_done:
                    print("🎣 Map d'intérêt atteinte ! Vérification poissons...")
                    fish_points = bot_vision.find_fish(current_pos)
                    
                    if stop_event and stop_event.is_set(): return

                    if fish_points:
                        process_fishing_session(
                            bot_nav,
                            bot_combat,
                            fish_points, 
                            stop_event, 
                            wait_time=fishing_wait_time, 
                            max_wait=max_map_wait,
                            spell_count=spell_count
                        )
                    else:
                        print("Pas de poissons ici pour le moment.")
                    
                    fishing_done = True # On a fini pour cette map
                
                # 1. Calcul direction vers l'étape courante
                direction = bot_nav.get_direction(tuple(current_pos), tuple(target_pos))
                
                if not direction:
                    break

                print(f"Direction calculée : {direction}")

                # 2. Déplacement
                map_change_success = False
                
                # A. Vérification Point Manuel (Priorité Absolue)
                manual_point = bot_nav.get_manual_point(current_pos, direction)
                
                potential_points = []
                if manual_point:
                    print("🎯 Utilisation du point manuel forcé.")
                    potential_points.append(manual_point)
                else:
                    # B. IA (YOLO) - Priorité 2
                    print("Recherche IA (YOLO)...")
                    sun_point = bot_vision.find_sun(direction)
                    if sun_point: potential_points.append(sun_point)
                    
                    # C. Grille
                    grid_points = bot_nav.get_grid_points(direction)
                    potential_points.extend(grid_points)

                for i, point in enumerate(potential_points):
                    if stop_event and stop_event.is_set(): return
                    
                    # Capture avant
                    img_before = bot_vision.take_screenshot()
                    
                    # Clic
                    bot_nav.click_point(point)
                    
                    # Attente changement map
                    start_time = time.time()
                    changed = False
                    while time.time() - start_time < 6.0:
                        if stop_event and stop_event.is_set(): return
                        time.sleep(0.5)
                        img_current = bot_vision.take_screenshot()
                        if bot_vision.has_map_changed(img_before, img_current):
                            changed = True
                            break
                    
                    if changed:
                        print("SUCCÈS ! Changement de map.")
                        map_change_success = True
                        
                        # Sauvegarde pos avant modif pour vérification
                        prev_pos = list(current_pos)
                        
                        if direction == "DROITE": current_pos[0] += 1
                        elif direction == "GAUCHE": current_pos[0] -= 1
                        elif direction == "HAUT": current_pos[1] -= 1
                        elif direction == "BAS": current_pos[1] += 1
                        
                        # --- CORRECTIONS SPÉCIALES (Téléportations / Maps Forcées) ---
                        forced_next = bot_nav.get_forced_next_map(prev_pos, direction)
                        if forced_next:
                            current_pos = forced_next
                            print(f"⚠️ SAUT DE MAP DÉTECTÉ (Manuel) : Position corrigée vers {current_pos}")
                        
                        # Sauvegarder l'état après chaque changement de map
                        save_circuit_state(current_pos, step_index, ROUTE, circuit_name)
                        
                        time.sleep(1.0)
                        
                        # NOUVELLE MAP -> On reset le flag de pêche pour la prochaine map
                        fishing_done = False
                        break
                
                if not map_change_success:
                    print("CRITIQUE : Impossible de bouger. Arrêt.")
                    return

            # --- ARRIVÉE SUR UNE ÉTAPE ---
            # Note : On ne pêche PLUS ici, car la boucle while traite déjà la pêche sur le chemin
            # Si l'étape est atteinte, c'est que current_pos == target_pos.
            # Au prochain tour de boucle 'for', on repartira de cette position
            # et le 'while' suivant traitera la pêche si nécessaire.
            print(f"✅ Étape {target_pos} atteinte !")
            # Sauvegarder l'état après avoir atteint une étape
            save_circuit_state(current_pos, step_index, ROUTE, circuit_name)
            
        # Fin de la route
        if not infinite_loop:
            print("=== TRAJET TERMINÉ ===")
            # Supprimer l'état sauvegardé à la fin du circuit
            if os.path.exists(CIRCUIT_STATE_FILE):
                try:
                    os.remove(CIRCUIT_STATE_FILE)
                    print("🗑️ État sauvegardé supprimé (circuit terminé)")
                except:
                    pass
            break
        else:
            print("🔄 Fin de la route. Mode boucle infinie : On recommence au début !")
            # Réinitialiser l'index de départ pour la prochaine boucle
            start_step_index = 0

if __name__ == "__main__":
    main()
