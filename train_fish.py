from ultralytics import YOLO
import os

def train_fish_model():
    # Charger un modèle de base (nano)
    model = YOLO('yolov8n.pt')  

    # Chemin absolu vers le fichier de config des poissons
    yaml_path = os.path.abspath("fish_data.yaml")

    print(f"Lancement de l'entraînement POISSONS sur {yaml_path}...")
    
    # Lancer l'entraînement
    # project='runs/fish' : On sépare les résultats des poissons des autres
    results = model.train(
        data=yaml_path, 
        epochs=50, 
        imgsz=640,
        plots=True,
        project='runs/fish',
        name='train'
    )

    print("Entraînement terminé !")
    print(f"Nouveau modèle disponible ici : {results.save_dir}/weights/best.pt")

if __name__ == "__main__":
    train_fish_model()


