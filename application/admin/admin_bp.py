from flask import Blueprint, url_for
from flask import request, Response, abort, jsonify, send_from_directory, current_app as app
from flask_security import roles_required, current_user
from application import flora_db, logger
import flaskfilemanager.filemanager as fm
from application.db.miflora import PageTextFamily, PageTextGenus, PageTextSpecies, HomePagesText, Images, ImagesDev
from sqlalchemy.exc import SQLAlchemyError
import datetime
import os
from ..utilities import thumbnail_generator

admin_bp = Blueprint('admin', __name__)
db = flora_db


@admin_bp.route('/edit-family/<string:family_id>', methods=['GET', 'PUT'])
@roles_required('admin')
def edit_family_text(family_id):
    if request.method == 'GET':
        return send_from_directory(app.template_folder, "index.html")

    if request.method == 'PUT':
        logger.info('Editor: ' + current_user.email)
        try:
            logger.info(request.json)
            db.session.query(PageTextFamily) \
                .filter(PageTextFamily.family_id == family_id) \
                .update({'text': request.json})
            db.session.commit()
            return jsonify(success=True)
        except SQLAlchemyError as e:
            logger.info(e)
            error = {"error": "Database error"}
            return jsonify(error)


@admin_bp.route('/edit-genus/<string:genus_id>', methods=['GET', 'PUT'])
@roles_required('admin')
def edit_genus_text(genus_id):

    if request.method == 'GET':
        return send_from_directory(app.template_folder, "index.html")

    if request.method == 'PUT':
        logger.info('Editor: ' + current_user.email)
        try:
            logger.info(request.json)
            db.session.query(PageTextGenus) \
                .filter(PageTextGenus.genus_id == genus_id) \
                .update({'text': request.json})
            db.session.commit()
            return jsonify(success=True)
        except SQLAlchemyError as e:
            logger.info(e)
            error = {"error": "Database error"}
            return jsonify(error)


@admin_bp.route("/edit-species/<string:species_id>", methods=['GET', 'PUT'])
@roles_required('admin')
def edit_species_text(species_id):

    if request.method == 'GET':
        return send_from_directory(app.template_folder, "index.html")

    if request.method == 'PUT':
        logger.info('Editor: ' + current_user.email)
        try:
            logger.info(request.json)
            db.session.query(PageTextSpecies) \
                .filter(PageTextSpecies.species_id == species_id) \
                .update({'text': request.json})
            db.session.commit()
            return jsonify(success=True)
        except SQLAlchemyError as e:
            logger.info(e)
            error = {'error': 'Database error'}
            return jsonify(error)


@admin_bp.route("/edit-home/<string:home_id>", methods=['GET', 'PUT'])
@roles_required('admin')
def edit_home_text(home_id):

    if request.method == 'GET':
        logger.info('authorized')
        return send_from_directory(app.template_folder, "index.html")

    if request.method == 'PUT':
        logger.info('Editor: ' + current_user.email)
        try:
            logger.info(request.json)
            db.session.query(HomePagesText) \
                .filter(HomePagesText.page_id == home_id) \
                .update({'text': request.json})
            db.session.commit()
            return jsonify(success=True)
        except SQLAlchemyError as e:
            logger.info(e)
            error = {"error": "Database error"}
            return jsonify(error)


# FYI - for paths to image files via flaskfilefilemanager,
# the forward slashes in the path must be escaped via URL encoding '%2F'
# E.g. - http://localhost:5000/admin/fm/species-images/88?path=_pid_88%2F8330.jpg

@admin_bp.route('/fm/species-images/<string:species_id>', methods=['GET', 'PUT'])
@roles_required('admin')
def edit_species_images(species_id):
    if request.method == 'GET':
        return send_from_directory(app.template_folder, "index.html")


@admin_bp.route('/fm/species-images/upload/<string:species_id>', methods=['GET', 'POST'])
@roles_required('admin')
def upload_image(species_id):

    file = request.files['files']
    species_images_dir = os.path.join(app.config.get('FLASKFILEMANAGER_FILE_PATH'), os.path.join('_pid_') + species_id)

    if request.method == 'POST':
        logger.info('Editor: ' + current_user.email)
        plant_id = int(species_id)
        jpg_name = str(request.files['files'].filename)
        caption = str(request.form.get('caption', None))
        photographer = str(request.form.get('photographer', None))
        priority = int(request.form.get('priority', None) == 'true')
        date_updated = datetime.datetime.today()
        image_obj = Images(plant_id=plant_id,
                           jpg_name=jpg_name,
                           caption=caption,
                           photographer=photographer,
                           priority=priority,
                           date_updated=date_updated)

        if priority == 1:
            # demote old priority image
            try:
                db.session.query(Images) \
                    .filter(Images.plant_id == species_id) \
                    .filter(Images.priority == 1) \
                    .update({'priority': 0})
                db.session.flush()
            except SQLAlchemyError as e:
                logger.info(e)
                error = {'error': 'Database error'}
                return jsonify(error)

        try:
            db.session.add(image_obj)
            db.session.flush()
        except SQLAlchemyError as e:
            logger.info(e)
            error = {'error': 'Database error'}
            return jsonify(error)

        try:
            file.filename = str(image_obj.image_id) + '.jpg'
            fm.upload_file()
        except Exception as e:
            logger.info(e)
            error = {'error': 'File manager error'}
            return jsonify(error)

        try:
            thumbnail_generator.thumbnail_generator(os.path.join(species_images_dir + "/" + file.filename))
        except Exception as e:
            logger.info(e)
            error = {'error': 'File manager error'}
            return jsonify(error)

        try:
            db.session.commit()
            return jsonify(success=True)
        except SQLAlchemyError as e:
            logger.info(e)
            error = {'error': 'Database error'}
            return jsonify(error)

    return send_from_directory(app.template_folder, "index.html")


@admin_bp.route('/fm/species-images/edit-image/<string:species_id>', methods=['PUT'])
@roles_required('admin')
def edit_image(species_id):
    if request.method == 'PUT':
        logger.info('Editor: ' + current_user.email)
        plant_id = int(species_id)
        image_id = int(request.form.get('image_id'))
        caption = str(request.form.get('caption', None))
        photographer = str(request.form.get('photographer', None))
        priority = int(request.form.get('priority', None) == 'true')
        date_updated = datetime.datetime.today()

        if priority == 1:
            # demote old priority image
            set_as_priority_image(species_id, image_id)

        try:
            db.session.query(Images) \
                .filter(Images.image_id == image_id) \
                .update({'caption': caption, 'photographer': photographer, 'priority': priority})
            return jsonify(success=True)

        except SQLAlchemyError as e:
            logger.info(e)
            error = {'error': 'Database error'}
            return jsonify(error)


@admin_bp.route('/fm/species-images/set-priority/<string:species_id>', methods=['PUT'])
@roles_required('admin')
def set_priority(species_id):
    if request.method == 'PUT':
        logger.info('Editor: ' + current_user.email)
        new_priority_id = int(request.form.get('image_id'))
        logger.info(new_priority_id)

        return set_as_priority_image(species_id, new_priority_id)


def set_as_priority_image(species_id, new_priority_id):
    current_priority_obj = db.session.query(Images) \
        .filter(Images.plant_id == species_id) \
        .filter(Images.priority == 1)

    new_priority_obj = db.session.query(Images) \
        .filter(Images.plant_id == species_id) \
        .filter(Images.image_id == new_priority_id)

    logger.info(current_priority_obj)
    logger.info(new_priority_obj)

    if new_priority_obj != current_priority_obj:
        # demote
        try:
            current_priority_obj.update({'priority': 0})
            new_priority_obj.update({'priority': 1})
            db.session.commit()
            return jsonify(success=True)
        except SQLAlchemyError as e:
            logger.info(e)
            error = {'error': 'Database error'}
            return jsonify(error)


@admin_bp.route('/fm/species-images/delete-image/<string:species_id>', methods=['DELETE'])
@roles_required('admin')
def delete_image(species_id):
    if request.method == 'DELETE':
        logger.info('Editor: ' + current_user.email)
        image_id = request.get_json()['image_id']
        species_images_dir = os.path.join(app.config.get('FLASKFILEMANAGER_FILE_PATH'),
                                          os.path.join('_pid_') + species_id) + '/'

        try:
            file_path = species_images_dir + str(image_id) + '.jpg'
            delete_file(file_path)

            file_hover_path = species_images_dir + 'hover_' + str(image_id) + '.jpg'
            delete_file(file_hover_path)

            file_thumb_path = species_images_dir + 'thumb_' + str(image_id) + '.jpg'
            delete_file(file_thumb_path)

        except Exception as e:
            logger.info(e)
            error = {'error': 'File manager error'}
            return jsonify(error)

        try:
            logger.info(request.json)
            db.session.query(Images) \
                .filter(Images.image_id == image_id) \
                .delete()
            db.session.commit()
            return jsonify(success=True)

        except SQLAlchemyError as e:
            logger.info(e)
            error = {"error": "Database error"}
            return jsonify(error)


def delete_file(path):
    if not os.path.exists(path):
        error = {'error': 'File %s doesn\'t exist' % path}
        return jsonify(error)

    try:
        logger.info('Deleting file: {}'.format(path))
        os.remove(path)
        return jsonify(success=True)
    except Exception as e:
        error = {'error': 'Operation failed: %s' % e}
        return jsonify(error)

'''

def better_listdir(dirpath):
        """
        Generator yielding (filename, filepath) tuples for every
        file in the given directory path.
        """
        # First clean up dirpath to absolutize relative paths and
        # symbolic path names (e.g. `.`, `..`, and `~`)
        dirpath = os.path.abspath(os.path.expanduser(dirpath))

        # List out (filename, filepath) tuples
        for filename in os.listdir(dirpath):
            yield filename, os.path.join(dirpath, filename)

'''