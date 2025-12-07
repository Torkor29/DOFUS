import customtkinter as ctk
import threading
import sys
import json
import os
import time
import pyautogui
import cv2
from tkinter import messagebox, filedialog

import main as bot_main
import train_fish
import collect_player_data
import prepare_player_dataset
import train_player

# --- Configuration Visuelle ---
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue") 

# --- Fichiers de données ---
SETTINGS_FILE = "bot_settings.json"
CIRCUITS_FILE = "circuits.json"
SCREEN_PROFILES_FILE = "screen_profiles.json"
MOVES_FILE = "manual_moves.json"
FISH_FILE = "manual_fishing.json"
COMBAT_FILE = "manual_combat.json"
COMBAT_MOVES_FILE = "manual_combat_moves.json"

class PrintRedirector:
    """Redirige les prints vers la console de l'interface"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout

    def write(self, text):
        try:
            self.text_widget.after(0, self._append_text, text)
        except:
            pass

    def _append_text(self, text):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", text)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class DofusBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Dofus Fishing Bot AI - Manager Pro")
        self.geometry("1100x800")
        
        # Variables d'état
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.current_circuit_name = ctk.StringVar(value="Non enregistré")
        self.current_screen_profile = ctk.StringVar(value="Profil par défaut")

        # Chargement des données
        self.settings = self.load_json(SETTINGS_FILE, default={
            "start_x": "12", "start_y": "4",
            "route_list": "12,4; 11,4; 10,4",
            "infinite_loop": False,
            "fishing_wait_time": "7.5",
            "max_map_wait": "25.0",
            "combat_spell_count": "3"
        })
        self.circuits = self.load_json(CIRCUITS_FILE, default={})
        self.screen_profiles = self.load_json(SCREEN_PROFILES_FILE, default={})
        self.templates = self.load_json("templates_config.json", default={
            "Personnage": {
                "class_id": 0,
                "class_name": "personnage",
                "folder": "Personnage",
                "description": "Détection du personnage joueur"
            },
            "Mobs": {
                "class_id": 1,
                "class_name": "mobs",
                "folder": "Mobs",
                "description": "Détection des ennemis/mobs en combat"
            }
        })
        self.current_template = ctk.StringVar(value="Personnage")

        # --- LAYOUT PRINCIPAL ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Menu)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="DOFUS AI\nMANAGER", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Menu Buttons
        self.create_sidebar_button("Tableau de Bord", "dashboard", 1)
        self.create_sidebar_button("Circuits & Routes", "circuits", 2)
        self.create_sidebar_button("Profils d'écran", "screens", 3)
        self.create_sidebar_button("Calibrage Manuel", "calib", 4)
        self.create_sidebar_button("Données & Map", "manage", 5)
        self.create_sidebar_button("Templates IA", "templates", 6)
        self.create_sidebar_button("Annoter", "annotate", 7)
        self.create_sidebar_button("Entraînement IA", "train", 8)

        # 2. Main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        
        # Initialisation des Vues
        self.frames = {}
        self.create_dashboard_view()
        self.create_circuits_view()
        self.create_screens_view()
        self.create_calib_view()
        self.create_manage_view()
        self.create_templates_view()
        self.create_annotate_view()
        self.create_train_view()
        
        # Variables pour la collecte de données personnage
        self.player_collector = collect_player_data.PlayerDataCollector()
        
        # Sauvegarder la config des templates si elle n'existe pas
        if not os.path.exists("templates_config.json"):
            self.save_json("templates_config.json", self.templates)

        self.show_frame("dashboard")

    def load_json(self, filepath, default):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_json(self, filepath, data):
        with open(filepath, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def create_sidebar_button(self, text, frame_name, row):
        btn = ctk.CTkButton(self.sidebar, text=text, height=40, corner_radius=10, 
                            fg_color="transparent", border_width=2, border_color="#3B8ED0", text_color=("gray10", "#DCE4EE"),
                            hover_color=("#3B8ED0", "#1F6AA5"),
                            anchor="w", command=lambda: self.show_frame(frame_name))
        btn.grid(row=row, column=0, padx=20, pady=5, sticky="ew")

    def show_frame(self, name):
        for frame in self.frames.values(): frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True, padx=20, pady=20)
        if name == "manage": 
            self.refresh_manage_view()
        elif name == "annotate":
            # Recharger les images et afficher la première
            self.annotate_load_images()

    # ----------------------------------------------------------------
    # 1. TABLEAU DE BORD
    # ----------------------------------------------------------------
    def create_dashboard_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["dashboard"] = frame
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header, text="Tableau de Bord", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        self.lbl_status_run = ctk.CTkLabel(header, text="STOPPÉ", text_color="red", font=ctk.CTkFont(weight="bold"))
        self.lbl_status_run.pack(side="right", padx=10)

        # Controls
        ctrl_frame = ctk.CTkFrame(frame, height=80)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_start = ctk.CTkButton(ctrl_frame, text="▶ LANCER LE BOT", fg_color="#2CC985", hover_color="#229966", 
                                       height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.start_bot)
        self.btn_start.pack(side="left", padx=10, pady=15, expand=True, fill="x")

        self.btn_resume = ctk.CTkButton(ctrl_frame, text="🔄 REPRENDRE CIRCUIT", fg_color="#FFA500", hover_color="#CC8800", 
                                        height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.resume_bot)
        self.btn_resume.pack(side="left", padx=10, pady=15, expand=True, fill="x")

        self.btn_stop = ctk.CTkButton(ctrl_frame, text="⏹ ARRÊTER", fg_color="#FF4D4D", hover_color="#CC0000", state="disabled",
                                      height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.stop_bot)
        self.btn_stop.pack(side="left", padx=10, pady=15, expand=True, fill="x")

        # Info Courante
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10)
        self.lbl_current_config = ctk.CTkLabel(info_frame, text="Configuration chargée : Dernière session", text_color="gray")
        self.lbl_current_config.pack(side="left")

        # Console
        self.console_text = ctk.CTkTextbox(frame, font=("Consolas", 12))
        self.console_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.console_text.configure(state="disabled")

        sys.stdout = PrintRedirector(self.console_text)

    # ----------------------------------------------------------------
    # 2. CIRCUITS & ROUTES
    # ----------------------------------------------------------------
    def create_circuits_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["circuits"] = frame
        
        # -- Haut : Gestion des circuits enregistrés --
        top_bar = ctk.CTkFrame(frame)
        top_bar.pack(fill="x", padx=10, pady=10)
        
        # Ligne 1 : circuits
        ctk.CTkLabel(top_bar, text="Circuit :").pack(side="left", padx=(10,2))
        self.combo_circuits = ctk.CTkComboBox(top_bar, values=list(self.circuits.keys()), width=180, command=self.on_circuit_select)
        self.combo_circuits.pack(side="left", padx=(0,10))
        
        ctk.CTkButton(top_bar, text="Charger", width=80, command=self.load_selected_circuit).pack(side="left", padx=3)
        ctk.CTkButton(top_bar, text="Nouveau...", width=110, fg_color="#E0A800", hover_color="#B08800", command=self.save_as_new_circuit).pack(side="left", padx=3)
        ctk.CTkButton(top_bar, text="Mettre à jour", width=100, command=self.update_current_circuit).pack(side="left", padx=3)
        ctk.CTkButton(top_bar, text="Renommer", width=95, command=self.rename_circuit).pack(side="left", padx=3)
        ctk.CTkButton(top_bar, text="🗑", width=40, fg_color="red", hover_color="darkred", command=self.delete_circuit).pack(side="left", padx=3)

        # Sélecteur de profil d'écran directement sur la même barre
        ctk.CTkLabel(top_bar, text="Profil écran :", padx=10).pack(side="left", padx=(20,2))
        self.combo_circuit_screen = ctk.CTkComboBox(
            top_bar, 
            width=160, 
            values=list(self.screen_profiles.keys()),
            command=self.on_circuit_screen_change
        )
        self.combo_circuit_screen.set(self.current_screen_profile.get())
        self.combo_circuit_screen.pack(side="left", padx=(0,5))

        # -- Corps : Édition (présentation en sections propres) --
        editor_frame = ctk.CTkScrollableFrame(frame, label_text="Configuration du Circuit", label_font=ctk.CTkFont(size=18, weight="bold"))
        editor_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # SECTION NAVIGATION
        section_nav = ctk.CTkFrame(editor_frame)
        section_nav.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(section_nav, text="Navigation", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=5, pady=(5,2))
        nav_inner = ctk.CTkFrame(section_nav, fg_color="transparent")
        nav_inner.pack(fill="x", padx=10, pady=(0,10))

        ctk.CTkLabel(nav_inner, text="Position Départ (X, Y)").grid(row=0, column=0, sticky="w")
        pos_row = ctk.CTkFrame(nav_inner, fg_color="transparent")
        pos_row.grid(row=0, column=1, sticky="w", padx=5)
        self.entry_start_x = ctk.CTkEntry(pos_row, width=60)
        self.entry_start_x.pack(side="left", padx=2)
        self.entry_start_x.insert(0, self.settings["start_x"])
        self.entry_start_y = ctk.CTkEntry(pos_row, width=60)
        self.entry_start_y.pack(side="left", padx=2)
        self.entry_start_y.insert(0, self.settings["start_y"])

        # SECTION PÊCHE
        section_fish = ctk.CTkFrame(editor_frame)
        section_fish.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(section_fish, text="Pêche", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=5, pady=(5,2))
        fish_inner = ctk.CTkFrame(section_fish, fg_color="transparent")
        fish_inner.pack(fill="x", padx=10, pady=(0,10))

        ctk.CTkLabel(fish_inner, text="Attente après pêche (s)").grid(row=0, column=0, sticky="w")
        self.entry_wait_time = ctk.CTkEntry(fish_inner, width=80)
        self.entry_wait_time.grid(row=0, column=1, sticky="w", padx=5)
        self.entry_wait_time.insert(0, self.settings.get("fishing_wait_time", "7.5"))

        ctk.CTkLabel(fish_inner, text="Pause chgmt map (si pêche) (s)").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.entry_max_map_wait = ctk.CTkEntry(fish_inner, width=80)
        self.entry_max_map_wait.grid(row=1, column=1, sticky="w", padx=5, pady=(5,0))
        self.entry_max_map_wait.insert(0, self.settings.get("max_map_wait", "25.0"))

        # SECTION COMBAT
        section_cbt = ctk.CTkFrame(editor_frame)
        section_cbt.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(section_cbt, text="Combat", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=5, pady=(5,2))
        cbt_inner = ctk.CTkFrame(section_cbt, fg_color="transparent")
        cbt_inner.pack(fill="x", padx=10, pady=(0,10))

        ctk.CTkLabel(cbt_inner, text="Nb lancers du sort par tour").grid(row=0, column=0, sticky="w")
        self.entry_spell_count = ctk.CTkEntry(cbt_inner, width=60)
        self.entry_spell_count.grid(row=0, column=1, sticky="w", padx=5)
        self.entry_spell_count.insert(0, self.settings.get("combat_spell_count", "3"))

        # Route
        route_frame = ctk.CTkFrame(editor_frame)
        route_frame.pack(fill="both", expand=False, pady=5, padx=5)
        ctk.CTkLabel(route_frame, text="Route (liste des maps)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=5, pady=(5,0))
        ctk.CTkLabel(route_frame, text="Format: x,y; x,y; x,y  (le bot pêchera sur chaque map de la route)", text_color="gray", font=("Arial", 10)).pack(anchor="w", padx=5)
        
        self.text_route = ctk.CTkTextbox(route_frame, height=150)
        self.text_route.pack(fill="x", pady=5, padx=5)
        self.text_route.insert("0.0", self.settings["route_list"])

        self.switch_infinite = ctk.CTkSwitch(editor_frame, text="Boucle Infinie (Recommencer à la fin)")
        self.switch_infinite.pack(pady=10, anchor="w")
        if self.settings["infinite_loop"]: self.switch_infinite.select()

        # Outils Map Rapide
        tools_frame = ctk.CTkFrame(frame, border_width=1, border_color="gray")
        tools_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(tools_frame, text="Inspecteur de Map (Calibration)").pack(side="left", padx=10)
        self.entry_inspect_map = ctk.CTkEntry(tools_frame, placeholder_text="ex: 12,4", width=100)
        self.entry_inspect_map.pack(side="left", padx=5)
        ctk.CTkButton(tools_frame, text="Vérifier Données", command=self.check_map_data).pack(side="left", padx=5)
        self.lbl_map_info = ctk.CTkLabel(tools_frame, text="-", text_color="gray")
        self.lbl_map_info.pack(side="left", padx=10)

    def on_circuit_select(self, choice):
        # Juste pour UX, le chargement est manuel via bouton "Charger" pour éviter pertes accidentelles
        pass

    def load_selected_circuit(self):
        name = self.combo_circuits.get()
        if name in self.circuits:
            data = self.circuits[name]
            # Update UI
            self.entry_start_x.delete(0, "end"); self.entry_start_x.insert(0, data.get("start_x", ""))
            self.entry_start_y.delete(0, "end"); self.entry_start_y.insert(0, data.get("start_y", ""))
            self.entry_wait_time.delete(0, "end"); self.entry_wait_time.insert(0, data.get("fishing_wait_time", ""))
            self.entry_max_map_wait.delete(0, "end"); self.entry_max_map_wait.insert(0, data.get("max_map_wait", ""))
            self.entry_spell_count.delete(0, "end"); self.entry_spell_count.insert(0, data.get("combat_spell_count", ""))
            self.text_route.delete("0.0", "end"); self.text_route.insert("0.0", data.get("route_list", ""))
            
            if data.get("infinite_loop", False): 
                self.switch_infinite.select()
            else: 
                self.switch_infinite.deselect()

            # Profil d'écran associé au circuit (si présent)
            screen_prof = data.get("screen_profile")
            if screen_prof and screen_prof in self.screen_profiles:
                self.current_screen_profile.set(screen_prof)
                self.refresh_screen_profile_ui()
                # Appliquer directement les calibrages de ce profil
                self.apply_screen_profile()
            else:
                # Compatibilité ancienne version : charger les snapshots manuels stockés dans le circuit
                moves = data.get("manual_moves")
                if moves is not None:
                    self.save_json(MOVES_FILE, moves)
                fish = data.get("manual_fishing")
                if fish is not None:
                    self.save_json(FISH_FILE, fish)
                combat = data.get("manual_combat")
                if combat is not None:
                    self.save_json(COMBAT_FILE, combat)

            self.current_circuit_name.set(name)
            self.lbl_current_config.configure(text=f"Configuration chargée : {name}")
            messagebox.showinfo("Chargé", f"Le circuit '{name}' a été chargé dans l'éditeur.")
        else:
            messagebox.showerror("Erreur", "Circuit introuvable.")

    def save_as_new_circuit(self):
        dialog = ctk.CTkInputDialog(text="Nom du circuit :", title="Sauvegarder Sous")
        name = dialog.get_input()
        if name:
            self.save_current_ui_to_dict(name)
            self.combo_circuits.configure(values=list(self.circuits.keys()))
            self.combo_circuits.set(name)
            self.current_circuit_name.set(name)
            self.lbl_current_config.configure(text=f"Configuration chargée : {name}")
            # Mettre aussi à jour la combo de profil pour refléter l'association
            if "screen_profile" in self.circuits[name]:
                self.current_screen_profile.set(self.circuits[name]["screen_profile"])
                if hasattr(self, "combo_circuit_screen"):
                    self.combo_circuit_screen.configure(values=list(self.screen_profiles.keys()))
                    self.combo_circuit_screen.set(self.circuits[name]["screen_profile"])

    def update_current_circuit(self):
        name = self.combo_circuits.get()
        if name in self.circuits:
            if messagebox.askyesno("Confirmer", f"Écraser le circuit '{name}' ?"):
                self.save_current_ui_to_dict(name)
        else:
            messagebox.showerror("Erreur", "Ce circuit n'existe pas, utilisez 'Sauvegarder Nouveau'")

    def delete_circuit(self):
        name = self.combo_circuits.get()
        if name in self.circuits and messagebox.askyesno("Confirmer", f"Supprimer '{name}' ?"):
            del self.circuits[name]
            self.save_json(CIRCUITS_FILE, self.circuits)
            self.combo_circuits.configure(values=list(self.circuits.keys()))
            if self.circuits: self.combo_circuits.set(list(self.circuits.keys())[0])
            else: self.combo_circuits.set("")

    def rename_circuit(self):
        """Renomme le circuit sélectionné sans perdre sa configuration/calibrages"""
        old_name = self.combo_circuits.get()
        if not old_name or old_name not in self.circuits:
            messagebox.showerror("Erreur", "Aucun circuit valide sélectionné.")
            return

        dialog = ctk.CTkInputDialog(text=f"Nouveau nom pour '{old_name}' :", title="Renommer le circuit")
        new_name = dialog.get_input()
        if not new_name or new_name == old_name:
            return
        if new_name in self.circuits:
            messagebox.showerror("Erreur", "Un circuit porte déjà ce nom.")
            return

        # Renommer la clé dans le dictionnaire
        self.circuits[new_name] = self.circuits.pop(old_name)
        self.save_json(CIRCUITS_FILE, self.circuits)

        # Mettre à jour la sélection et les libellés
        self.combo_circuits.configure(values=list(self.circuits.keys()))
        self.combo_circuits.set(new_name)
        self.current_circuit_name.set(new_name)
        self.lbl_current_config.configure(text=f"Configuration chargée : {new_name}")


    def save_current_ui_to_dict(self, name):
        # 1. Sauvegarde des paramètres de route / options
        data = {
            "start_x": self.entry_start_x.get(),
            "start_y": self.entry_start_y.get(),
            "fishing_wait_time": self.entry_wait_time.get(),
            "max_map_wait": self.entry_max_map_wait.get(),
            "combat_spell_count": self.entry_spell_count.get(),
            "route_list": self.text_route.get("1.0", "end-1c"),
            "infinite_loop": self.switch_infinite.get() == 1,
            # Nouveau : le circuit sait quel profil d'écran il utilise
            "screen_profile": self.current_screen_profile.get()
        }

        # 2. (Compat) Snapshot des calibrages actuels pour ce circuit
        # Gardé pour ne pas casser d'anciens circuits, mais le chemin normal
        # passera par les profils d'écran.
        data["manual_moves"] = self.load_json(MOVES_FILE, {})
        data["manual_fishing"] = self.load_json(FISH_FILE, {})
        data["manual_combat"] = self.load_json(COMBAT_FILE, {})

        self.circuits[name] = data
        self.save_json(CIRCUITS_FILE, self.circuits)
        
        # On sauvegarde aussi en tant que "current settings" pour le run
        self.settings.update(data)
        self.save_json(SETTINGS_FILE, self.settings)

    def on_circuit_screen_change(self, choice):
        """Quand on change de profil écran depuis l'onglet circuits"""
        if choice in self.screen_profiles:
            self.current_screen_profile.set(choice)
            # si un circuit est sélectionné on met aussi à jour son champ screen_profile en mémoire (pas encore sauvegardé)
            name = self.combo_circuits.get()
            if name in self.circuits:
                self.circuits[name]["screen_profile"] = choice

    # ----------------------------------------------------------------
    # 2bis. PROFILS D'ÉCRAN
    # ----------------------------------------------------------------
    def create_screens_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["screens"] = frame

        ctk.CTkLabel(frame, text="Profils d'écran", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top, text="Profil actif :").pack(side="left", padx=10)
        self.combo_screen = ctk.CTkComboBox(top, width=200, command=self.on_screen_profile_change)
        self.combo_screen.pack(side="left", padx=5)

        ctk.CTkButton(top, text="Appliquer au bot", command=self.apply_screen_profile).pack(side="left", padx=10)

        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.pack(fill="x", padx=10, pady=(0,10))
        ctk.CTkButton(btns, text="Nouveau Profil...", width=140, command=self.create_screen_profile).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Dupliquer", width=100, command=self.duplicate_screen_profile).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Renommer", width=100, command=self.rename_screen_profile).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Supprimer", width=100, fg_color="red", hover_color="darkred", command=self.delete_screen_profile).pack(side="left", padx=5)

        self.lbl_screen_info = ctk.CTkLabel(frame, text="-", text_color="gray")
        self.lbl_screen_info.pack(pady=5)

        # Initialisation des profils à partir des fichiers actuels si vide
        if not self.screen_profiles:
            self.bootstrap_default_screen_profile()
        self.refresh_screen_profile_ui()

    def bootstrap_default_screen_profile(self):
        """Crée un profil 'Par défaut' à partir des fichiers manuels actuels"""
        try:
            w, h = pyautogui.size()
        except:
            w, h = (0, 0)
        self.screen_profiles["Par défaut"] = {
            "resolution": [w, h],
            "moves": self.load_json(MOVES_FILE, {}),
            "fishing": self.load_json(FISH_FILE, {}),
            "combat": self.load_json(COMBAT_FILE, {})
        }
        self.save_json(SCREEN_PROFILES_FILE, self.screen_profiles)

    def refresh_screen_profile_ui(self):
        names = list(self.screen_profiles.keys())
        if not names:
            self.combo_screen.configure(values=["Aucun"])
            self.combo_screen.set("Aucun")
            self.lbl_screen_info.configure(text="Aucun profil enregistré.")
            return
        self.combo_screen.configure(values=names)
        current = self.current_screen_profile.get()
        if current not in names:
            current = names[0]
            self.current_screen_profile.set(current)
        self.combo_screen.set(current)

        prof = self.screen_profiles[current]
        res = prof.get("resolution", ["?", "?"])
        mv = len(prof.get("moves", {}))
        fi = len(prof.get("fishing", {}))
        cb = len(prof.get("combat", {}))
        self.lbl_screen_info.configure(
            text=f"Résolution: {res[0]}x{res[1]}  |  Nav: {mv} calibrages  |  Pêche: {fi} maps  |  Combat: {len(prof.get('combat', {}))} points"
        )

    def on_screen_profile_change(self, choice):
        if choice in self.screen_profiles:
            self.current_screen_profile.set(choice)
            self.refresh_screen_profile_ui()

    def apply_screen_profile(self):
        """Écrit le profil d'écran actif dans les fichiers manuels utilisés par le bot"""
        name = self.current_screen_profile.get()
        if name not in self.screen_profiles:
            messagebox.showerror("Erreur", "Profil d'écran introuvable.")
            return
        prof = self.screen_profiles[name]
        self.save_json(MOVES_FILE, prof.get("moves", {}))
        self.save_json(FISH_FILE, prof.get("fishing", {}))
        self.save_json(COMBAT_FILE, prof.get("combat", {}))
        messagebox.showinfo("Profil appliqué", f"Les calibrages du profil '{name}' ont été appliqués.")

    def create_screen_profile(self):
        dialog = ctk.CTkInputDialog(text="Nom du nouveau profil d'écran :", title="Nouveau profil")
        name = dialog.get_input()
        if not name:
            return
        if name in self.screen_profiles:
            messagebox.showerror("Erreur", "Un profil porte déjà ce nom.")
            return
        try:
            w, h = pyautogui.size()
        except:
            w, h = (0, 0)
        self.screen_profiles[name] = {
            "resolution": [w, h],
            "moves": self.load_json(MOVES_FILE, {}),
            "fishing": self.load_json(FISH_FILE, {}),
            "combat": self.load_json(COMBAT_FILE, {})
        }
        self.save_json(SCREEN_PROFILES_FILE, self.screen_profiles)
        self.current_screen_profile.set(name)
        self.refresh_screen_profile_ui()

    def duplicate_screen_profile(self):
        src = self.current_screen_profile.get()
        if src not in self.screen_profiles:
            messagebox.showerror("Erreur", "Aucun profil à dupliquer.")
            return
        dialog = ctk.CTkInputDialog(text=f"Nouveau nom pour la copie de '{src}' :", title="Dupliquer profil")
        name = dialog.get_input()
        if not name:
            return
        if name in self.screen_profiles:
            messagebox.showerror("Erreur", "Un profil porte déjà ce nom.")
            return
        self.screen_profiles[name] = json.loads(json.dumps(self.screen_profiles[src]))  # deep copy simple
        self.save_json(SCREEN_PROFILES_FILE, self.screen_profiles)
        self.current_screen_profile.set(name)
        self.refresh_screen_profile_ui()

    def rename_screen_profile(self):
        old = self.current_screen_profile.get()
        if old not in self.screen_profiles:
            messagebox.showerror("Erreur", "Aucun profil sélectionné.")
            return
        dialog = ctk.CTkInputDialog(text=f"Nouveau nom pour '{old}' :", title="Renommer profil")
        new = dialog.get_input()
        if not new or new == old:
            return
        if new in self.screen_profiles:
            messagebox.showerror("Erreur", "Un profil porte déjà ce nom.")
            return
        self.screen_profiles[new] = self.screen_profiles.pop(old)
        self.save_json(SCREEN_PROFILES_FILE, self.screen_profiles)
        self.current_screen_profile.set(new)
        self.refresh_screen_profile_ui()

    def delete_screen_profile(self):
        name = self.current_screen_profile.get()
        if name not in self.screen_profiles:
            return
        if len(self.screen_profiles) == 1:
            messagebox.showerror("Erreur", "Impossible de supprimer le dernier profil.")
            return
        if not messagebox.askyesno("Confirmer", f"Supprimer le profil '{name}' ?"):
            return
        del self.screen_profiles[name]
        self.save_json(SCREEN_PROFILES_FILE, self.screen_profiles)
        # Bascule sur un autre profil
        self.current_screen_profile.set(list(self.screen_profiles.keys())[0])
        self.refresh_screen_profile_ui()

    def check_map_data(self):
        map_id = self.entry_inspect_map.get().strip()
        if not map_id: return
        
        # Load data
        moves = self.load_json(MOVES_FILE, {})
        fish = self.load_json(FISH_FILE, {})
        
        info = []
        # Check moves
        move_dirs = [k.split('_')[1] for k in moves.keys() if k.startswith(map_id + "_")]
        if move_dirs: info.append(f"Sorties calibrées: {', '.join(move_dirs)}")
        else: info.append("Aucune sortie calibrée")
        
        # Check fish
        if map_id in fish: info.append(f"Poissons: {len(fish[map_id])} spots")
        else: info.append("Aucun poisson")
        
        self.lbl_map_info.configure(text=" | ".join(info))

    # ----------------------------------------------------------------
    # 3. CALIBRAGE MANUEL
    # ----------------------------------------------------------------
    def create_calib_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["calib"] = frame
        
        ctk.CTkLabel(frame, text="Outils de Calibrage", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20,5))
        ctk.CTkLabel(
            frame, 
            text="Choisissez le type de point à enregistrer puis cliquez sur \"DÉMARRER CALIBRAGE\".", 
            text_color="gray"
        ).pack()

        # Bandeau profil écran pour bien voir où seront stockés les calibrages
        screen_bar = ctk.CTkFrame(frame, fg_color="transparent")
        screen_bar.pack(pady=(5, 10))
        ctk.CTkLabel(screen_bar, text="Profil d'écran pour ce calibrage :", text_color="gray").pack(side="left", padx=5)
        self.combo_calib_screen = ctk.CTkComboBox(
            screen_bar,
            width=180,
            values=list(self.screen_profiles.keys()),
            command=self.on_calib_screen_change
        )
        # Valeur initiale = profil courant
        self.combo_calib_screen.set(self.current_screen_profile.get())
        self.combo_calib_screen.pack(side="left", padx=5)
        
        # Selecteur Mode (Liste déroulante)
        mode_frame = ctk.CTkFrame(frame, fg_color="transparent")
        mode_frame.pack(pady=10)
        
        ctk.CTkLabel(mode_frame, text="Type de calibrage :", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        
        self.calib_type = ctk.StringVar(value="move")
        modes_list = [
            "Déplacement (Map)",
            "Poissons (Spots)",
            "Cible Combat",
            "Pos. Sort",
            "Zone PA",
            "Zone PM",
            "--- Templates Personnage ---",
            "Template Perso - Face",
            "Template Perso - Dos",
            "Template Perso - Côté Gauche",
            "Template Perso - Côté Droit",
            "Template Perso - Haut",
            "Template Perso - Bas",
            "Template Perso - Diag. Haut-Droite",
            "Template Perso - Diag. Haut-Gauche",
            "Template Perso - Diag. Bas-Droite",
            "Template Perso - Diag. Bas-Gauche",
            "--- Autres ---",
            "📏 Taille Case Combat (TEMP)",
            "Arme de drop",
            "Canne à pêche",
            "Dragodinde",
        ]
        modes_values = [
            "move",
            "fish",
            "combat",
            "spell",
            "ap",
            "mp",
            "separator1",
            "player_face",
            "player_dos",
            "player_left",
            "player_right",
            "player_top",
            "player_bottom",
            "player_top_right",
            "player_top_left",
            "player_bottom_right",
            "player_bottom_left",
            "separator2",
            "case_size",
            "weapon_drop",
            "weapon_fish",
            "dd",
        ]
        
        self.combo_calib_type = ctk.CTkComboBox(
            mode_frame,
            values=modes_list,
            variable=self.calib_type,
            width=250,
            command=self.on_calib_type_change
        )
        self.combo_calib_type.pack(side="left", padx=10)
        
        # Mapping pour convertir le texte affiché en valeur
        self.calib_type_mapping = dict(zip(modes_list, modes_values))

        # Config
        self.frame_calib_opts = ctk.CTkFrame(frame, border_width=1, border_color="#444444")
        self.frame_calib_opts.pack(pady=20, padx=50, fill="x")
        
        self.lbl_calib_map = ctk.CTkLabel(self.frame_calib_opts, text="Map (ex: 12,4) :")
        self.lbl_calib_map.pack(pady=(10,0))
        self.entry_calib_map = ctk.CTkEntry(self.frame_calib_opts)
        self.entry_calib_map.pack(pady=5)
        
        self.calib_extra_frame = ctk.CTkFrame(self.frame_calib_opts, fg_color="transparent")
        self.calib_extra_frame.pack(pady=5)
        
        self.combo_calib_dir = ctk.CTkComboBox(self.calib_extra_frame, values=["DROITE", "GAUCHE", "HAUT", "BAS"])
        self.entry_forced_map = ctk.CTkEntry(self.calib_extra_frame, placeholder_text="Map forcée (Optionnel)")

        # Action
        self.btn_capture = ctk.CTkButton(frame, text="DÉMARRER CALIBRAGE (5s)", height=50, font=("Arial", 16), command=self.start_calibration)
        self.btn_capture.pack(pady=20)
        
        self.lbl_calib_status = ctk.CTkLabel(frame, text="En attente...", font=("Arial", 14))
        self.lbl_calib_status.pack(pady=10)
        
        self.update_calib_ui()

    def on_calib_screen_change(self, choice):
        """Quand on change de profil écran directement depuis l'onglet Calibrage"""
        if choice in self.screen_profiles:
            self.current_screen_profile.set(choice)
            # Garder l'UI cohérente : mettre à jour aussi les autres combos si elles existent
            if hasattr(self, "combo_screen"):
                self.combo_screen.configure(values=list(self.screen_profiles.keys()))
                self.combo_screen.set(choice)
            if hasattr(self, "combo_circuit_screen"):
                self.combo_circuit_screen.configure(values=list(self.screen_profiles.keys()))
                self.combo_circuit_screen.set(choice)

    def on_calib_type_change(self, choice):
        """Quand on change le type de calibrage depuis la liste déroulante"""
        # Convertir le texte affiché en valeur
        mode = self.calib_type_mapping.get(choice, choice.lower().replace(" ", "_"))
        self.calib_type.set(mode)
        self.update_calib_ui()

    def update_calib_ui(self):
        mode = self.calib_type.get()
        if mode == "move":
            self.lbl_calib_map.pack(pady=(10,0))
            self.entry_calib_map.pack(pady=5)
            self.calib_extra_frame.pack(pady=5)
            self.combo_calib_dir.pack(side="left", padx=5)
            self.entry_forced_map.pack(side="left", padx=5)
            self.btn_capture.configure(text="Capturer Changement Map (5s)")
        elif mode == "fish":
            self.lbl_calib_map.pack(pady=(10,0))
            self.entry_calib_map.pack(pady=5)
            self.calib_extra_frame.pack_forget()
            self.btn_capture.configure(text="Ajouter Spot Poisson (5s)")
        else:
            self.lbl_calib_map.pack_forget()
            self.entry_calib_map.pack_forget()
            self.calib_extra_frame.pack_forget()
            label = {
                "combat": "Cible Combat",
                "spell": "Position Sort",
                "ap": "Zone PA",
                "mp": "Zone PM",
                "player_face": "Template Perso - Face",
                "player_dos": "Template Perso - Dos",
                "player_left": "Template Perso - Côté Gauche",
                "player_right": "Template Perso - Côté Droit",
                "player_top": "Template Perso - Haut",
                "player_bottom": "Template Perso - Bas",
                "player_top_right": "Template Perso - Diag. Haut-Droite",
                "player_top_left": "Template Perso - Diag. Haut-Gauche",
                "player_bottom_right": "Template Perso - Diag. Bas-Droite",
                "player_bottom_left": "Template Perso - Diag. Bas-Gauche",
                "case_size": "Taille Case Combat",
                "weapon_drop": "Arme de Drop",
                "weapon_fish": "Canne à Pêche",
                "dd": "Dragodinde",
            }.get(mode, mode.upper())
            
            if mode == "case_size":
                self.btn_capture.configure(text="📏 Cliquer 2 points d'une case (5s) - Point 1")
            elif mode in ["player_face", "player_dos", "player_left", "player_right", 
                         "player_top", "player_bottom", "player_top_right", "player_top_left",
                         "player_bottom_right", "player_bottom_left"]:
                self.btn_capture.configure(text=f"📸 Capturer {label} (5s)")
            elif mode in ["separator1", "separator2"]:
                self.btn_capture.configure(text="--- (Séparateur)")
            else:
                self.btn_capture.configure(text=f"Définir {label} (5s)")

    def start_calibration(self):
        # Logique identique mais adaptée à la nouvelle structure
        map_coords = self.entry_calib_map.get()
        # Récupérer la valeur depuis le mapping si nécessaire
        choice = self.combo_calib_type.get()
        mode = self.calib_type_mapping.get(choice, self.calib_type.get())
        
        if mode in ["move", "fish"] and (not map_coords or "," not in map_coords):
            messagebox.showerror("Erreur", "Veuillez entrer les coordonnées de la map (X,Y)")
            return
        
        direction = self.combo_calib_dir.get() if mode == "move" else None
        forced = self.entry_forced_map.get().strip() if mode == "move" and self.entry_forced_map.get().strip() else None

        self.btn_capture.configure(state="disabled")
        threading.Thread(target=self._calibration_thread, args=(map_coords, mode, direction, forced)).start()
        
    def _calibration_thread(self, map_coords, mode, direction, forced):
        # Pour le calibrage de taille de case, on gère différemment (2 clics)
        if mode == "case_size":
            if not hasattr(self, '_case_size_point1'):
                # Premier clic
                for i in range(5, 0, -1):
                    self.lbl_calib_status.configure(text=f"Point 1 : Placez votre souris sur un coin de case... {i}s", text_color="orange")
                    time.sleep(1)
                x, y = pyautogui.position()
                self._case_size_point1 = (x, y)
                self.lbl_calib_status.configure(text="✅ Point 1 enregistré. Relancez le calibrage pour le point 2.", text_color="green")
                self.btn_capture.configure(state="normal")
                self.btn_capture.configure(text="📏 Cliquer 2 points d'une case (5s) - Point 2")
                return
            else:
                # Deuxième clic
                for i in range(5, 0, -1):
                    self.lbl_calib_status.configure(text=f"Point 2 : Placez votre souris sur le coin opposé... {i}s", text_color="orange")
                    time.sleep(1)
                x, y = pyautogui.position()
                x1, y1 = self._case_size_point1
                
                # Calculer la taille
                width = abs(x - x1)
                height = abs(y - y1)
                case_size = max(width, height)
                
                # Sauvegarder
                data = self.load_json(COMBAT_FILE, {})
                data["case_size_pixels"] = case_size
                self.save_json(COMBAT_FILE, data)
                
                msg = f"Taille de case calibrée : {case_size} pixels (largeur: {width}, hauteur: {height})"
                delattr(self, '_case_size_point1')
                self.lbl_calib_status.configure(text=f"✅ {msg}", text_color="green")
                self.btn_capture.configure(state="normal")
                self.btn_capture.configure(text="📏 Cliquer 2 points d'une case (5s) - Point 1")
                return
        
        # Pour les autres modes, calibrage normal
        for i in range(5, 0, -1):
            self.lbl_calib_status.configure(text=f"Placez votre souris... {i}s", text_color="orange")
            time.sleep(1)
        
        x, y = pyautogui.position()
        msg = "Succès"
        
        if mode == "move":
            data = self.load_json(MOVES_FILE, {})
            val = [x, y]
            if forced: val.append(forced)
            data[f"{map_coords}_{direction}"] = val
            self.save_json(MOVES_FILE, data)
            msg = f"Sortie {direction} calibrée sur {map_coords}"
            
        elif mode == "fish":
            data = self.load_json(FISH_FILE, {})
            if map_coords not in data: data[map_coords] = []
            data[map_coords].append([x, y])
            self.save_json(FISH_FILE, data)
            msg = f"Poisson ajouté sur {map_coords} (Total: {len(data[map_coords])})"
            
        elif mode in ["separator1", "separator2"]:
            msg = "Séparateur (non calibrable)"
        
        elif mode in ["player_face", "player_dos", "player_left", "player_right", 
                      "player_top", "player_bottom", "player_top_right", "player_top_left",
                      "player_bottom_right", "player_bottom_left"]:
            # Capture des templates du personnage sous différents angles
            # Zone plus grande pour capturer tout le personnage + la DD (peut être assez grand)
            template_size = 150  # Augmenté à 150x150 pour être sûr de tout capturer
            # Décalage vers le haut : on prend moins en bas, plus en haut
            # Le personnage est généralement centré un peu plus haut que la position de la souris
            # Appliqué à TOUS les angles (face, dos, gauche, droite, haut, bas, diagonales)
            offset_y = -30  # On remonte de 30 pixels pour tous les angles
            region = (
                max(0, x - template_size//2), 
                max(0, y - template_size//2 + offset_y), 
                template_size, 
                template_size
            )
            
            try:
                import PIL.Image
                template_img = pyautogui.screenshot(region=region)
                
                if not os.path.exists("templates"):
                    os.makedirs("templates")
                
                # Créer un dossier debug pour voir ce qui est capturé
                if not os.path.exists("debug_templates"):
                    os.makedirs("debug_templates")
                
                # Mapping des modes vers les noms de fichiers
                template_names = {
                    "player_face": "player_face.png",
                    "player_dos": "player_dos.png",
                    "player_left": "player_left.png",
                    "player_right": "player_right.png",
                    "player_top": "player_top.png",
                    "player_bottom": "player_bottom.png",
                    "player_top_right": "player_top_right.png",
                    "player_top_left": "player_top_left.png",
                    "player_bottom_right": "player_bottom_right.png",
                    "player_bottom_left": "player_bottom_left.png"
                }
                
                template_path = os.path.join("templates", template_names[mode])
                template_img.save(template_path)
                
                # Sauvegarder aussi dans debug pour vérification
                debug_path = os.path.join("debug_templates", template_names[mode])
                template_img.save(debug_path)
                
                angle_names = {
                    "player_face": "Face",
                    "player_dos": "Dos",
                    "player_left": "Côté Gauche",
                    "player_right": "Côté Droit",
                    "player_top": "Haut",
                    "player_bottom": "Bas",
                    "player_top_right": "Diagonale Haut-Droite",
                    "player_top_left": "Diagonale Haut-Gauche",
                    "player_bottom_right": "Diagonale Bas-Droite",
                    "player_bottom_left": "Diagonale Bas-Gauche"
                }
                
                msg = f"Template personnage ({angle_names[mode]}) sauvegardé : {template_path} ({template_size}x{template_size}px)\n📸 Image de debug : {debug_path}"
            except Exception as e:
                msg = f"Erreur sauvegarde template : {e}"
        
        elif mode in ["combat", "spell", "ap", "mp", "weapon_drop", "weapon_fish", "dd"]:
            data = self.load_json(COMBAT_FILE, {})
            keys = {
                "combat": "target_point",
                "spell": "spell_point",
                "ap": "ap_point",
                "mp": "mp_point",
                "weapon_drop": "weapon_drop_point",
                "weapon_fish": "weapon_fish_point",
                "dd": "dd_point",
            }
            data[keys[mode]] = [x, y]
            self.save_json(COMBAT_FILE, data)
            labels = {
                "combat": "Cible Combat",
                "spell": "Position Sort",
                "ap": "Zone PA",
                "mp": "Zone PM",
                "weapon_drop": "Arme de Drop",
                "dd": "Dragodinde",
                "weapon_fish": "Canne à Pêche",
            }
            msg = f"{labels.get(mode, mode)} défini."

        # Après chaque calibrage, on synchronise le profil d'écran actif
        self.sync_current_screen_profile_from_files()

        self.lbl_calib_status.configure(text=f"✅ {msg}", text_color="green")
        self.btn_capture.configure(state="normal")

    def sync_current_screen_profile_from_files(self):
        """Mets à jour le profil d'écran actif à partir des fichiers manuels"""
        name = self.current_screen_profile.get()
        if not name:
            return
        if name not in self.screen_profiles:
            # Si le profil n'existe plus, on le recrée rapidement
            try:
                w, h = pyautogui.size()
            except:
                w, h = (0, 0)
            self.screen_profiles[name] = {
                "resolution": [w, h],
                "moves": {},
                "fishing": {},
                "combat": {}
            }
        self.screen_profiles[name]["moves"] = self.load_json(MOVES_FILE, {})
        self.screen_profiles[name]["fishing"] = self.load_json(FISH_FILE, {})
        self.screen_profiles[name]["combat"] = self.load_json(COMBAT_FILE, {})
        self.save_json(SCREEN_PROFILES_FILE, self.screen_profiles)

    # ----------------------------------------------------------------
    # 4. GESTION (Tables)
    # ----------------------------------------------------------------
    def create_manage_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["manage"] = frame
        
        ctk.CTkLabel(frame, text="Base de Données Calibrage", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)
        
        self.tab_view = ctk.CTkTabview(frame)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        t_nav = self.tab_view.add("Navigation")
        t_fish = self.tab_view.add("Pêche")
        t_cbt = self.tab_view.add("Combat")
        
        self.scroll_nav = ctk.CTkScrollableFrame(t_nav)
        self.scroll_nav.pack(fill="both", expand=True)
        
        self.scroll_fish = ctk.CTkScrollableFrame(t_fish)
        self.scroll_fish.pack(fill="both", expand=True)
        
        self.scroll_cbt = ctk.CTkScrollableFrame(t_cbt)
        self.scroll_cbt.pack(fill="both", expand=True)
        
        ctk.CTkButton(frame, text="Actualiser", command=self.refresh_manage_view).pack(pady=5)

    def refresh_manage_view(self):
        for s in [self.scroll_nav, self.scroll_fish, self.scroll_cbt]:
            for w in s.winfo_children(): w.destroy()

        # Nav
        moves = self.load_json(MOVES_FILE, {})
        for k, v in moves.items():
            self._add_row(self.scroll_nav, k, f"Clic: {v}", MOVES_FILE, moves)

        # Fish
        fish = self.load_json(FISH_FILE, {})
        for k, v in fish.items():
            self._add_row(self.scroll_fish, k, f"{len(v)} spots", FISH_FILE, fish)

        # Combat
        cbt = self.load_json(COMBAT_FILE, {})
        for k, v in cbt.items():
            self._add_row(self.scroll_cbt, k, f"{v}", COMBAT_FILE, cbt)

    def _add_row(self, parent, key, desc, filepath, full_data):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=key, width=100, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=desc, anchor="w").pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(row, text="X", width=30, fg_color="red", command=lambda: self._delete_item(key, filepath)).pack(side="right", padx=5, pady=2)

    def _delete_item(self, key, filepath):
        data = self.load_json(filepath, {})
        if key in data:
            del data[key]
            self.save_json(filepath, data)
            self.refresh_manage_view()

    # ----------------------------------------------------------------
    # 5. TEMPLATES IA (Générique)
    # ----------------------------------------------------------------
    def create_templates_view(self):
        """Crée la vue de gestion des templates IA (Personnage, Mobs, etc.)"""
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["templates"] = frame
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="🎯 Gestion des Templates IA", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack()
        
        # Sélection du template actif
        select_frame = ctk.CTkFrame(frame)
        select_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(select_frame, text="Template actif :", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        
        template_names = list(self.templates.keys())
        self.combo_template = ctk.CTkComboBox(select_frame, 
                                             values=template_names,
                                             variable=self.current_template,
                                             width=200,
                                             command=self.on_template_change)
        self.combo_template.pack(side="left", padx=10)
        self.combo_template.set(self.current_template.get())
        
        # Boutons de gestion
        btn_frame = ctk.CTkFrame(select_frame, fg_color="transparent")
        btn_frame.pack(side="left", padx=20)
        
        ctk.CTkButton(btn_frame, text="➕ Nouveau", width=100,
                     command=self.create_new_template).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Modifier", width=100,
                     command=self.edit_template).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ Supprimer", width=100, fg_color="red",
                     command=self.delete_template).pack(side="left", padx=5)
        
        # Info du template sélectionné
        self.template_info_frame = ctk.CTkFrame(frame)
        self.template_info_frame.pack(fill="x", padx=20, pady=10)
        self.refresh_template_info()
        
        # Actions pour le template sélectionné
        actions_frame = ctk.CTkFrame(frame)
        actions_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(actions_frame, text="Actions pour ce template :", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # Collecte
        collect_frame = ctk.CTkFrame(actions_frame)
        collect_frame.pack(fill="x", padx=10, pady=5)
        
        self.btn_start_collect = ctk.CTkButton(collect_frame, 
            text="▶ Démarrer Collecte (2 min)", 
            height=50, 
            fg_color="#2CC985", 
            hover_color="#229966",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_template_collection)
        self.btn_start_collect.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_stop_collect = ctk.CTkButton(collect_frame, 
            text="⏹ Arrêter", 
            height=50, 
            fg_color="#FF4D4D", 
            hover_color="#CC0000",
            state="disabled",
            command=self.stop_template_collection)
        self.btn_stop_collect.pack(side="left", padx=5)
        
        # Statut collecte
        self.lbl_collect_status = ctk.CTkLabel(actions_frame, 
            text="Prêt à collecter", 
            font=ctk.CTkFont(size=12))
        self.lbl_collect_status.pack(pady=5)
        
        # Progression
        self.progress_collect = ctk.CTkProgressBar(actions_frame)
        self.progress_collect.pack(fill="x", padx=20, pady=10)
        self.progress_collect.set(0)
        
        # Autres actions
        other_actions = ctk.CTkFrame(actions_frame, fg_color="transparent")
        other_actions.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(other_actions, 
            text="📦 Déplacer Images", 
            height=40, 
            fg_color="#E67E22", 
            hover_color="#D35400",
            command=self.move_template_images).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(other_actions, 
            text="✏️ Annoter", 
            height=40, 
            fg_color="#9B59B6", 
            hover_color="#7D3C98",
            command=lambda: self.show_frame("annotate")).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(other_actions, 
            text="📦 Préparer Dataset", 
            height=40, 
            fg_color="#3B8ED0", 
            hover_color="#1F6AA5",
            command=self.prepare_template_dataset).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(other_actions, 
            text="🚀 Entraîner", 
            height=40, 
            fg_color="#D97706", 
            hover_color="#B45309",
            command=self.train_template_model).pack(side="left", padx=5, expand=True, fill="x")
    
    def refresh_template_info(self):
        """Met à jour l'affichage des infos du template sélectionné."""
        for widget in self.template_info_frame.winfo_children():
            widget.destroy()
        
        template_name = self.current_template.get()
        if template_name in self.templates:
            template = self.templates[template_name]
            info_text = f"""
📁 Dossier : player_dataset/images/{template['folder']}/
🏷️  Class ID : {template['class_id']}
📝 Nom classe : {template['class_name']}
ℹ️  Description : {template.get('description', 'Aucune')}
            """
            ctk.CTkLabel(self.template_info_frame, text=info_text.strip(), 
                        justify="left", font=ctk.CTkFont(size=11)).pack(padx=20, pady=10)
    
    def on_template_change(self, choice):
        """Quand on change de template."""
        self.current_template.set(choice)
        self.refresh_template_info()
    
    def create_new_template(self):
        """Crée un nouveau template."""
        dialog = ctk.CTkInputDialog(text="Nom du nouveau template :", title="Nouveau Template")
        name = dialog.get_input()
        if not name or name in self.templates:
            if name in self.templates:
                messagebox.showerror("Erreur", "Un template avec ce nom existe déjà.")
            return
        
        # Dialog pour les détails
        class_id = len(self.templates)  # ID automatique
        folder = name  # Dossier = nom du template
        
        self.templates[name] = {
            "class_id": class_id,
            "class_name": name.lower(),
            "folder": folder,
            "description": f"Détection de {name}"
        }
        
        self.save_json("templates_config.json", self.templates)
        self.combo_template.configure(values=list(self.templates.keys()))
        self.combo_template.set(name)
        self.current_template.set(name)
        self.refresh_template_info()
        messagebox.showinfo("Succès", f"Template '{name}' créé !")
    
    def edit_template(self):
        """Modifie un template existant."""
        template_name = self.current_template.get()
        if template_name not in self.templates:
            return
        
        # Pour l'instant, on peut juste modifier la description
        dialog = ctk.CTkInputDialog(
            text=f"Description pour '{template_name}' :", 
            title="Modifier Template"
        )
        desc = dialog.get_input()
        if desc:
            self.templates[template_name]["description"] = desc
            self.save_json("templates_config.json", self.templates)
            self.refresh_template_info()
    
    def delete_template(self):
        """Supprime un template."""
        template_name = self.current_template.get()
        if template_name not in self.templates:
            return
        
        if len(self.templates) <= 1:
            messagebox.showerror("Erreur", "Impossible de supprimer le dernier template.")
            return
        
        if messagebox.askyesno("Confirmer", f"Supprimer le template '{template_name}' ?"):
            del self.templates[template_name]
            self.save_json("templates_config.json", self.templates)
            template_names = list(self.templates.keys())
            self.combo_template.configure(values=template_names)
            self.combo_template.set(template_names[0])
            self.current_template.set(template_names[0])
            self.refresh_template_info()
    
    def start_template_collection(self):
        """Démarre la collecte pour le template actif."""
        template_name = self.current_template.get()
        if template_name not in self.templates:
            return
        
        template = self.templates[template_name]
        save_dir = os.path.join("player_dataset", "images", template["folder"])
        
        if self.player_collector.is_collecting:
            return
        
        self.btn_start_collect.configure(state="disabled")
        self.btn_stop_collect.configure(state="normal")
        self.progress_collect.set(0)
        
        def update_status(message, count, total):
            self.lbl_collect_status.configure(text=message)
            if total > 0:
                self.progress_collect.set(count / total)
        
        def collection_thread():
            try:
                self.player_collector.collect_images_only(
                    duration_seconds=120,
                    interval=2.0,
                    save_dir=save_dir,
                    callback=update_status
                )
            finally:
                self.btn_start_collect.configure(state="normal")
                self.btn_stop_collect.configure(state="disabled")
                self.progress_collect.set(1.0)
        
        threading.Thread(target=collection_thread, daemon=True).start()
    
    def stop_template_collection(self):
        """Arrête la collecte."""
        self.player_collector.stop_collection()
        self.btn_start_collect.configure(state="normal")
        self.btn_stop_collect.configure(state="disabled")
        self.lbl_collect_status.configure(text="Collecte arrêtée")
    
    def move_template_images(self):
        """Déplace les images collectées vers le dossier du template."""
        template_name = self.current_template.get()
        if template_name not in self.templates:
            return
        
        template = self.templates[template_name]
        source_dir = "player_dataset/images"
        dest_dir = os.path.join("player_dataset", "images", template["folder"])
        
        if not os.path.exists(source_dir):
            messagebox.showerror("Erreur", f"Dossier source non trouvé : {source_dir}")
            return
        
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        image_files = [f for f in os.listdir(source_dir) 
                      if any(f.lower().endswith(ext) for ext in extensions) 
                      and '_annotated' not in f]
        
        if not image_files:
            messagebox.showinfo("Info", "Aucune image à déplacer.")
            return
        
        moved = 0
        for img_file in image_files:
            src_path = os.path.join(source_dir, img_file)
            dst_path = os.path.join(dest_dir, img_file)
            if not os.path.exists(dst_path):
                import shutil
                shutil.move(src_path, dst_path)
                moved += 1
        
        messagebox.showinfo("Succès", f"{moved} image(s) déplacée(s) vers {template['folder']}/")
    
    def prepare_template_dataset(self):
        """Prépare le dataset pour le template actif."""
        template_name = self.current_template.get()
        if template_name not in self.templates:
            return
        
        template = self.templates[template_name]
        source_dir = os.path.join("player_dataset", "images", template["folder"])
        
        if not os.path.exists(source_dir):
            messagebox.showerror("Erreur", f"Dossier non trouvé : {source_dir}")
            return
        
        txt_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]
        if not txt_files:
            messagebox.showerror("Erreur", f"Aucune annotation trouvée dans {source_dir}")
            return
        
        if messagebox.askyesno("Confirmation", 
            f"Préparer le dataset pour '{template_name}' ?\n\n"
            f"📁 {len(txt_files)} annotation(s) trouvée(s)\n"
            f"📦 Les images seront copiées vers train/ et validation/"):
            try:
                # Utiliser la fonction générique de préparation
                from prepare_template_dataset import prepare_template_dataset
                prepare_template_dataset(template_name, self.templates)
                messagebox.showinfo("Succès", "Dataset préparé avec succès !")
            except Exception as e:
                import traceback
                messagebox.showerror("Erreur", f"Erreur : {e}\n\n{traceback.format_exc()}")
    
    def train_template_model(self):
        """Lance l'entraînement pour le template actif."""
        template_name = self.current_template.get()
        if template_name not in self.templates:
            return
        
        if messagebox.askyesno("Attention", 
            f"Lancer l'entraînement pour '{template_name}' ?\n\n"
            "Cela peut prendre du temps."):
            threading.Thread(
                target=self._train_template_thread, 
                args=(template_name,), 
                daemon=True
            ).start()
            messagebox.showinfo("Info", "Entraînement lancé en arrière-plan.")
    
    def _train_template_thread(self, template_name):
        """Thread d'entraînement."""
        from train_template import train_template_model
        train_template_model(template_name, self.templates)

    # ----------------------------------------------------------------
    # 5bis. ANCIEN TEMPLATE PERSONNAGE (déprécié, gardé pour compatibilité)
    # ----------------------------------------------------------------
    def create_player_template_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["player_template"] = frame
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="🎯 Collecte de Données Personnage (YOLO)", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack()
        
        # Instructions
        info_frame = ctk.CTkFrame(frame)
        info_frame.pack(fill="x", padx=20, pady=10)
        instructions = """
📋 Instructions :
1. Va en combat ou déplace-toi sur la map
2. Clique sur "Démarrer Collecte" ci-dessous
3. Le bot va capturer des screenshots toutes les 2 secondes pendant 2 minutes
4. Les images seront automatiquement annotées (détection du rond rouge)
5. Une fois terminé, prépare le dataset et lance l'entraînement
        """
        ctk.CTkLabel(info_frame, text=instructions, justify="left", 
                    font=ctk.CTkFont(size=12)).pack(padx=20, pady=15)
        
        # Contrôles
        controls_frame = ctk.CTkFrame(frame)
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        # Bouton de collecte
        self.btn_start_collect = ctk.CTkButton(controls_frame, 
            text="▶ Démarrer Collecte (2 min)", 
            height=50, 
            fg_color="#2CC985", 
            hover_color="#229966",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_player_collection)
        self.btn_start_collect.pack(pady=10)
        
        self.btn_stop_collect = ctk.CTkButton(controls_frame, 
            text="⏹ Arrêter Collecte", 
            height=40, 
            fg_color="#FF4D4D", 
            hover_color="#CC0000",
            state="disabled",
            command=self.stop_player_collection)
        self.btn_stop_collect.pack(pady=5)
        
        # Statut
        self.lbl_collect_status = ctk.CTkLabel(controls_frame, 
            text="Prêt à collecter", 
            font=ctk.CTkFont(size=12))
        self.lbl_collect_status.pack(pady=10)
        
        # Progression
        self.progress_collect = ctk.CTkProgressBar(controls_frame)
        self.progress_collect.pack(fill="x", padx=20, pady=10)
        self.progress_collect.set(0)
        
        # Actions post-collecte
        actions_frame = ctk.CTkFrame(frame)
        actions_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(actions_frame, text="Actions après collecte :", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        btn_move_images = ctk.CTkButton(actions_frame, 
            text="📦 Déplacer Images vers Personnage/", 
            height=40, 
            fg_color="#E67E22", 
            hover_color="#D35400",
            command=self.move_images_to_personnage)
        btn_move_images.pack(pady=5)
        
        btn_annotate = ctk.CTkButton(actions_frame, 
            text="✏️ Ouvrir Annotateur Manuel", 
            height=40, 
            fg_color="#9B59B6", 
            hover_color="#7D3C98",
            command=lambda: self.show_frame("annotate"))
        btn_annotate.pack(pady=5)
        
        btn_prepare = ctk.CTkButton(actions_frame, 
            text="📦 Préparer Dataset (Train/Val)", 
            height=40, 
            fg_color="#3B8ED0", 
            hover_color="#1F6AA5",
            command=self.prepare_player_dataset)
        btn_prepare.pack(pady=5)
        
        btn_train = ctk.CTkButton(actions_frame, 
            text="🚀 Lancer Entraînement YOLO", 
            height=40, 
            fg_color="#D97706", 
            hover_color="#B45309",
            command=self.train_player_model)
        btn_train.pack(pady=5)
    
    def start_player_collection(self):
        """Démarre la collecte de données du personnage."""
        if self.player_collector.is_collecting:
            return
        
        self.btn_start_collect.configure(state="disabled")
        self.btn_stop_collect.configure(state="normal")
        self.progress_collect.set(0)
        
        def update_status(message, count, total):
            self.lbl_collect_status.configure(text=message)
            if total > 0:
                self.progress_collect.set(count / total)
        
        def collection_thread():
            try:
                self.player_collector.collect_images_only(
                    duration_seconds=120,  # 2 minutes
                    interval=2.0,  # Toutes les 2 secondes
                    save_dir="player_dataset/images/Personnage",
                    callback=update_status
                )
            finally:
                self.btn_start_collect.configure(state="normal")
                self.btn_stop_collect.configure(state="disabled")
                self.progress_collect.set(1.0)
        
        threading.Thread(target=collection_thread, daemon=True).start()
    
    def stop_player_collection(self):
        """Arrête la collecte en cours."""
        self.player_collector.stop_collection()
        self.btn_start_collect.configure(state="normal")
        self.btn_stop_collect.configure(state="disabled")
        self.lbl_collect_status.configure(text="Collecte arrêtée")
    
    def move_images_to_personnage(self):
        """Déplace les images collectées vers le dossier Personnage."""
        import move_images_to_personnage
        if messagebox.askyesno("Confirmation", 
            "Cela va déplacer les images de player_dataset/images/ vers player_dataset/images/Personnage/.\n\n"
            "Les images existantes dans Personnage/ seront conservées.\n\nContinuer ?"):
            try:
                move_images_to_personnage.move_images_to_personnage()
                messagebox.showinfo("Succès", "Images déplacées avec succès !\nTu peux maintenant ouvrir l'annotateur.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du déplacement : {e}")
    
    def open_annotator(self):
        """Ouvre l'outil d'annotation manuelle."""
        import subprocess
        import sys
        
        # Chemin absolu vers l'annotateur
        annotator_path = os.path.abspath("annotate_player.py")
        
        if not os.path.exists(annotator_path):
            messagebox.showerror("Erreur", 
                f"Fichier annotate_player.py non trouvé !\n\n"
                f"Chemin cherché : {annotator_path}")
            return
        
        try:
            # Importer et lancer directement l'annotateur dans un thread séparé
            from annotate_player import PlayerAnnotator
            from tkinter import Tk
            
            def launch_annotator():
                try:
                    root = Tk()
                    app = PlayerAnnotator(root)
                    root.mainloop()
                except Exception as e:
                    import traceback
                    error_msg = f"Erreur lors du lancement de l'annotateur :\n{e}\n\n"
                    error_msg += traceback.format_exc()
                    # Utiliser after pour afficher l'erreur depuis le thread GUI
                    self.after(0, lambda: messagebox.showerror("Erreur Annotateur", error_msg))
            
            # Lancer dans un thread séparé pour ne pas bloquer l'interface
            threading.Thread(target=launch_annotator, daemon=True).start()
            
            messagebox.showinfo("Info", 
                "Outil d'annotation ouvert !\n\n"
                "Les annotations seront sauvegardées dans :\n"
                "player_dataset/images/Personnage/\n\n"
                "Si la fenêtre ne s'affiche pas, vérifie les erreurs dans la console.")
        except ImportError as e:
            messagebox.showerror("Erreur", 
                f"Impossible d'importer l'annotateur : {e}\n\n"
                "Vérifie que le fichier annotate_player.py existe et que toutes les dépendances sont installées.")
        except Exception as e:
            import traceback
            error_msg = f"Impossible d'ouvrir l'annotateur : {e}\n\n"
            error_msg += f"Traceback :\n{traceback.format_exc()}"
            messagebox.showerror("Erreur", error_msg)
    
    def prepare_player_dataset(self):
        """Prépare le dataset pour YOLO (séparation train/val)."""
        # Vérifier qu'il y a des annotations
        annotated_dir = os.path.abspath("player_dataset/images/Personnage")
        if not os.path.exists(annotated_dir):
            messagebox.showerror("Erreur", 
                f"Dossier non trouvé : {annotated_dir}\n\n"
                "Assure-toi d'avoir annoté des images avec l'annotateur.")
            return
        
        # Compter les annotations
        txt_files = [f for f in os.listdir(annotated_dir) if f.endswith('.txt')]
        if not txt_files:
            messagebox.showerror("Erreur", 
                f"Aucune annotation trouvée dans {annotated_dir}\n\n"
                "Annote d'abord des images avec l'annotateur.")
            return
        
        if messagebox.askyesno("Confirmation", 
            f"Cela va préparer le dataset pour YOLO :\n\n"
            f"📁 {len(txt_files)} annotation(s) trouvée(s) dans Personnage/\n"
            f"📦 Les images seront copiées vers :\n"
            f"   - player_dataset/train/ (80%)\n"
            f"   - player_dataset/validation/ (20%)\n\n"
            f"✅ Les originaux resteront dans Personnage/\n\n"
            f"Continuer ?"):
            try:
                prepare_player_dataset.prepare_player_dataset()
                messagebox.showinfo("Succès", 
                    "✅ Dataset préparé avec succès !\n\n"
                    "📁 Structure créée :\n"
                    "   - train/images/ et train/labels/\n"
                    "   - validation/images/ et validation/labels/\n"
                    "   - data.yaml (configuration YOLO)\n\n"
                    "📦 Les originaux sont conservés dans Personnage/\n\n"
                    "🚀 Tu peux maintenant lancer l'entraînement !")
            except Exception as e:
                import traceback
                error_msg = f"Erreur lors de la préparation :\n{e}\n\n"
                error_msg += traceback.format_exc()
                messagebox.showerror("Erreur", error_msg)
    
    def train_player_model(self):
        """Lance l'entraînement du modèle YOLO pour le personnage."""
        if messagebox.askyesno("Attention", 
            "L'entraînement peut prendre du temps (plusieurs minutes).\nContinuer ?"):
            threading.Thread(target=train_player.train_player_model, daemon=True).start()
            messagebox.showinfo("Info", "Entraînement lancé en arrière-plan.\nRegarde la console pour suivre la progression.")

    # ----------------------------------------------------------------
    # 6. ANNOTATEUR PERSONNAGE
    # ----------------------------------------------------------------
    def _update_annotate_directories(self):
        """Met à jour les dossiers selon le template actif."""
        template_name = self.current_template.get()
        if template_name in self.templates:
            template = self.templates[template_name]
            folder = template["folder"]
            base_dir = os.path.abspath("player_dataset/images")
            self.annotate_image_dir = os.path.join(base_dir, folder)
            self.annotate_annotated_dir = os.path.join(base_dir, folder)
            self.annotate_current_class_id = template["class_id"]
    
    def annotate_on_class_change(self, choice):
        """Quand on change de classe dans l'annotateur."""
        if choice in self.templates:
            self.current_template.set(choice)
            self._update_annotate_directories()
            # Recharger les images du nouveau dossier
            self.annotate_load_images()
    
    def create_annotate_view(self):
        """Crée la vue intégrée pour l'annotateur de personnage."""
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["annotate"] = frame
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header, text="✏️ Annotateur YOLO Multi-Classes", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        # Container principal avec layout horizontal
        main_container = ctk.CTkFrame(frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Zone d'image (gauche)
        image_frame = ctk.CTkFrame(main_container)
        image_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        image_frame.grid_columnconfigure(0, weight=1)
        image_frame.grid_rowconfigure(0, weight=1)
        
        # Canvas Tkinter pour l'image (nécessaire pour PhotoImage)
        from tkinter import Canvas as TkCanvas
        self.annotate_canvas = TkCanvas(image_frame, bg="black", highlightthickness=0, cursor="crosshair")
        self.annotate_canvas.grid(row=0, column=0, sticky="nsew")
        self.annotate_canvas_id = None
        self.annotate_current_photo = None
        
        # Zone de contrôles (droite)
        control_frame = ctk.CTkFrame(main_container, width=300)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        control_frame.grid_propagate(False)
        
        # Sélecteur de classe/template (AVANT les instructions)
        class_frame = ctk.CTkFrame(control_frame)
        class_frame.pack(pady=(10, 5))
        
        ctk.CTkLabel(class_frame, text="Classe à annoter :", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(5, 2))
        
        template_names = list(self.templates.keys())
        self.annotate_class_combo = ctk.CTkComboBox(class_frame, 
                                                   values=template_names,
                                                   width=200,
                                                   command=self.annotate_on_class_change)
        self.annotate_class_combo.pack(pady=5)
        self.annotate_class_combo.set(self.current_template.get())
        # Note: annotate_on_class_change sera appelé après la création de tous les widgets
        
        # Instructions
        ctk.CTkLabel(control_frame, text="Instructions:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        instructions = """1. Clique et glisse pour dessiner une bounding box autour du personnage

2. Clique sur "Valider" pour sauvegarder l'annotation

3. Clique sur "Passer" pour ignorer cette image

4. Utilise les flèches pour naviguer entre les images"""
        ctk.CTkLabel(control_frame, text=instructions, 
                    justify="left", font=ctk.CTkFont(size=11)).pack(pady=5, padx=10)
        
        # Navigation
        nav_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        nav_frame.pack(pady=15)
        
        self.btn_prev_img = ctk.CTkButton(nav_frame, text="◀ Précédent", 
                                          command=self.annotate_prev_image,
                                          width=120, fg_color="#3B8ED0")
        self.btn_prev_img.pack(side="left", padx=5)
        
        self.btn_next_img = ctk.CTkButton(nav_frame, text="Suivant ▶", 
                                          command=self.annotate_next_image,
                                          width=120, fg_color="#2CC985")
        self.btn_next_img.pack(side="left", padx=5)
        
        # Statut
        self.annotate_status_label = ctk.CTkLabel(control_frame, text="Image 0/0", 
                                                 font=ctk.CTkFont(size=12))
        self.annotate_status_label.pack(pady=10)
        
        # Actions
        self.btn_validate = ctk.CTkButton(control_frame, text="✅ Valider Annotation (Entrée)", 
                                          command=self.annotate_save,
                                          height=50, fg_color="#2CC985", 
                                          font=ctk.CTkFont(size=12, weight="bold"))
        self.btn_validate.pack(pady=10, padx=10, fill="x")
        
        self.btn_skip = ctk.CTkButton(control_frame, text="⏭ Passer (Sans annotation)", 
                                      command=self.annotate_skip,
                                      height=40, fg_color="#FFA500")
        self.btn_skip.pack(pady=5, padx=10, fill="x")
        
        self.btn_delete = ctk.CTkButton(control_frame, text="🗑 Supprimer Annotation", 
                                        command=self.annotate_delete,
                                        height=40, fg_color="#FF4D4D")
        self.btn_delete.pack(pady=5, padx=10, fill="x")
        
        # Raccourcis
        ctk.CTkLabel(control_frame, text="Raccourcis :", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(control_frame, text="← → : Navigation\nEntrée : Valider", 
                    justify="left", font=ctk.CTkFont(size=10), text_color="gray").pack(pady=5)
        
        # Info bbox
        self.annotate_bbox_label = ctk.CTkLabel(control_frame, text="Aucune bbox dessinée", 
                                                text_color="yellow", font=ctk.CTkFont(size=10))
        self.annotate_bbox_label.pack(pady=10)
        
        # Variables pour l'annotateur
        self.annotate_current_class_id = 0  # Class ID actuel (0=Personnage, 1=Mobs, etc.)
        self.annotate_image_dir = None
        self.annotate_annotated_dir = None
        self._update_annotate_directories()  # Initialiser les dossiers selon le template actif
        self.annotate_image_files = []
        self.annotate_current_index = 0
        self.annotate_current_image_path = None
        self.annotate_current_image = None
        self.annotate_scale = 1.0
        self.annotate_start_x = None
        self.annotate_start_y = None
        self.annotate_bboxes = []  # Liste de toutes les bboxes : [(x1, y1, x2, y2, class_id), ...]
        self.annotate_selected_bbox_index = -1  # Index de la bbox sélectionnée (-1 = aucune)
        self.annotate_drawing = False
        self.annotate_dragging_bbox = False  # True si on déplace une bbox existante
        self.annotate_bbox_is_new = False  # Flag pour savoir si des bboxes sont nouvelles (non sauvegardées)
        
        # Bind events sur le canvas
        self.annotate_canvas.bind("<Button-1>", self.annotate_on_click)
        self.annotate_canvas.bind("<B1-Motion>", self.annotate_on_drag)
        self.annotate_canvas.bind("<ButtonRelease-1>", self.annotate_on_release)
        
        # Bind clavier sur la fenêtre principale
        self.bind("<Left>", lambda e: self.annotate_prev_image())
        self.bind("<Right>", lambda e: self.annotate_next_image())
        self.bind("<Return>", lambda e: self.annotate_save())
        
        # Initialiser et charger les images (après création de tous les widgets)
        self.annotate_on_class_change(self.current_template.get())
    
    def annotate_load_images(self):
        """Charge la liste des images à annoter."""
        if not os.path.exists(self.annotate_image_dir):
            if not os.path.exists(self.annotate_annotated_dir):
                os.makedirs(self.annotate_annotated_dir)
            self.annotate_image_dir = self.annotate_annotated_dir
        
        if not os.path.exists(self.annotate_image_dir):
            self.annotate_status_label.configure(text="Dossier non trouvé")
            return
        
        # Chercher toutes les images
        self.annotate_image_files = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        for filename in os.listdir(self.annotate_image_dir):
            if any(filename.lower().endswith(ext.lower()) for ext in image_extensions):
                if '_annotated' not in filename and not filename.endswith('.txt'):
                    full_path = os.path.join(self.annotate_image_dir, filename)
                    self.annotate_image_files.append(full_path)
        
        self.annotate_image_files.sort()
        self.annotate_current_index = 0
        
        if self.annotate_image_files:
            self.annotate_load_current_image()
        else:
            self.annotate_status_label.configure(text="Aucune image trouvée")
    
    def annotate_load_current_image(self):
        """Charge l'image actuelle."""
        if not self.annotate_image_files:
            return
        
        self.annotate_current_image_path = self.annotate_image_files[self.annotate_current_index]
        
        import cv2
        from PIL import Image, ImageTk
        
        img = cv2.imread(self.annotate_current_image_path)
        if img is None:
            messagebox.showerror("Erreur", f"Impossible de charger {self.annotate_current_image_path}")
            return
        
        self.annotate_current_image = img.copy()
        h, w = img.shape[:2]
        
        # Redimensionner pour l'affichage (max 1000px de largeur)
        max_width = 1000
        if w > max_width:
            self.annotate_scale = max_width / w
            new_w = max_width
            new_h = int(h * self.annotate_scale)
            img = cv2.resize(img, (new_w, new_h))
        else:
            self.annotate_scale = 1.0
        
        # Convertir en format PIL puis PhotoImage
        import numpy as np
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(np.uint8(img_rgb))
        photo_image = ImageTk.PhotoImage(pil_image)
        
        # Garder la référence
        self.annotate_current_photo = photo_image
        
        # Réinitialiser les bboxes avant de charger une nouvelle image
        self.annotate_bboxes = []
        self.annotate_selected_bbox_index = -1
        self.annotate_drawing = False
        self.annotate_dragging_bbox = False
        
        # Nettoyer le Canvas
        self.annotate_canvas.delete("all")
        
        # Obtenir les dimensions du Canvas
        self.annotate_canvas.update_idletasks()
        canvas_width = self.annotate_canvas.winfo_width()
        canvas_height = self.annotate_canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = new_w
        if canvas_height <= 1:
            canvas_height = new_h
        
        # Centrer l'image
        x = canvas_width // 2
        y = canvas_height // 2
        
        # Afficher l'image
        self.annotate_canvas_id = self.annotate_canvas.create_image(x, y, image=photo_image, anchor="center")
        self.annotate_canvas.update_idletasks()
        
        # Charger annotation existante
        self.annotate_load_existing_annotation()
        
        # Mettre à jour le statut
        self.annotate_update_status()
    
    def annotate_load_existing_annotation(self):
        """Charge toutes les annotations existantes pour cette image."""
        base_name = os.path.splitext(os.path.basename(self.annotate_current_image_path))[0]
        txt_path = os.path.join(self.annotate_annotated_dir, f"{base_name}.txt")
        if not os.path.exists(txt_path):
            txt_path = os.path.join(self.annotate_image_dir, f"{base_name}.txt")
        
        self.annotate_bboxes = []
        
        if os.path.exists(txt_path):
            h, w = self.annotate_current_image.shape[:2]
            display_w = int(w * self.annotate_scale)
            display_h = int(h * self.annotate_scale)
            
            with open(txt_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) == 5:
                        class_id, x_center, y_center, width, height = map(float, parts)
                        
                        if self.annotate_canvas_id:
                            bbox = self.annotate_canvas.bbox(self.annotate_canvas_id)
                            if bbox:
                                img_x1, img_y1, img_x2, img_y2 = bbox
                                img_center_x = (img_x1 + img_x2) / 2
                                img_center_y = (img_y1 + img_y2) / 2
                                
                                x_center_px = img_center_x + (x_center - 0.5) * display_w
                                y_center_px = img_center_y + (y_center - 0.5) * display_h
                                width_px = width * display_w
                                height_px = height * display_h
                                
                                x1 = int(x_center_px - width_px / 2)
                                y1 = int(y_center_px - height_px / 2)
                                x2 = int(x_center_px + width_px / 2)
                                y2 = int(y_center_px + height_px / 2)
                                
                                # Stocker avec le class_id
                                self.annotate_bboxes.append((x1, y1, x2, y2, int(class_id)))
        
        self.annotate_bbox_is_new = False  # Bboxes chargées depuis fichier = déjà sauvegardées
        self.annotate_selected_bbox_index = -1
        self.annotate_draw_all_bboxes()
        self.annotate_update_bbox_label()
    
    def annotate_find_bbox_at(self, x, y):
        """Trouve l'index de la bbox contenant le point (x, y). Retourne -1 si aucune."""
        for i, (x1, y1, x2, y2, _) in enumerate(self.annotate_bboxes):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return -1
    
    def annotate_on_click(self, event):
        """Gère le clic : sélection d'une bbox existante ou début d'un nouveau dessin."""
        click_x = self.annotate_canvas.canvasx(event.x)
        click_y = self.annotate_canvas.canvasy(event.y)
        
        # Chercher si on clique sur une bbox existante
        bbox_idx = self.annotate_find_bbox_at(click_x, click_y)
        
        if bbox_idx >= 0:
            # On clique sur une bbox existante : la sélectionner pour déplacement
            self.annotate_selected_bbox_index = bbox_idx
            self.annotate_dragging_bbox = True
            x1, y1, x2, y2, _ = self.annotate_bboxes[bbox_idx]
            # Calculer l'offset du clic par rapport au coin supérieur gauche
            self.annotate_start_x = click_x - x1
            self.annotate_start_y = click_y - y1
            self.annotate_drawing = False
        else:
            # Nouveau dessin
            self.annotate_start_x = click_x
            self.annotate_start_y = click_y
            self.annotate_drawing = True
            self.annotate_dragging_bbox = False
            self.annotate_selected_bbox_index = -1
        
        self.annotate_draw_all_bboxes()
    
    def annotate_on_drag(self, event):
        """Pendant le dessin ou le déplacement d'une bbox."""
        current_x = self.annotate_canvas.canvasx(event.x)
        current_y = self.annotate_canvas.canvasy(event.y)
        
        if self.annotate_dragging_bbox and self.annotate_selected_bbox_index >= 0:
            # Déplacer la bbox sélectionnée
            x1, y1, x2, y2, class_id = self.annotate_bboxes[self.annotate_selected_bbox_index]
            width = x2 - x1
            height = y2 - y1
            
            # Nouvelle position basée sur l'offset
            new_x1 = current_x - self.annotate_start_x
            new_y1 = current_y - self.annotate_start_y
            new_x2 = new_x1 + width
            new_y2 = new_y1 + height
            
            # Mettre à jour la bbox
            self.annotate_bboxes[self.annotate_selected_bbox_index] = (int(new_x1), int(new_y1), int(new_x2), int(new_y2), class_id)
            self.annotate_bbox_is_new = True
            self.annotate_draw_all_bboxes()
        elif self.annotate_drawing:
            # Dessiner une nouvelle bbox
            self.annotate_canvas.delete("bbox_temp")
            x1 = min(self.annotate_start_x, current_x)
            y1 = min(self.annotate_start_y, current_y)
            x2 = max(self.annotate_start_x, current_x)
            y2 = max(self.annotate_start_y, current_y)
            self.annotate_canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="yellow", width=2, tags="bbox_temp"
            )
    
    def annotate_on_release(self, event):
        """Fin du dessin ou du déplacement d'une bbox."""
        if self.annotate_dragging_bbox:
            # Fin du déplacement
            self.annotate_dragging_bbox = False
            self.annotate_draw_all_bboxes()
            self.annotate_update_bbox_label()
        elif self.annotate_drawing:
            # Fin du dessin d'une nouvelle bbox
            end_x = self.annotate_canvas.canvasx(event.x)
            end_y = self.annotate_canvas.canvasy(event.y)
            
            x1 = min(self.annotate_start_x, end_x)
            y1 = min(self.annotate_start_y, end_y)
            x2 = max(self.annotate_start_x, end_x)
            y2 = max(self.annotate_start_y, end_y)
            
            # Vérifier que la bbox a une taille minimale
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                # Ajouter la nouvelle bbox avec le class_id actuel
                self.annotate_bboxes.append((int(x1), int(y1), int(x2), int(y2), self.annotate_current_class_id))
                self.annotate_selected_bbox_index = len(self.annotate_bboxes) - 1  # Sélectionner la nouvelle
                self.annotate_bbox_is_new = True
            
            self.annotate_drawing = False
            self.annotate_canvas.delete("bbox_temp")
            self.annotate_draw_all_bboxes()
            self.annotate_update_bbox_label()
    
    def annotate_draw_all_bboxes(self):
        """Dessine toutes les bboxes sur le canvas."""
        self.annotate_canvas.delete("bbox")
        
        for i, (x1, y1, x2, y2, class_id) in enumerate(self.annotate_bboxes):
            # Rouge si sélectionnée, vert sinon
            color = "red" if i == self.annotate_selected_bbox_index else "green"
            width = 3 if i == self.annotate_selected_bbox_index else 2
            self.annotate_canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=width, tags="bbox")
    
    def annotate_update_bbox_label(self):
        """Met à jour le label avec les infos des bboxes."""
        if not hasattr(self, 'annotate_bbox_label') or not self.annotate_bbox_label:
            return  # Le widget n'existe pas encore
        
        count = len(self.annotate_bboxes)
        if count > 0:
            if self.annotate_selected_bbox_index >= 0:
                x1, y1, x2, y2, class_id = self.annotate_bboxes[self.annotate_selected_bbox_index]
                w = x2 - x1
                h = y2 - y1
                self.annotate_bbox_label.configure(
                    text=f"📦 {count} bbox(es) | Sélectionnée: ({x1}, {y1}) - ({x2}, {y2})\nTaille: {w}x{h}px | Classe: {class_id}"
                )
            else:
                self.annotate_bbox_label.configure(text=f"📦 {count} bbox(es) | Aucune sélectionnée")
        else:
            self.annotate_bbox_label.configure(text="Aucune bbox dessinée")
    
    def annotate_save(self):
        """Sauvegarde toutes les annotations au format YOLO."""
        if not self.annotate_bboxes:
            messagebox.showwarning("Aucune bbox", "Dessine d'abord au moins une bounding box !")
            return
        
        import cv2
        
        h, w = self.annotate_current_image.shape[:2]
        display_w = int(w * self.annotate_scale)
        display_h = int(h * self.annotate_scale)
        
        base_name = os.path.splitext(os.path.basename(self.annotate_current_image_path))[0]
        txt_path = os.path.join(self.annotate_annotated_dir, f"{base_name}.txt")
        
        # Lire les annotations existantes pour préserver celles des autres classes
        existing_annotations = {}
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) == 5:
                        class_id = int(float(parts[0]))
                        # Garder seulement les annotations des autres classes
                        if class_id != self.annotate_current_class_id:
                            existing_annotations[class_id] = existing_annotations.get(class_id, []) + [line]
        
        # Convertir toutes les bboxes au format YOLO
        yolo_lines = []
        
        for x1, y1, x2, y2, class_id in self.annotate_bboxes:
            # Obtenir la position de l'image dans le Canvas
            if self.annotate_canvas_id:
                img_bbox = self.annotate_canvas.bbox(self.annotate_canvas_id)
                if img_bbox:
                    img_x1, img_y1, img_x2, img_y2 = img_bbox
                    img_center_x = (img_x1 + img_x2) / 2
                    img_center_y = (img_y1 + img_y2) / 2
                    
                    x1_img = (x1 - img_center_x) + display_w / 2
                    y1_img = (y1 - img_center_y) + display_h / 2
                    x2_img = (x2 - img_center_x) + display_w / 2
                    y2_img = (y2 - img_center_y) + display_h / 2
                    
                    x1_orig = x1_img / self.annotate_scale
                    y1_orig = y1_img / self.annotate_scale
                    x2_orig = x2_img / self.annotate_scale
                    y2_orig = y2_img / self.annotate_scale
                else:
                    x1_orig = x1 / self.annotate_scale
                    y1_orig = y1 / self.annotate_scale
                    x2_orig = x2 / self.annotate_scale
                    y2_orig = y2 / self.annotate_scale
            else:
                x1_orig = x1 / self.annotate_scale
                y1_orig = y1 / self.annotate_scale
                x2_orig = x2 / self.annotate_scale
                y2_orig = y2 / self.annotate_scale
            
            # Calculer le centre et la taille (normalisés 0-1)
            width_norm = (x2_orig - x1_orig) / w
            height_norm = (y2_orig - y1_orig) / h
            x_center_norm = ((x1_orig + x2_orig) / 2) / w
            y_center_norm = ((y1_orig + y2_orig) / 2) / h
            
            # Ajouter la ligne YOLO pour cette bbox
            yolo_lines.append(f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {width_norm:.6f} {height_norm:.6f}")
        
        # Nom de base de l'image
        base_name = os.path.splitext(os.path.basename(self.annotate_current_image_path))[0]
        img_ext = os.path.splitext(self.annotate_current_image_path)[1]
        
        # Copier l'image si nécessaire
        dest_img_path = os.path.join(self.annotate_annotated_dir, f"{base_name}{img_ext}")
        if not os.path.exists(dest_img_path):
            import shutil
            shutil.copy2(self.annotate_current_image_path, dest_img_path)
        
        # Écrire toutes les annotations : d'abord celles des autres classes, puis celles de la classe actuelle
        all_lines = []
        for class_id_lines in existing_annotations.values():
            all_lines.extend(class_id_lines)
        all_lines.extend(yolo_lines)
        
        with open(txt_path, 'w') as f:
            for line in all_lines:
                f.write(line + '\n')
        
        # Message de confirmation avec le chemin
        annotation_dir = os.path.relpath(self.annotate_annotated_dir)
        self.annotate_status_label.configure(
            text=f"✅ {len(yolo_lines)} annotation(s) sauvegardée(s) dans\n{annotation_dir}/"
        )
        self.after(3000, self.annotate_update_status)
        
        # Marquer les bboxes comme sauvegardées
        self.annotate_bbox_is_new = False
        
        # Recharger pour afficher les bboxes sauvegardées
        self.annotate_load_existing_annotation()
    
    def annotate_skip(self):
        """Passe à l'image suivante sans annoter."""
        self.annotate_next_image()
    
    def annotate_delete(self):
        """Supprime la bbox sélectionnée."""
        if self.annotate_selected_bbox_index < 0:
            messagebox.showwarning("Aucune sélection", "Sélectionne d'abord une bbox à supprimer !\n(Clique dessus)")
            return
        
        # Supprimer la bbox sélectionnée
        self.annotate_bboxes.pop(self.annotate_selected_bbox_index)
        self.annotate_selected_bbox_index = -1
        self.annotate_bbox_is_new = True
        self.annotate_draw_all_bboxes()
        self.annotate_update_bbox_label()
    
    def annotate_prev_image(self):
        """Image précédente."""
        if self.annotate_current_index > 0:
            self.annotate_current_index -= 1
            # Réinitialiser le flag avant de charger la nouvelle image
            self.annotate_bboxes = []
            self.annotate_selected_bbox_index = -1
            self.annotate_drawing = False
            self.annotate_dragging_bbox = False
            self.annotate_bbox_is_new = False
            self.annotate_load_current_image()
    
    def annotate_next_image(self):
        """Image suivante."""
        # Vérifier seulement si c'est une NOUVELLE bbox non sauvegardée
        if self.annotate_bboxes and self.annotate_bbox_is_new:
            if not messagebox.askyesno("Bbox non sauvegardée", 
                "Tu as dessiné des bboxes mais ne les as pas validées.\n\n"
                "Veux-tu vraiment passer à l'image suivante sans sauvegarder ?"):
                return
        
        if self.annotate_current_index < len(self.annotate_image_files) - 1:
            self.annotate_current_index += 1
            # Réinitialiser le flag avant de charger la nouvelle image
            self.annotate_bboxes = []
            self.annotate_selected_bbox_index = -1
            self.annotate_drawing = False
            self.annotate_dragging_bbox = False
            self.annotate_bbox_is_new = False
            self.annotate_load_current_image()
        else:
            annotated = sum(1 for img_file in self.annotate_image_files 
                          if os.path.exists(os.path.join(self.annotate_image_dir, 
                              os.path.splitext(os.path.basename(img_file))[0] + ".txt")))
            messagebox.showinfo("Fin des images", 
                f"Toutes les images ont été parcourues !\n\n"
                f"{annotated}/{len(self.annotate_image_files)} image(s) annotée(s)")
    
    def annotate_update_status(self):
        """Met à jour le label de statut."""
        total = len(self.annotate_image_files)
        current = self.annotate_current_index + 1
        
        # Compter les annotations de la classe actuelle
        annotated = 0
        if os.path.exists(self.annotate_annotated_dir):
            class_id_str = str(self.annotate_current_class_id)
            for txt_file in os.listdir(self.annotate_annotated_dir):
                if txt_file.endswith('.txt'):
                    txt_path = os.path.join(self.annotate_annotated_dir, txt_file)
                    with open(txt_path, 'r') as f:
                        for line in f:
                            if line.strip().startswith(class_id_str + " "):
                                annotated += 1
                                break
        
        template_name = self.current_template.get()
        self.annotate_status_label.configure(
            text=f"Image {current}/{total}\n{annotated} {template_name} annoté(s)"
        )

    # ----------------------------------------------------------------
    # 7. TRAIN
    # ----------------------------------------------------------------
    def create_train_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        self.frames["train"] = frame
        ctk.CTkLabel(frame, text="Entraînement Modèle IA", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=50)
        ctk.CTkButton(frame, text="Lancer Entraînement", height=50, fg_color="#D97706", hover_color="#B45309", 
                      command=self.run_training).pack()

    def run_training(self):
        if messagebox.askyesno("Attention", "Cela peut prendre du temps. Continuer ?"):
            threading.Thread(target=train_fish.train_fish_model).start()

    # ----------------------------------------------------------------
    # START / STOP LOGIC
    # ----------------------------------------------------------------
    def start_bot(self):
        if self.is_running: return
        
        # Save current UI settings to disk (active config)
        self.save_current_ui_to_dict("last_run_temp") 
        self.settings = self.load_json(SETTINGS_FILE, {}) # Reload to be sure
        
        try:
            # Parse settings
            start_pos = [int(self.settings["start_x"]), int(self.settings["start_y"])]
            route_str = self.settings["route_list"]
            route = []
            for p in route_str.split(';'):
                if p.strip():
                    parts = p.split(',')
                    route.append([int(parts[0]), int(parts[1])])
            
            if not route: raise ValueError("Route vide")
            
            infinite = self.settings["infinite_loop"]
            wait = float(self.settings["fishing_wait_time"])
            max_wait = float(self.settings["max_map_wait"])
            spell_count = int(self.settings.get("combat_spell_count", 3))

            self.stop_event.clear()
            self.is_running = True
            self.lbl_status_run.configure(text="EN COURS...", text_color="#2CC985")
            self.btn_start.configure(state="disabled")
            self.btn_resume.configure(state="disabled")
            self.btn_stop.configure(state="normal")

            circuit_name = self.current_circuit_name.get()
            self.bot_thread = threading.Thread(target=self._run_bot_wrapper, args=(start_pos, route, infinite, wait, max_wait, spell_count, False, circuit_name))
            self.bot_thread.start()

        except Exception as e:
            messagebox.showerror("Erreur Lancement", f"Paramètres invalides : {e}")

    def resume_bot(self):
        """Reprend le circuit depuis l'état sauvegardé"""
        if self.is_running: return
        
        # Vérifier qu'un état existe
        if not os.path.exists("circuit_state.json"):
            messagebox.showwarning("Aucun état sauvegardé", "Aucun circuit en cours n'a été sauvegardé. Utilisez 'LANCER LE BOT' pour démarrer un nouveau circuit.")
            return
        
        # Save current UI settings to disk (active config)
        self.save_current_ui_to_dict("last_run_temp") 
        self.settings = self.load_json(SETTINGS_FILE, {}) # Reload to be sure
        
        try:
            # Parse settings
            start_pos = [int(self.settings["start_x"]), int(self.settings["start_y"])]
            route_str = self.settings["route_list"]
            route = []
            for p in route_str.split(';'):
                if p.strip():
                    parts = p.split(',')
                    route.append([int(parts[0]), int(parts[1])])
            
            if not route: raise ValueError("Route vide")
            
            infinite = self.settings["infinite_loop"]
            wait = float(self.settings["fishing_wait_time"])
            max_wait = float(self.settings["max_map_wait"])
            spell_count = int(self.settings.get("combat_spell_count", 3))

            self.stop_event.clear()
            self.is_running = True
            self.lbl_status_run.configure(text="REPRISE...", text_color="#FFA500")
            self.btn_start.configure(state="disabled")
            self.btn_resume.configure(state="disabled")
            self.btn_stop.configure(state="normal")

            circuit_name = self.current_circuit_name.get()
            self.bot_thread = threading.Thread(target=self._run_bot_wrapper, args=(start_pos, route, infinite, wait, max_wait, spell_count, True, circuit_name))
            self.bot_thread.start()

        except Exception as e:
            messagebox.showerror("Erreur Reprise", f"Paramètres invalides : {e}")

    def _run_bot_wrapper(self, *args):
        try:
            # args peut contenir resume_from_state et circuit_name en plus
            if len(args) >= 8:
                bot_main.main(start_pos=args[0], route_list=args[1], stop_event=self.stop_event, 
                              infinite_loop=args[2], fishing_wait_time=args[3], max_map_wait=args[4], 
                              spell_count=args[5], resume_from_state=args[6], circuit_name=args[7])
            else:
                bot_main.main(start_pos=args[0], route_list=args[1], stop_event=self.stop_event, 
                              infinite_loop=args[2], fishing_wait_time=args[3], max_map_wait=args[4], spell_count=args[5])
        except Exception as e:
            print(f"Erreur Bot: {e}")
        finally:
            self.after(0, self.on_bot_finished)

    def stop_bot(self):
        if self.is_running:
            self.stop_event.set()
            print("--- ARRÊT DEMANDÉ ---")

    def on_bot_finished(self):
        self.is_running = False
        self.lbl_status_run.configure(text="STOPPÉ", text_color="red")
        self.btn_start.configure(state="normal")
        self.btn_resume.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def _get_current_player_position_for_calibration(self):
        """Helper pour détecter la position du personnage pendant la calibration via le rond rouge"""
        try:
            import cv2
            import numpy as np
            screen_w, screen_h = pyautogui.size()
            combat_region = (
                int(screen_w * 0.1),
                int(screen_h * 0.1),
                int(screen_w * 0.8),
                int(screen_h * 0.7)
            )
            img = pyautogui.screenshot(region=combat_region)
            img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Détecter le rond rouge autour du personnage
            lower_red = np.array([0, 0, 200])
            upper_red = np.array([50, 50, 255])
            mask = cv2.inRange(img_np, lower_red, upper_red)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 100 < area < 5000:
                    perimeter = cv2.arcLength(cnt, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        if circularity > 0.5:  # Forme circulaire
                            M = cv2.moments(cnt)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                return (combat_region[0] + cx, combat_region[1] + cy)
        except Exception as e:
            print(f"Erreur détection rond rouge : {e}")
        return None

if __name__ == "__main__":
    app = DofusBotApp()
    app.mainloop()
