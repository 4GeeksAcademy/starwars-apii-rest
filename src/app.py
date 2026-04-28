"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Posts, Profile, Favorite
from sqlalchemy import select
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

# CREATING USER FOR DEVELOPMENT

@app.route('/seed', methods=['GET'])
def seed():
    user = User(
        email="test@test.com",
        password="test",
        is_active=True
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "Seed creado"})

# GET PPL ------------

@app.route("/people", methods=["GET"])
def get_people():
    people = db.session.execute(select(People)).scalars().all()
    transform = [person.serialize() for person in people]
    return jsonify({"sucess": True, "data": transform}), 200

# GET PLANETS ------------

@app.route("/planets", methods=["GET"])
def get_planets():
    planets = db.session.execute(select(Planet)).scalars().all()
    transform = [planet.serialize() for planet in planets]
    return jsonify({"sucess": True, "data": transform}), 200

# ADD PPL ------------

@app.route("/people", methods=["POST"])
def add_people():
    body = request.get_json()
    if not body['name'] or not body["hair_color"] or not body['birth_year'] or not body['eye_color'] or not body['gender'] or not body['height'] or not body['height'] or not body['mass']:
        return jsonify({'sucess': False, 'msg': 'missing data'}), 403

    new_person = People(
        name=body['name'],
        birth_year=body['birth_year'],
        eye_color=body['eye_color'],
        gender=body['gender'],
        hair_color=body['hair_color'],
        height=body['height'],
        mass=body['mass'],
        skin_color=body['skin_color']
    )
    db.session.add(new_person)
    db.session.commit()

    return jsonify({"sucess": True, "data": new_person.serialize()}), 200

# ADD PLANET -----------

@app.route("/planets", methods=["POST"])
def add_planet():
    body = request.get_json()
    if not body['name'] or not body["diameter"] or not body['population'] or not body['climate'] or not body['terrain'] or not body['surface_water'] or not body['gravity']:
        return jsonify({'sucess': False, 'msg': 'missing data'}), 403

    new_planet = Planet(
        name=body['name'],
        diameter=body['diameter'],
        gravity=body['gravity'],
        population=body['population'],
        climate=body['climate'],
        terrain=body['terrain'],
        surface_water=body['surface_water']
    )
    db.session.add(new_planet)
    db.session.commit()

    return jsonify({"sucess": True, "data": new_planet.serialize()}), 200

# GET PPL BY ID -----------

@app.route("/people/<int:id>", methods=["GET"])
def get_one_person(id):
    person = db.session.get(People, id)
    return jsonify({"sucess": True, "data": person.serialize()}), 200

# GET PLANET DETAILS -----------

@app.route("/planet/<int:id>", methods=["GET"])
def get_planet_details(id):
    planet = db.session.get(Planet, id)
    return jsonify({"sucess": True, "data": planet.serialize()}), 200
    
# UPDATE PPL -------------

@app.route("/people/update/<int:id>", methods=["PUT"])
def modify_person(id):
    person = db.session.get(People, id)
    if not person:
        return jsonify({"success": False, "data": "not found"}), 404
    body = request.get_json()

    person.name = body["name"] if body["name"] else person.name
    person.birth_year = body["birth_year"] if body["birth_year"] else person.birth_year
    person.eye_color = body["eye_color"] if body["eye_color"] else person.eye_color
    person.gender = body["gender"] if body["gender"] else person.gender
    person.hair_color = body["hair_color"] if body["hair_color"] else person.hair_color
    person.height = body["height"] if body["height"] else person.height
    person.mass = body["mass"] if body["mass"] else person.mass
    person.skin_color = body["skin_color"] if body["skin_color"] else person.skin_color

    db.session.commit()

    return jsonify({"sucess": True, "data": person.serialize()})

# DELETE PPL -----------

@app.route("/people/delete/<int:id>", methods=["DELETE"])
def delete_person(id):
    person = db.session.get(People, id)
    db.session.delete(person)
    db.session.commit()
    return jsonify({"sucess": True, "data": "user delete " + str(id)}), 200


# GET USER FAVS -----------

@app.route("/users/favorites/<int:id>", methods=["GET"])
def get_favorites(id):

    favs = Favorite.query.filter_by(user_id=id).all()
    if len(favs) == 0:
        return jsonify({"msg": "No favorites added yet"}), 404
    return jsonify([f.serialize() for f in favs]), 200

# DELETE USER ALL HIS FAVS -----------

@app.route("/users/favorites/<int:id>", methods=["DELETE"])
def delete_all_favorites(id):

    favs = Favorite.query.filter_by(user_id=id).all()

    if not favs:
        return jsonify({"msg": "No favorites to delete"}), 404

    for fav in favs:
        db.session.delete(fav)

    db.session.commit()

    return jsonify({"msg": "All favorites deleted"}), 200

# DELETE ONLY PLANET FROM FAVS

@app.route("/favorite/planet/<int:planet_id>", methods=["DELETE"])
def delete_fav_planet(planet_id):
    CURRENT_USER_ID = 1 # RETRIEVE THIS VALUE FROM THE LOCAL STORAGE

    fav = Favorite.query.filter_by(
        user_id=CURRENT_USER_ID,
        planet_id=planet_id
    ).first()

    if not fav:
        return jsonify({"error": "not found"}), 404

    db.session.delete(fav)
    db.session.commit()

    return jsonify({"msg": "deleted"}), 200

# DELETE ONLY PPL FROM FAVS

@app.route("/favorite/people/<int:people_id>", methods=["DELETE"])
def delete_fav_people(people_id):
    CURRENT_USER_ID = 1

    fav = Favorite.query.filter_by(
        user_id=CURRENT_USER_ID,
        people_id=people_id
    ).first()

    if not fav:
        return jsonify({"error": "not found"}), 404

    db.session.delete(fav)
    db.session.commit()

    return jsonify({"msg": "deleted"}), 200

# ADD ONLY A PLANET TO FAVS, SO WE CAND DELETE LATER ONLY THIS FAV

@app.route("/favorite/planet/<int:planet_id>", methods=["POST"])
def add_fav_planet(planet_id):
    CURRENT_USER_ID = 1  

    fav = Favorite(
        user_id=CURRENT_USER_ID,
        planet_id=planet_id
    )

    db.session.add(fav)
    db.session.commit()

    return jsonify({"msg": "planet added to favorites"}), 201

# ADD ONLY A PERSON TO FAVS, SO WE CAND DELETE LATER ONLY THIS FAV

@app.route("/favorite/people/<int:people_id>", methods=["POST"])
def add_fav_people(people_id):
    CURRENT_USER_ID = 1

    fav = Favorite(
        user_id=CURRENT_USER_ID,
        people_id=people_id
    )

    db.session.add(fav)
    db.session.commit()

    return jsonify({"msg": "people added to favorites"}), 201


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
