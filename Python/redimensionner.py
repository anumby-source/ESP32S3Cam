import cv2
import os

# Dossier contenant vos images originales
dossier_entree = "../panneaux/"
# Dossier de sortie pour les images redimensionnées
dossier_sortie = "../panneaux_petits/"
# Taille souhaitée (largeur, hauteur)
taille = (50, 50)

# Crée le dossier de sortie s'il n'existe pas
os.makedirs(dossier_sortie, exist_ok=True)

# Parcourt toutes les images du dossier d'entrée
for nom_fichier in os.listdir(dossier_entree):
    if nom_fichier.endswith(".png"):
        # Chemin complet de l'image d'entrée
        chemin_entree = os.path.join(dossier_entree, nom_fichier)
        # Chemin complet de l'image de sortie
        chemin_sortie = os.path.join(dossier_sortie, nom_fichier)

        print("in", chemin_entree, "out", chemin_sortie)

        # Charge l'image
        image = cv2.imread(chemin_entree, cv2.IMREAD_UNCHANGED)

        # Redimensionne l'image
        image_redimensionnee = cv2.resize(image, taille, interpolation=cv2.INTER_AREA)

        # Enregistre l'image redimensionnée
        cv2.imwrite(chemin_sortie, image_redimensionnee)

print("Redimensionnement terminé ! Les images sont dans le dossier 'panneaux_redimensionnes'.")

