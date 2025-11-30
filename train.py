from ultralytics import YOLO
import os

def train_model():
    # Charger un modèle pré-entraîné (nano version, très rapide)
    model = YOLO('yolov8n.pt')  

    # Chemin absolu vers le fichier data.yaml
    yaml_path = os.path.abspath("dataset/data.yaml")

    print(f"Lancement de l'entraînement sur {yaml_path}...")
    
    # Lancer l'entraînement
    # epochs=50 : Il va passer 50 fois sur tes images
    # imgsz=640 : Taille standard pour YOLO
    results = model.train(
        data=yaml_path, 
        epochs=50, 
        imgsz=640,
        plots=True
    )

    print("Entraînement terminé !")
    print(f"Modèle sauvegardé dans : {results.save_dir}")

if __name__ == "__main__":
    train_model()

