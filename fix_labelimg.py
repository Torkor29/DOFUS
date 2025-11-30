import os
import sys

# Chemin probable de l'installation (basé sur ton erreur précédente)
target_file = r"C:\Users\Julie\AppData\Local\Programs\Python\Python311\Lib\site-packages\labelImg\labelImg.py"

if not os.path.exists(target_file):
    print(f"Erreur: Fichier non trouvé à {target_file}")
    print("Vérifie ton installation.")
    sys.exit(1)

print(f"Réparation de {target_file}...")

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
fixed = False
for line in lines:
    # On cherche la ligne buggée: bar.setValue(bar.value() + bar.singleStep() * units)
    if "bar.setValue(bar.value() + bar.singleStep() * units)" in line:
        # On remplace par la version corrigée avec int()
        new_line = line.replace(
            "bar.setValue(bar.value() + bar.singleStep() * units)",
            "bar.setValue(int(bar.value() + bar.singleStep() * units))"
        )
        new_lines.append(new_line)
        fixed = True
        print("Ligne corrigée !")
    else:
        new_lines.append(line)

if fixed:
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("Succès ! Tu peux relancer labelImg.")
    except PermissionError:
        print("Erreur de permission. Essaie de lancer ce script en Administrateur.")
else:
    print("Aucune ligne à corriger trouvée. Peut-être déjà patché ou version différente ?")

