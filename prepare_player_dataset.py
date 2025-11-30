import os
import shutil
import random
import yaml

def prepare_player_dataset(source_dir="player_dataset/images/Personnage", base_dir="player_dataset"):
    """
    Prépare le dataset pour YOLO en séparant les images annotées en train/validation.
    Les images doivent être dans le dossier Personnage avec leurs annotations.
    """
    # Vérifier que le dossier Personnage existe
    if not os.path.exists(source_dir):
        print(f"❌ Dossier {source_dir} non trouvé !")
        print("💡 Assure-toi d'avoir annoté des images. Elles doivent être dans player_dataset/images/Personnage/")
        return
    
    # Création de la structure YOLO
    dirs = [
        "train/images", "train/labels",
        "validation/images", "validation/labels"
    ]
    
    for d in dirs:
        path = os.path.join(base_dir, d)
        if not os.path.exists(path):
            os.makedirs(path)
    
    # Récupération des fichiers images et labels depuis le dossier Personnage
    files = []
    extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    for f in os.listdir(source_dir):
        if any(f.lower().endswith(ext) for ext in extensions):
            files.append(f)
    
    # Filtrer uniquement les images qui ont un fichier .txt correspondant
    valid_files = []
    for img_file in files:
        base_name = os.path.splitext(img_file)[0]
        txt_file = base_name + ".txt"
        txt_path = os.path.join(source_dir, txt_file)
        if os.path.exists(txt_path):
            valid_files.append(img_file)
        else:
            print(f"⚠️  Pas d'annotation pour {img_file}, ignoré.")
    
    if not valid_files:
        print("❌ Aucune image annotée trouvée dans le dossier Personnage !")
        print("💡 Assure-toi d'avoir annoté des images avec l'outil d'annotation.")
        return
    
    # Mélange pour avoir un set aléatoire
    random.shuffle(valid_files)
    
    # Séparation 80% train / 20% validation
    split_idx = int(len(valid_files) * 0.8)
    train_files = valid_files[:split_idx]
    val_files = valid_files[split_idx:]
    
    def move_files(file_list, split_name):
        moved = 0
        for img_file in file_list:
            base_name = os.path.splitext(img_file)[0]
            txt_file = base_name + ".txt"
            
            src_img = os.path.join(source_dir, img_file)
            src_txt = os.path.join(source_dir, txt_file)
            
            # Destination
            dst_img = os.path.join(base_dir, split_name, "images", img_file)
            dst_txt = os.path.join(base_dir, split_name, "labels", txt_file)
            
            # Copier au lieu de déplacer (pour garder les originaux dans Personnage)
            shutil.copy2(src_img, dst_img)
            shutil.copy2(src_txt, dst_txt)
            moved += 1
        return moved
    
    print(f"📦 Copie de {len(train_files)} images vers TRAIN...")
    train_moved = move_files(train_files, "train")
    
    print(f"📦 Copie de {len(val_files)} images vers VALIDATION...")
    val_moved = move_files(val_files, "validation")
    
    # Création du fichier data.yaml
    # Convertir le chemin Windows en format YOLO (forward slashes)
    abs_path = os.path.abspath(base_dir).replace('\\', '/')
    yaml_content = {
        'path': abs_path,
        'train': 'train/images',
        'val': 'validation/images',
        'names': {
            0: 'personnage'
        }
    }
    
    yaml_path = os.path.join(base_dir, 'data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
    
    print(f"\n✅ Dataset prêt pour YOLO !")
    print(f"   📁 Structure créée :")
    print(f"      - {train_moved} images d'entraînement → {base_dir}/train/images/")
    print(f"      - {val_moved} images de validation → {base_dir}/validation/images/")
    print(f"      - Labels correspondants → train/labels/ et validation/labels/")
    print(f"\n   📦 Fichiers originaux conservés dans : {source_dir}")
    print(f"   ⚙️  Configuration YOLO : {yaml_path}")
    print(f"\n💡 Tu peux maintenant lancer l'entraînement depuis l'interface !")
    print(f"   (Le modèle utilisera automatiquement {yaml_path})")

if __name__ == "__main__":
    prepare_player_dataset()

