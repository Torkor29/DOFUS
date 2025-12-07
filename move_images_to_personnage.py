import os
import shutil

def move_images_to_personnage():
    """
    Déplace les images collectées de player_dataset/images/ vers player_dataset/images/Personnage/
    """
    source_dir = "player_dataset/images"
    dest_dir = "player_dataset/images/Personnage"
    
    if not os.path.exists(source_dir):
        print(f"❌ Dossier source non trouvé : {source_dir}")
        return
    
    # Créer le dossier Personnage s'il n'existe pas
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"📁 Dossier créé : {dest_dir}")
    
    # Chercher toutes les images (pas les .txt)
    extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    image_files = []
    
    for file in os.listdir(source_dir):
        if any(file.lower().endswith(ext) for ext in extensions):
            # Exclure les images _annotated
            if '_annotated' not in file:
                image_files.append(file)
    
    if not image_files:
        print(f"ℹ️  Aucune image trouvée dans {source_dir}")
        return
    
    print(f"📦 Déplacement de {len(image_files)} image(s) vers {dest_dir}...")
    
    moved = 0
    for img_file in image_files:
        src_path = os.path.join(source_dir, img_file)
        dst_path = os.path.join(dest_dir, img_file)
        
        # Vérifier si l'image existe déjà dans Personnage
        if os.path.exists(dst_path):
            print(f"⚠️  {img_file} existe déjà dans Personnage/, ignoré")
            continue
        
        try:
            shutil.move(src_path, dst_path)
            moved += 1
            print(f"✅ {img_file}")
        except Exception as e:
            print(f"❌ Erreur lors du déplacement de {img_file} : {e}")
    
    print(f"\n✅ {moved} image(s) déplacée(s) avec succès !")
    print(f"💡 Les images sont maintenant dans {dest_dir}")
    print(f"💡 Tu peux maintenant ouvrir l'annotateur pour les annoter.")

if __name__ == "__main__":
    move_images_to_personnage()






