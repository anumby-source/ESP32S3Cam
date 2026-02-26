import cv2
import os
import glob
import xml.etree.ElementTree as ET
import numpy as np

# === CONFIGURATION ===
BASE_DIR = "dataset"
IMAGE_DIR = os.path.join(BASE_DIR, "images")
XML_DIR = os.path.join(BASE_DIR, "xml")
MIN_AREA_RATIO = 0.005  # plus fin que version précédente

os.makedirs(XML_DIR, exist_ok=True)

# ======================

def create_voc_xml(filename, width, height, class_name, xmin, ymin, xmax, ymax):
    annotation = ET.Element("annotation")

    ET.SubElement(annotation, "folder").text = "images"
    ET.SubElement(annotation, "filename").text = filename

    size = ET.SubElement(annotation, "size")
    ET.SubElement(size, "width").text = str(width)
    ET.SubElement(size, "height").text = str(height)
    ET.SubElement(size, "depth").text = "3"

    ET.SubElement(annotation, "segmented").text = "0"

    obj = ET.SubElement(annotation, "object")
    ET.SubElement(obj, "name").text = class_name

    bndbox = ET.SubElement(obj, "bndbox")
    ET.SubElement(bndbox, "xmin").text = str(xmin)
    ET.SubElement(bndbox, "ymin").text = str(ymin)
    ET.SubElement(bndbox, "xmax").text = str(xmax)
    ET.SubElement(bndbox, "ymax").text = str(ymax)

    return ET.ElementTree(annotation)


image_paths = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.jpg")))

for image_path in image_paths:

    filename = os.path.basename(image_path)

    try:
        class_name = filename.split("_")[1]
    except:
        print(f"Nom invalide : {filename}")
        continue

    img = cv2.imread(image_path)
    if img is None:
        continue

    display_img = img.copy()
    height, width = img.shape[:2]
    image_area = width * height

    # === SEGMENTATION FINE ===
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur léger
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Otsu automatique
    _, mask = cv2.threshold(
        blurred, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Inverser si objet sombre :
    # _, mask = cv2.threshold(
    #     blurred, 0, 255,
    #     cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    # )

    # Morphological opening (enlève bruit)
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small)

    # Morphological closing (remplit petits trous)
    kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_large)

    # === SUPPRESSION PETITS BLOBS ===
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    valid_contours = [
        c for c in contours
        if cv2.contourArea(c) > MIN_AREA_RATIO * image_area
    ]

    if not valid_contours:
        print(f"Aucun objet valide : {filename}")
        continue

    # Créer masque propre
    clean_mask = np.zeros_like(mask)
    largest_contour = max(valid_contours, key=cv2.contourArea)
    cv2.drawContours(clean_mask, [largest_contour], -1, 255, -1)

    # === BOUNDING BOX ULTRA SERRÉE ===
    ys, xs = np.where(clean_mask == 255)
    xmin = np.min(xs)
    xmax = np.max(xs)
    ymin = np.min(ys)
    ymax = np.max(ys)

    # === AFFICHAGE ===
    cv2.rectangle(display_img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
    cv2.putText(display_img, class_name,
                (xmin, max(20, ymin - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0), 2)

    """
    cv2.imshow("Preview - s:save n:next q:quit", display_img)

    print(f"\nImage : {filename}")
    print("s = sauvegarder | n = passer | q = quitter")

    key = cv2.waitKey(0) & 0xFF
    """
    key = ord('s')
    if key == ord('s'):
        xml_tree = create_voc_xml(
            filename, width, height,
            class_name,
            xmin, ymin, xmax, ymax
        )

        xml_path = os.path.join(
            XML_DIR,
            filename.replace(".jpg", ".xml")
        )

        xml_tree.write(xml_path)
        print(f"✔ XML sauvegardé : {xml_path}")
    """

    elif key == ord('q'):
        break

    cv2.destroyAllWindows()
    """

cv2.destroyAllWindows()
print("Terminé.")
