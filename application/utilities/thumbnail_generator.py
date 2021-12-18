from application import logger
import os
from PIL import Image


def thumbnail_generator(image_path):

    logger.info(image_path)
    image_name = os.path.basename(image_path)
    dir = os.path.dirname(image_path) + "/"

    if image_name[0:6] != "hover_":

        try:
            im_hover = Image.open(image_path)
            im_hover.thumbnail((512, 512), Image.ANTIALIAS)
            im_hover.save(dir + "hover_" + image_name)

        except Exception as e:
            logger.info(e)
            logger.info(dir + image_name)
            pass

    if image_name[0:6] != "thumb_":

        try:
            im_thumb = Image.open(image_path)
            im_thumb.thumbnail((128, 128), Image.ANTIALIAS)
            im_thumb.save(dir + "thumb_" + image_name)

        except Exception as e:
            logger.info(e)
            logger.info(dir + image_name)
            pass




