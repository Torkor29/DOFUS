import cv2
import os
import json
from tkinter import Tk, Canvas, Button, Label, messagebox, filedialog
from PIL import Image, ImageTk
import glob

class PlayerAnnotator:
    def __init__(self, root, image_dir="player_dataset/images/Personnage", annotated_dir="player_dataset/images/Personnage"):
        self.root = root
        self.root.title("Annotateur Personnage YOLO")
        self.root.geometry("1200x800")
        
        # Utiliser les chemins absolus
        self.image_dir = os.path.abspath(image_dir)
        self.annotated_dir = os.path.abspath(annotated_dir)
        
        # Créer le dossier Personnage s'il n'existe pas
        if not os.path.exists(self.annotated_dir):
            os.makedirs(self.annotated_dir)
            print(f"📁 Dossier créé : {self.annotated_dir}")
        self.current_image_path = None
        self.current_image = None
        self.display_image = None
        self.scale = 1.0
        # Référence à l'image PhotoImage actuelle (maintenue par le Canvas)
        # Le Canvas maintient automatiquement les références via create_image()
        self.current_photo_image = None
        
        # État de l'annotation
        self.start_x = None
        self.start_y = None
        self.bbox = None
        self.drawing = False
        
        # Liste des images
        self.image_files = []
        self.current_index = 0
        
        self.setup_ui()
        self.load_images()
        # Ne pas précharger toutes les images, on les chargera à la volée
        # Le préchargement cause des problèmes de garbage collection
        
    def setup_ui(self):
        # Frame principal
        from tkinter import Frame
        
        # Container principal
        main_container = Frame(self.root, bg="gray20")
        main_container.pack(fill="both", expand=True)
        
        # Frame pour l'image
        image_container = Frame(main_container, bg="gray20")
        image_container.pack(side="left", fill="both", expand=True)
        
        # Frame pour contenir le Canvas
        self.image_frame_container = Frame(image_container, bg="black")
        self.image_frame_container.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Canvas unique pour afficher l'image ET dessiner les bbox
        # Le Canvas maintient automatiquement les références PhotoImage via create_image()
        self.image_canvas = Canvas(self.image_frame_container, bg="black", highlightthickness=0, cursor="crosshair")
        self.image_canvas.pack(fill="both", expand=True)
        
        # ID de l'image dans le Canvas (pour pouvoir la mettre à jour)
        self.canvas_image_id = None
        
        # Référence à l'image PhotoImage actuelle (CRUCIAL pour éviter garbage collection)
        self.current_photo_image = None
        
        # Bind events pour dessiner sur le Canvas
        self.image_canvas.bind("<Button-1>", self.on_click)
        self.image_canvas.bind("<B1-Motion>", self.on_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Navigation au clavier
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Return>", lambda e: self.save_annotation())
        self.root.focus_set()
        
        # Frame pour les contrôles
        control_frame = Canvas(main_container, bg="gray30", width=300)
        control_frame.pack(side="right", fill="y", padx=10, pady=10)
        
        # Instructions
        Label(control_frame, text="Instructions:", font=("Arial", 12, "bold"), bg="gray30", fg="white").pack(pady=10)
        instructions = """
1. Clique et glisse pour dessiner
   une bounding box autour du
   personnage

2. Clique sur "Valider" pour
   sauvegarder l'annotation

3. Clique sur "Passer" pour
   ignorer cette image

4. Utilise les flèches pour
   naviguer entre les images
        """
        Label(control_frame, text=instructions, justify="left", bg="gray30", fg="white").pack(pady=10)
        
        # Navigation
        nav_frame = Canvas(control_frame, bg="gray30")
        nav_frame.pack(pady=20)
        
        Button(nav_frame, text="◀ Précédent", command=self.prev_image, width=15, 
              bg="#3B8ED0", fg="white").pack(side="left", padx=5)
        Button(nav_frame, text="Suivant ▶", command=self.next_image, width=15,
              bg="#2CC985", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        # Statut
        self.status_label = Label(control_frame, text="Image 0/0", bg="gray30", fg="white", font=("Arial", 10))
        self.status_label.pack(pady=10)
        
        # Actions
        Button(control_frame, text="✅ Valider Annotation (Entrée)", command=self.save_annotation, 
              bg="#2CC985", fg="white", font=("Arial", 12, "bold"), width=28, height=3).pack(pady=10)
        Button(control_frame, text="⏭ Passer (Sans annotation)", command=self.skip_image,
              bg="#FFA500", fg="white", font=("Arial", 11), width=28, height=2).pack(pady=5)
        Button(control_frame, text="🗑 Supprimer Annotation", command=self.delete_annotation,
              bg="#FF4D4D", fg="white", font=("Arial", 11), width=28, height=2).pack(pady=5)
        
        # Raccourcis clavier
        Label(control_frame, text="Raccourcis :", font=("Arial", 10, "bold"), bg="gray30", fg="white").pack(pady=(20,5))
        Label(control_frame, text="← → : Navigation\nEntrée : Valider", 
              justify="left", bg="gray30", fg="lightgray", font=("Arial", 9)).pack(pady=5)
        
        # Info bbox
        self.bbox_label = Label(control_frame, text="Aucune bbox dessinée", bg="gray30", fg="yellow")
        self.bbox_label.pack(pady=10)
        
    def load_images(self):
        """Charge la liste des images à annoter."""
        # Utiliser le chemin absolu pour éviter les problèmes
        self.image_dir = os.path.abspath(self.image_dir)
        
        if not os.path.exists(self.image_dir):
            error_msg = f"Dossier non trouvé :\n{self.image_dir}\n\n"
            error_msg += f"Chemin absolu : {os.path.abspath(self.image_dir)}\n\n"
            error_msg += "Vérifie que le dossier existe ou déplace les images avec le bouton 'Déplacer Images'."
            messagebox.showerror("Erreur", error_msg)
            self.root.destroy()
            return
        
        # Chercher toutes les images (exclure les images annotées de debug)
        # Chercher directement tous les fichiers image dans le dossier
        self.image_files = []
        
        if os.path.exists(self.image_dir):
            # Lister tous les fichiers du dossier
            all_files = os.listdir(self.image_dir)
            
            # Filtrer pour ne garder que les images
            image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
            for filename in all_files:
                # Vérifier l'extension
                if any(filename.lower().endswith(ext.lower()) for ext in image_extensions):
                    # Exclure les fichiers _annotated et les fichiers .txt
                    if '_annotated' not in filename and not filename.endswith('.txt'):
                        full_path = os.path.join(self.image_dir, filename)
                        self.image_files.append(full_path)
        
        self.image_files.sort()
        
        print(f"📁 {len(self.image_files)} image(s) trouvée(s) dans {self.image_dir}")
        
        if not self.image_files:
            # Lister tous les fichiers pour debug
            all_files = os.listdir(self.image_dir) if os.path.exists(self.image_dir) else []
            error_msg = f"Aucune image trouvée dans :\n{self.image_dir}\n\n"
            error_msg += f"Fichiers présents ({len(all_files)}) :\n"
            for f in all_files[:10]:  # Afficher les 10 premiers
                error_msg += f"  - {f}\n"
            if len(all_files) > 10:
                error_msg += f"  ... et {len(all_files) - 10} autres\n"
            error_msg += "\nVérifie que les images sont bien dans ce dossier."
            messagebox.showwarning("Aucune image", error_msg)
            self.root.destroy()
            return
        
        self.current_index = 0
        
        # Attendre que la fenêtre soit complètement initialisée avant de charger l'image
        self.root.after(100, self._initialize_annotator)
    
    def _initialize_annotator(self):
        """Initialise l'annotateur après que la fenêtre soit prête."""
        self.load_current_image()
        
        # Message de bienvenue
        messagebox.showinfo("Annotateur Prêt", 
            f"{len(self.image_files)} image(s) chargée(s) !\n\n"
            "Instructions :\n"
            "1. Clique et glisse pour dessiner une bbox\n"
            "2. Clique sur 'Valider Annotation'\n"
            "3. Clique sur 'Suivant' pour passer à l'image suivante")
    
    def load_current_image(self):
        """Charge l'image actuelle."""
        if not self.image_files:
            return
        
        self.current_image_path = self.image_files[self.current_index]
        
        # Charger l'image
        img = cv2.imread(self.current_image_path)
        if img is None:
            messagebox.showerror("Erreur", f"Impossible de charger {self.current_image_path}")
            return
        
        self.current_image = img.copy()
        h, w = img.shape[:2]
        
        # Redimensionner pour l'affichage (max 1000px de largeur)
        max_width = 1000
        if w > max_width:
            self.scale = max_width / w
            new_w = max_width
            new_h = int(h * self.scale)
            img = cv2.resize(img, (new_w, new_h))
        else:
            self.scale = 1.0
        
        # Convertir en format PIL puis PhotoImage
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(img_rgb)
        
        # Créer l'image PhotoImage
        # CRUCIAL: Le Canvas maintient automatiquement la référence via create_image()
        photo_image = ImageTk.PhotoImage(pil_image)
        
        # Garder une référence dans self pour éviter le garbage collection
        # (même si le Canvas en garde déjà une)
        self.current_photo_image = photo_image
        
        # Nettoyer le Canvas (supprimer l'ancienne image et les bbox)
        self.image_canvas.delete("all")
        
        # Obtenir les dimensions du Canvas
        self.image_canvas.update_idletasks()
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # Si le Canvas n'a pas encore de dimensions, utiliser les dimensions de l'image
        if canvas_width <= 1:
            canvas_width = new_w
        if canvas_height <= 1:
            canvas_height = new_h
        
        # Centrer l'image dans le Canvas
        x = canvas_width // 2
        y = canvas_height // 2
        
        # Afficher l'image dans le Canvas
        # CRUCIAL: create_image() maintient automatiquement la référence PhotoImage
        # Tant que l'image existe dans le Canvas, elle ne sera pas garbage collectée
        self.canvas_image_id = self.image_canvas.create_image(x, y, image=photo_image, anchor="center")
        
        # Mettre à jour le Canvas pour forcer l'affichage
        self.image_canvas.update_idletasks()
        
        # Charger annotation existante si elle existe
        self.load_existing_annotation()
        
        # Mettre à jour le statut
        self.update_status()
    
    def load_existing_annotation(self):
        """Charge une annotation existante si elle existe."""
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        # Chercher d'abord dans Personnage, puis dans image_dir
        txt_path = os.path.join(self.annotated_dir, f"{base_name}.txt")
        if not os.path.exists(txt_path):
            txt_path = os.path.join(self.image_dir, f"{base_name}.txt")
        
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as f:
                line = f.readline().strip()
                if line:
                    parts = line.split()
                    if len(parts) == 5:
                        # Format YOLO: class x_center y_center width height (normalisé 0-1)
                        _, x_center, y_center, width, height = map(float, parts)
                        
                        # Convertir en coordonnées pixel pour l'affichage
                        h, w = self.current_image.shape[:2]
                        display_w = int(w * self.scale)
                        display_h = int(h * self.scale)
                        
                        # Obtenir la position de l'image dans le Canvas
                        if self.canvas_image_id:
                            bbox = self.image_canvas.bbox(self.canvas_image_id)
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
                                
                                # Dessiner la bbox
                                self.image_canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2, tags="bbox")
                                self.bbox = (x1, y1, x2, y2)
                                self.update_bbox_label()
    
    def on_click(self, event):
        """Début du dessin de la bbox."""
        # Coordonnées relatives au Canvas
        self.start_x = self.image_canvas.canvasx(event.x)
        self.start_y = self.image_canvas.canvasy(event.y)
        self.drawing = True
        self.bbox = None
        self.image_canvas.delete("bbox")
    
    def on_drag(self, event):
        """Pendant le dessin de la bbox."""
        if not self.drawing:
            return
        
        # Coordonnées relatives au Canvas
        current_x = self.image_canvas.canvasx(event.x)
        current_y = self.image_canvas.canvasy(event.y)
        
        # Effacer l'ancienne bbox
        self.image_canvas.delete("bbox")
        
        # Dessiner la nouvelle
        self.image_canvas.create_rectangle(
            self.start_x, self.start_y, current_x, current_y,
            outline="yellow", width=2, tags="bbox"
        )
    
    def on_release(self, event):
        """Fin du dessin de la bbox."""
        if not self.drawing:
            return
        
        # Coordonnées relatives au Canvas
        end_x = self.image_canvas.canvasx(event.x)
        end_y = self.image_canvas.canvasy(event.y)
        
        # S'assurer que x1 < x2 et y1 < y2
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        self.bbox = (int(x1), int(y1), int(x2), int(y2))
        self.drawing = False
        
        # Redessiner en vert (validée)
        self.image_canvas.delete("bbox")
        self.image_canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2, tags="bbox")
        
        self.update_bbox_label()
    
    def update_bbox_label(self):
        """Met à jour le label avec les infos de la bbox."""
        if self.bbox:
            x1, y1, x2, y2 = self.bbox
            w = x2 - x1
            h = y2 - y1
            self.bbox_label.config(text=f"Bbox: ({x1}, {y1}) - ({x2}, {y2})\nTaille: {w}x{h}px")
        else:
            self.bbox_label.config(text="Aucune bbox dessinée")
    
    def save_annotation(self):
        """Sauvegarde l'annotation au format YOLO dans le dossier Personnage."""
        if not self.bbox:
            messagebox.showwarning("Aucune bbox", "Dessine d'abord une bounding box autour du personnage !")
            return
        
        # Convertir les coordonnées d'affichage en coordonnées YOLO normalisées
        h, w = self.current_image.shape[:2]
        display_w = int(w * self.scale)
        display_h = int(h * self.scale)
        
        x1, y1, x2, y2 = self.bbox
        
        # Obtenir la position de l'image dans le Canvas
        if self.canvas_image_id:
            img_bbox = self.image_canvas.bbox(self.canvas_image_id)
            if img_bbox:
                img_x1, img_y1, img_x2, img_y2 = img_bbox
                img_center_x = (img_x1 + img_x2) / 2
                img_center_y = (img_y1 + img_y2) / 2
                
                # Convertir les coordonnées Canvas en coordonnées relatives à l'image affichée
                # L'image est centrée dans le Canvas
                x1_img = (x1 - img_center_x) + display_w / 2
                y1_img = (y1 - img_center_y) + display_h / 2
                x2_img = (x2 - img_center_x) + display_w / 2
                y2_img = (y2 - img_center_y) + display_h / 2
                
                # Convertir en coordonnées de l'image originale (avant redimensionnement)
                x1_orig = x1_img / self.scale
                y1_orig = y1_img / self.scale
                x2_orig = x2_img / self.scale
                y2_orig = y2_img / self.scale
            else:
                # Fallback : conversion directe
                x1_orig = x1 / self.scale
                y1_orig = y1 / self.scale
                x2_orig = x2 / self.scale
                y2_orig = y2 / self.scale
        else:
            # Fallback : conversion directe
            x1_orig = x1 / self.scale
            y1_orig = y1 / self.scale
            x2_orig = x2 / self.scale
            y2_orig = y2 / self.scale
        
        # Calculer le centre et la taille (normalisés 0-1)
        width_norm = (x2_orig - x1_orig) / w
        height_norm = (y2_orig - y1_orig) / h
        x_center_norm = ((x1_orig + x2_orig) / 2) / w
        y_center_norm = ((y1_orig + y2_orig) / 2) / h
        
        # Nom de base de l'image
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        img_ext = os.path.splitext(self.current_image_path)[1]
        
        # Copier l'image dans le dossier Personnage si elle n'y est pas déjà
        dest_img_path = os.path.join(self.annotated_dir, f"{base_name}{img_ext}")
        if not os.path.exists(dest_img_path):
            import shutil
            shutil.copy2(self.current_image_path, dest_img_path)
        
        # Sauvegarder l'annotation dans le dossier Personnage
        txt_path = os.path.join(self.annotated_dir, f"{base_name}.txt")
        
        with open(txt_path, 'w') as f:
            # Format: class_id x_center y_center width height
            f.write(f"0 {x_center_norm:.6f} {y_center_norm:.6f} {width_norm:.6f} {height_norm:.6f}\n")
        
        # Message de confirmation court
        self.status_label.config(text=f"✅ Annotation sauvegardée dans Personnage/ !")
        self.root.after(2000, self.update_status)  # Remettre le statut normal après 2s
        
        # Recharger pour afficher la bbox sauvegardée
        self.load_existing_annotation()
    
    def skip_image(self):
        """Passe à l'image suivante sans annoter."""
        self.next_image()
    
    def delete_annotation(self):
        """Supprime l'annotation existante."""
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        txt_path = os.path.join(self.annotated_dir, f"{base_name}.txt")
        
        if os.path.exists(txt_path):
            os.remove(txt_path)
            # Supprimer aussi l'image du dossier Personnage si elle y est
            img_ext = os.path.splitext(self.current_image_path)[1]
            dest_img_path = os.path.join(self.annotated_dir, f"{base_name}{img_ext}")
            if os.path.exists(dest_img_path):
                os.remove(dest_img_path)
            messagebox.showinfo("Succès", "Annotation supprimée")
            self.bbox = None
            self.image_canvas.delete("bbox")
            self.load_current_image()
        else:
            messagebox.showinfo("Info", "Aucune annotation à supprimer")
    
    def prev_image(self):
        """Image précédente."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
    
    def next_image(self):
        """Image suivante."""
        # Si on a une bbox non sauvegardée, demander confirmation
        if self.bbox:
            if not messagebox.askyesno("Bbox non sauvegardée", 
                "Tu as dessiné une bbox mais ne l'as pas validée.\n\n"
                "Veux-tu vraiment passer à l'image suivante sans sauvegarder ?"):
                return
        
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_current_image()
        else:
            # Dernière image
            annotated = sum(1 for img_file in self.image_files 
                          if os.path.exists(os.path.join(self.image_dir, 
                              os.path.splitext(os.path.basename(img_file))[0] + ".txt")))
            messagebox.showinfo("Fin des images", 
                f"Toutes les images ont été parcourues !\n\n"
                f"{annotated}/{len(self.image_files)} image(s) annotée(s)\n\n"
                "Tu peux maintenant préparer le dataset pour l'entraînement.")
    
    def update_status(self):
        """Met à jour le label de statut."""
        total = len(self.image_files)
        current = self.current_index + 1
        
        # Compter les images annotées (dans le dossier Personnage)
        annotated = 0
        if os.path.exists(self.annotated_dir):
            annotated_files = [f for f in os.listdir(self.annotated_dir) if f.endswith('.txt')]
            annotated = len(annotated_files)
        
        self.status_label.config(
            text=f"Image {current}/{total}\n{annotated} annotée(s) dans Personnage/"
        )

if __name__ == "__main__":
    root = Tk()
    app = PlayerAnnotator(root)
    root.mainloop()

