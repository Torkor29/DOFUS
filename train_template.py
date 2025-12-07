from ultralytics import YOLO
import os
import json

def train_template_model(template_name, templates_config):
    """
    Entraîne un modèle YOLO pour un template spécifique.
    
    template_name: Nom du template (ex: "Personnage", "Mobs")
    templates_config: Dictionnaire de tous les templates
    """
    # Charger un modèle de base (nano)
    model = YOLO('yolov8n.pt')
    
    # Chercher le fichier YAML
    yaml_path = os.path.join("player_dataset", "data.yaml")
    if not os.path.exists(yaml_path):
        print(f"❌ Erreur : Fichier YAML non trouvé à {yaml_path} !")
        print("Assure-toi d'avoir préparé le dataset avec prepare_template_dataset()")
        return
    
    print(f"🚀 Lancement de l'entraînement '{template_name}' sur {yaml_path}...")
    
    # Nom du projet selon le template
    project_name = f"runs/{template_name.lower()}"
    
    # Lancer l'entraînement
    results = model.train(
        data=yaml_path,
        epochs=50,
        imgsz=640,
        plots=True,
        project=project_name,
        name='train'
    )
    
    print("✅ Entraînement terminé !")
    print(f"📦 Nouveau modèle disponible ici : {results.save_dir}/weights/best.pt")
    print(f"💡 Tu peux maintenant utiliser ce modèle dans combat.py pour détecter les {template_name.lower()} !")

if __name__ == "__main__":
    with open("templates_config.json", "r") as f:
        templates = json.load(f)
    train_template_model("Personnage", templates)





