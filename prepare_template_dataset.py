import os
import shutil
import random
import yaml

def prepare_template_dataset(template_name, templates_config, base_dir="player_dataset"):
    """
    Prépare le dataset pour YOLO en séparant les images annotées en train/validation.
    Supporte plusieurs classes (multi-classes).
    
    template_name: Nom du template à préparer (ex: "Personnage", "Mobs")
    templates_config: Dictionnaire de tous les templates avec leurs configs
    """
    if template_name not in templates_config:
        print(f"❌ Template '{template_name}' non trouvé dans la configuration !")
        return
    
    template = templates_config[template_name]
    source_dir = os.path.join(base_dir, "images", template["folder"])
    
    if not os.path.exists(source_dir):
        print(f"❌ Dossier {source_dir} non trouvé !")
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
    
    # Récupération des fichiers images et labels
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
            # Vérifier qu'il y a au moins une annotation de cette classe
            with open(txt_path, 'r') as f:
                class_id_str = str(template["class_id"])
                for line in f:
                    if line.strip().startswith(class_id_str + " "):
                        valid_files.append(img_file)
                        break
    
    if not valid_files:
        print(f"❌ Aucune image annotée trouvée pour '{template_name}' dans {source_dir} !")
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
            
            # Copier (garder les originaux)
            shutil.copy2(src_img, dst_img)
            shutil.copy2(src_txt, dst_txt)
            moved += 1
        return moved
    
    print(f"📦 Copie de {len(train_files)} images vers TRAIN...")
    train_moved = move_files(train_files, "train")
    
    print(f"📦 Copie de {len(val_files)} images vers VALIDATION...")
    val_moved = move_files(val_files, "validation")
    
    # Création du fichier data.yaml avec TOUTES les classes
    abs_path = os.path.abspath(base_dir).replace('\\', '/')
    
    # Construire le dictionnaire des noms de classes
    names = {}
    for name, tpl in templates_config.items():
        names[tpl["class_id"]] = tpl["class_name"]
    
    yaml_content = {
        'path': abs_path,
        'train': 'train/images',
        'val': 'validation/images',
        'names': names
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
    print(f"   🏷️  Classes configurées : {len(names)} ({', '.join(names.values())})")
    print(f"\n💡 Tu peux maintenant lancer l'entraînement depuis l'interface !")

if __name__ == "__main__":
    import json
    with open("templates_config.json", "r") as f:
        templates = json.load(f)
    prepare_template_dataset("Personnage", templates)





