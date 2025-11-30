import os
import shutil
import random
import yaml

def prepare_dataset(source_dir="dataset/images", base_dir="dataset"):
    # Création de la structure YOLO
    dirs = [
        "train/images", "train/labels",
        "val/images", "val/labels"
    ]
    
    for d in dirs:
        path = os.path.join(base_dir, d)
        if not os.path.exists(path):
            os.makedirs(path)
            
    # Récupération des fichiers images et labels
    files = [f for f in os.listdir(source_dir) if f.endswith('.jpg') or f.endswith('.png')]
    
    # Mélange pour avoir un set aléatoire
    random.shuffle(files)
    
    # Séparation 80% train / 20% val
    split_idx = int(len(files) * 0.8)
    train_files = files[:split_idx]
    val_files = files[split_idx:]
    
    def move_files(file_list, split_name):
        for img_file in file_list:
            # Noms
            base_name = os.path.splitext(img_file)[0]
            txt_file = base_name + ".txt"
            
            src_img = os.path.join(source_dir, img_file)
            src_txt = os.path.join(source_dir, txt_file)
            
            # Vérifier si le fichier txt existe (parfois on a l'image sans annotation)
            if not os.path.exists(src_txt):
                print(f"Attention: Pas d'annotation pour {img_file}, ignoré.")
                continue
                
            # Destination
            dst_img = os.path.join(base_dir, split_name, "images", img_file)
            dst_txt = os.path.join(base_dir, split_name, "labels", txt_file)
            
            shutil.move(src_img, dst_img)
            shutil.move(src_txt, dst_txt)
            
    print(f"Déplacement de {len(train_files)} images vers TRAIN...")
    move_files(train_files, "train")
    
    print(f"Déplacement de {len(val_files)} images vers VAL...")
    move_files(val_files, "val")
    
    # Création du fichier data.yaml
    yaml_content = {
        'path': os.path.abspath(base_dir),
        'train': 'train/images',
        'val': 'val/images',
        'names': {
            0: 'soleil' # On suppose que tu as utilisé une seule classe
        }
    }
    
    with open(os.path.join(base_dir, 'data.yaml'), 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
        
    print("Dataset prêt pour YOLO !")

if __name__ == "__main__":
    prepare_dataset()

