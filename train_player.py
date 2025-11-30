from ultralytics import YOLO
import os

def train_player_model():
    # Charger un modèle de base (nano)
    model = YOLO('yolov8n.pt')  

    # Chercher le fichier YAML (dans player_dataset/data.yaml ou à la racine)
    yaml_path = None
    if os.path.exists("player_dataset/data.yaml"):
        yaml_path = os.path.abspath("player_dataset/data.yaml")
    elif os.path.exists("player_data.yaml"):
        yaml_path = os.path.abspath("player_data.yaml")
    
    if not yaml_path or not os.path.exists(yaml_path):
        print(f"❌ Erreur : Fichier YAML non trouvé !")
        print("Assure-toi d'avoir préparé le dataset avec prepare_player_dataset.py")
        return

    print(f"🚀 Lancement de l'entraînement PERSONNAGE sur {yaml_path}...")
    
    # Lancer l'entraînement
    # project='runs/player' : On sépare les résultats du personnage des autres
    results = model.train(
        data=yaml_path, 
        epochs=50, 
        imgsz=640,
        plots=True,
        project='runs/player',
        name='train'
    )

    print("✅ Entraînement terminé !")
    print(f"📦 Nouveau modèle disponible ici : {results.save_dir}/weights/best.pt")
    print(f"💡 Tu peux maintenant utiliser ce modèle dans combat.py pour détecter ton personnage !")

if __name__ == "__main__":
    train_player_model()

