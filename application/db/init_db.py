from application import flora_db


def init_flora_db():
    flora_db.create_all(bind='flora_db')


