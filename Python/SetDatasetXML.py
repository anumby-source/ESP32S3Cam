import os
import cv2
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Chemins
image_dir = "../dataset/images"
output_dir = "../dataset/xml"
os.makedirs(output_dir, exist_ok=True)

# Variables globales pour l'édition interactive
ix, iy = -1, -1
drawing = False
current_bbox = [0, 0, 0, 0]
img_copy = None
current_img_name = ""

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

def get_tight_bbox(image_path):
    """Calcule la bounding box la plus serrée (avec vérification)."""
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    rect = (10, 10, w-20, h-20)
    cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    kernel = np.ones((3, 3), np.uint8)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel, iterations=2)
    contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        bbox = [x, y, x + w, y + h]
        if not is_valid_bbox(bbox):
            bbox = fix_bbox(bbox, w, h)
        return bbox
    else:
        return [0, 0, w, h]  # Bbox par défaut (toute l'image)

def draw_rectangle(event, x, y, flags, param):
    """Callback pour dessiner/modifier la bounding box."""
    global ix, iy, drawing, current_bbox, img_copy, current_img_name, img

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        current_bbox[0], current_bbox[1] = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_copy = img.copy()
            cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        current_bbox[2], current_bbox[3] = x, y
        # Corrige la bbox si nécessaire
        current_bbox = fix_bbox(current_bbox, img.shape[1], img.shape[0])
        cv2.rectangle(img_copy, (current_bbox[0], current_bbox[1]), (current_bbox[2], current_bbox[3]), (0, 255, 0), 2)

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

# Parcourir toutes les images
select = ["photo_05_22.jpg", "photo_05_26.jpg"]
for img_name in os.listdir(image_dir):
    if img_name.endswith(".jpg"):
        img_path = os.path.join(image_dir, img_name)
        # print(img_name)
        if not select is None:
            if img_name in select:
                print("select", img_path)
            else:
                continue
        else:
            continue
        img = cv2.imread(img_path)
        h, w, d = img.shape
        class_name = img_name.split("_")[1]

        # Détecter la bounding box initiale
        current_bbox = get_tight_bbox(img_path)
        img_copy = img.copy()
        cv2.rectangle(img_copy, (current_bbox[0], current_bbox[1]), (current_bbox[2], current_bbox[3]), (0, 255, 0), 2)

        # Afficher l'image et permettre l'édition
        cv2.namedWindow(img_name)
        cv2.setMouseCallback(img_name, draw_rectangle)
        print(f"\nImage: {img_name}")
        print(f"BBox initiale: {current_bbox}")
        print("Instructions:")
        print("- Cliquez et glissez pour modifier la BBox.")
        print("- 's' : Sauvegarder le XML.")
        print("- 'r' : Réinitialiser la BBox.")
        print("- 'q' : Quitter.")

        while True:
            cv2.imshow(img_name, img_copy)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                # Sauvegarder le XML
                create_pascal_voc_xml(img_name, w, h, d, class_name, current_bbox)
                break
            elif key == ord('r'):
                # Réinitialiser la BBox
                current_bbox = get_tight_bbox(img_path)
                img_copy = img.copy()
                cv2.rectangle(img_copy, (current_bbox[0], current_bbox[1]), (current_bbox[2], current_bbox[3]), (0, 255, 0), 2)
            elif key == ord('q'):
                # Quitter
                exit()

        cv2.destroyAllWindows()
