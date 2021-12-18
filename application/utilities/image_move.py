"""

import os
import shutil
from application import logger, APP_ROOT

def move_images(path, images):
    images_root = os.path.join(os.path.dirname(APP_ROOT), 'static', 'species_images')

    try:
        logger.info(path)
        # images = db.session.query(ImagesDev).all()
        for row in images:
            # filename = str(row.image_id) + '.jpg'
            jpg_path = os.path.join(images_root, str(row.image_id) + '.jpg')
            if os.path.isfile(jpg_path):
                dest_folder = '_pid_' + str(row.plant_id)
                new_path = os.path.join(images_root, dest_folder)
                shutil.copy2(jpg_path, new_path)

            # logger.info(os.path.isfile(jpg_path))
            # dest = os.path.join(images_root, '_pid_' + str(row.plant_id) + '/' + str(row.image_id))
            # logger.info(jpg_path)
            # logger.info(image_files)

            # shutil.copy2(jpg_path, dest)
            # os.mkdir(os.path.join(images_root, '_pid_' + str(row.plant_id)))
"""
