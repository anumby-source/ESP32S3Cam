import cv2
import os
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Variables globales
contours_trouves = []
image_globale = None
index_selectionne = -1
mode_dessin = False
point_depart = None
bb_manuelle = None
liste_images = []
index_image_courante = 0
choix_valides = {}  # {chemin_image: {"label": str, "bb": tuple}}
dossier_annotations = "annotations"

# Chemins
image_dir = "../dataset/images"
output_dir = "../dataset/xml"
os.makedirs(output_dir, exist_ok=True)

# Créer le dossier pour les annotations XML
os.makedirs(dossier_annotations, exist_ok=True)

def detecter_contours(image_path):
    global contours_trouves, image_globale, index_selectionne, bb_manuelle
    image = cv2.imread(image_path)
    # print("detecter_contours> image_path")
    if image is None:
        print(f"Erreur : impossible de charger {image_path}")
        return None

    gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    flou = cv2.GaussianBlur(gris, (7, 7), 0)
    edges = cv2.Canny(flou, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    contours_trouves = contours
    image_globale = image.copy()
    bb_manuelle = None

    # Dessiner toutes les BB en bleu
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(image_globale, (x, y), (x + w, y + h), (255, 0, 0), 2)

    return image_globale

def is_valid_bbox(bbox, min_size=10):
    """Vérifie si la bbox est valide (taille > min_size, coordonnées cohérentes)."""
    x1, y1, x2, y2 = bbox
    return (x2 > x1) and (y2 > y1) and ((x2 - x1) >= min_size) and ((y2 - y1) >= min_size)

def fix_bbox(bbox, img_width, img_height):
    """Corrige une bbox invalide (ex: y2 < y1)."""
    x1, y1, x2, y2 = bbox
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])
    # Assure une taille minimale de 10x10
    x2 = max(x1 + 10, x2)
    y2 = max(y1 + 10, y2)
    # Limite aux dimensions de l'image
    x2 = min(x2, img_width)
    y2 = min(y2, img_height)
    return [x1, y1, x2, y2]

def create_pascal_voc_xml(img_name, img_width, img_height, img_depth, class_name, bbox):
    """Génère un fichier XML Pascal VOC valide."""
    # Vérifie et corrige la bbox
    if not is_valid_bbox(bbox):
        print(f"[WARNING] BBox invalide pour {img_name}. Correction automatique...")
        bbox = fix_bbox(bbox, img_width, img_height)

    root = ET.Element("xml")

    # Folder
    folder = ET.SubElement(root, "folder")
    folder.text = "images"

    # Filename
    filename = ET.SubElement(root, "filename")
    filename.text = img_name

    # Path
    path = ET.SubElement(root, "path")
    path.text = os.path.join("dataset", img_name).replace("\\", "/")

    # Source
    source = ET.SubElement(root, "source")
    database = ET.SubElement(source, "database")
    database.text = "Unknown"

    # Size
    size = ET.SubElement(root, "size")
    width = ET.SubElement(size, "width")
    width.text = str(img_width)
    height = ET.SubElement(size, "height")
    height.text = str(img_height)
    depth = ET.SubElement(size, "depth")
    depth.text = str(img_depth)

    # Segmented
    segmented = ET.SubElement(root, "segmented")
    segmented.text = "0"

    # Object
    obj = ET.SubElement(root, "object")
    name = ET.SubElement(obj, "name")
    name.text = class_name
    pose = ET.SubElement(obj, "pose")
    pose.text = "Unspecified"
    truncated = ET.SubElement(obj, "truncated")
    truncated.text = "0"
    difficult = ET.SubElement(obj, "difficult")
    difficult.text = "0"

    # Bndbox
    bndbox = ET.SubElement(obj, "bndbox")
    xmin = ET.SubElement(bndbox, "xmin")
    xmin.text = str(bbox[0])
    ymin = ET.SubElement(bndbox, "ymin")
    ymin.text = str(bbox[1])
    xmax = ET.SubElement(bndbox, "xmax")
    xmax.text = str(bbox[2])
    ymax = ET.SubElement(bndbox, "ymax")
    ymax.text = str(bbox[3])

    # Écriture du fichier XML
    xml_str = ET.tostring(root)
    xml_pretty = minidom.parseString(xml_str).toprettyxml(indent="   ")
    xml_file = os.path.join(output_dir, img_name.replace(".jpg", ".xml"))
    with open(xml_file, "w") as f:
        f.write(xml_pretty)
    print(f"Fichier XML sauvegardé : {xml_file}")

def lire_xml_et_ajouter_choix(image_path):
    """Lit le fichier XML et ajoute les BB à `choix_valides`."""
    global contours_trouves, image_globale, index_selectionne, bb_manuelle

    if image_globale is None:
        image = cv2.imread(image_path)
        image_globale = image.copy()

    xml_path = os.path.join(output_dir, os.path.basename(image_path).replace(".jpg", ".xml").replace(".png", ".xml"))
    if not os.path.exists(xml_path):
        print("NOT xml path ", xml_path)
        return False

    print("xml path", xml_path)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    for obj in root.findall("object"):
        bndbox = obj.find("bndbox")
        xmin = int(bndbox.find("xmin").text)
        ymin = int(bndbox.find("ymin").text)
        xmax = int(bndbox.find("xmax").text)
        ymax = int(bndbox.find("ymax").text)
        label = "manual"
        bb_manuelle = xmin, ymin, xmax, ymax

        choix_valides[image_path] = {"label": label, "bb": bb_manuelle}
        print("lire_xml_et_ajouter_choix> ", image_path, label, bb_manuelle)
        afficher_image_avec_selection()
        return True
    return False

def gestion_souris(event, x, y, flags, param):
    global index_selectionne, mode_dessin, point_depart, bb_manuelle, image_globale


    if mode_dessin:
        if event == cv2.EVENT_LBUTTONDOWN:
            point_depart = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and point_depart:
            img_temp = image_globale.copy()
            for contour in contours_trouves:
                x_c, y_c, w_c, h_c = cv2.boundingRect(contour)
                cv2.rectangle(img_temp, (x_c, y_c), (x_c + w_c, y_c + h_c), (255, 0, 0), 2)
            cv2.rectangle(img_temp, point_depart, (x, y), (0, 255, 0), 2)
            cv2.imshow("BB - Flèches: naviguer, Espace: valider, d: dessiner", img_temp)
        elif event == cv2.EVENT_LBUTTONUP and point_depart:
            bb_manuelle = (*point_depart, x, y)
            afficher_image_avec_selection()
            point_depart = None
            # print("gestion_souris", index_selectionne, mode_dessin, point_depart, bb_manuelle)
            mode_dessin = False
            valider_et_passer_a_suivante()
    else:
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, contour in enumerate(contours_trouves):
                x_c, y_c, w_c, h_c = cv2.boundingRect(contour)
                if x_c <= x <= x_c + w_c and y_c <= y <= y_c + h_c:
                    index_selectionne = i
                    afficher_image_avec_selection()
                    break
            valider_et_passer_a_suivante()


def afficher_image_avec_selection():
    global image_globale, contours_trouves, index_selectionne, bb_manuelle, choix_valides, liste_images, index_image_courante

    image_temp = image_globale.copy()
    chemin_image = liste_images[index_image_courante]

    img_path, img_name = os.path.split(chemin_image)
    cv2.putText(image_temp, img_name, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # print("afficher_image_avec_selection", bb_manuelle, choix_valides[chemin_image])

    # Si l'image a un choix validé, l'afficher en rouge
    if chemin_image in choix_valides:
        choix = choix_valides[chemin_image]
        bb = choix["bb"]
        if choix["label"] == "manual":
            # print("afficher_image_avec_selection 1")
            x1, y1, x2, y2 = bb
            cv2.rectangle(image_temp, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Rouge pour BB validée
            # cv2.putText(image_temp, "Manuel", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # print("afficher_image_avec_selection 2")
            for i, contour in enumerate(contours_trouves):
                x, y, w, h = cv2.boundingRect(contour)
                if (x, y, x + w, y + h) == bb:
                    cv2.rectangle(image_temp, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Rouge
                    peri = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.03 * peri, True)
                    """
                    if len(approx) == 8:
                        cv2.putText(image_temp, "STOP", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    elif len(approx) == 3:
                        cv2.putText(image_temp, "Triangle", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    elif len(approx) == 4:
                        cv2.putText(image_temp, "Carre", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    else:
                        cv2.putText(image_temp, "Cercle", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    """
                    break
    else:
        # Afficher les BB non validées en bleu
        # print("afficher_image_avec_selection 3")
        for i, contour in enumerate(contours_trouves):
            x, y, w, h = cv2.boundingRect(contour)
            color = (0, 0, 255) if i == index_selectionne else (255, 0, 0)
            cv2.rectangle(image_temp, (x, y), (x + w, y + h), color, 2)

            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.03 * peri, True)
            """
            if len(approx) == 8:
                cv2.putText(image_temp, "STOP", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            elif len(approx) == 3:
                cv2.putText(image_temp, "Triangle", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            elif len(approx) == 4:
                aspect_ratio = float(w)/h
                if 0.95 <= aspect_ratio <= 1.05:
                    cv2.putText(image_temp, "Carre", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                else:
                    cv2.putText(image_temp, "Rectangle", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            else:
                cv2.putText(image_temp, "Cercle", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            """

    # Afficher la BB manuelle (si elle existe)
    if bb_manuelle:
        # print("afficher_image_avec_selection 4", bb_manuelle)
        x1, y1, x2, y2 = bb_manuelle
        cv2.rectangle(image_temp, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # cv2.putText(image_temp, "Manuel", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("BB - Flèches: naviguer, Espace: valider, d: dessiner", image_temp)

def obtenir_label_et_bb():
    global index_selectionne, bb_manuelle, contours_trouves

    # print("obtenir_label_et_bb>")

    if index_selectionne != -1:
        contour = contours_trouves[index_selectionne]
        x, y, w, h = cv2.boundingRect(contour)
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.03 * peri, True)
        if len(approx) == 8:
            return "stop_sign", (x, y, x + w, y + h)
        elif len(approx) == 3:
            return "triangle", (x, y, x + w, y + h)
        elif len(approx) == 4:
            return "square", (x, y, x + w, y + h)
        else:
            return "circle", (x, y, x + w, y + h)
    elif bb_manuelle:
        return "manual", bb_manuelle
    return None, None

def valider_et_passer_a_suivante():
    global choix_valides, index_image_courante, liste_images


    chemin_image = liste_images[index_image_courante]
    # print("valider_et_passer_a_suivante>", chemin_image)
    label, bb = obtenir_label_et_bb()
    if label and bb:
        choix_valides[chemin_image] = {"label": label, "bb": bb}
        # sauvegarder_annotation(chemin_image, bb, label)
        img_path, img_name = os.path.split(chemin_image)
        img = cv2.imread(chemin_image)
        img_height, img_width, img_depth = img.shape
        class_name = img_name.split("_")[1]

        create_pascal_voc_xml(img_name, img_width, img_height, img_depth, class_name, bb)

    if index_image_courante < len(liste_images) - 1:
        index_image_courante += 1
        traiter_image(liste_images[index_image_courante])
    else:
        print("Dernière image atteinte.")

def traiter_image(image_path):
    global image_globale, contours_trouves, index_selectionne, bb_manuelle, choix_valides

    # print("traiter_image> Image courante:", image_path)

    # Vérifier si un fichier XML existe déjà pour cette image
    if image_path not in choix_valides:
        lire_xml_et_ajouter_choix(image_path)
        afficher_image_avec_selection()

    if image_path in choix_valides:
        # Charger les choix validés
        choix = choix_valides[image_path]
        if choix["label"] == "manual":
            bb_manuelle = choix["bb"]
        else:
            for i, contour in enumerate(contours_trouves):
                x, y, w, h = cv2.boundingRect(contour)
                if (x, y, x + w, y + h) == choix["bb"]:
                    index_selectionne = i
                    break
        detecter_contours(image_path)
    else:
        contours_trouves = []
        index_selectionne = -1
        bb_manuelle = None
        detecter_contours(image_path)

    afficher_image_avec_selection()
    cv2.setMouseCallback("BB - Flèches: naviguer, Espace: valider, d: dessiner", gestion_souris)

def naviguer_entre_images():
    global index_image_courante, mode_dessin
    while True:
        key = cv2.waitKey(0)
        if key == 98:  # "b"
            if index_image_courante > 0:
                index_image_courante -= 1
                traiter_image(liste_images[index_image_courante])
        elif key == 110:  # "n"
            if index_image_courante < len(liste_images) - 1:
                index_image_courante += 1
                traiter_image(liste_images[index_image_courante])
        elif key == 32:  # Espace : valider et passer à la suivante
            valider_et_passer_a_suivante()
        elif key == ord('v'):  # Activer/désactiver le mode dessin
            mode_dessin = not mode_dessin
            # print("Mode dessin activé" if mode_dessin else "Mode dessin désactivé")
        elif key == 27:  # Échap : quitter
            break
    cv2.destroyAllWindows()

# Exemple d'utilisation
liste_images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if liste_images:
    index_image_courante = 0
    traiter_image(liste_images[index_image_courante])
    naviguer_entre_images()
else:
    print(f"Aucune image trouvée dans le dossier '{image_dir}'.")
