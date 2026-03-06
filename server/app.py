#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json() or {}

        username = data.get('username')
        password = data.get('password')
        password_confirmation = data.get('password_confirmation')
        image_url = data.get('image_url')
        bio = data.get('bio')

        errors = []
        if not username:
            errors.append('Username is required.')
        if not password:
            errors.append('Password is required.')
        if (
            password
            and password_confirmation is not None
            and password != password_confirmation
        ):
            errors.append('Password confirmation must match password.')

        if errors:
            return {'errors': errors}, 422

        try:
            user = User(
                username=username,
                image_url=image_url,
                bio=bio,
            )
            user.password_hash = password

            db.session.add(user)
            db.session.commit()
        except (ValueError, IntegrityError) as exc:
            db.session.rollback()

            if isinstance(exc, IntegrityError):
                return {'errors': ['Username has already been taken.']}, 422

            return {'errors': [str(exc)]}, 422

        session['user_id'] = user.id
        return user.to_dict(only=('id', 'username', 'image_url', 'bio')), 201

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {'error': 'Unauthorized'}, 401

        return user.to_dict(only=('id', 'username', 'image_url', 'bio')), 200

class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and password and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(only=('id', 'username', 'image_url', 'bio')), 200

        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id', None)
            return '', 204

        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    pass

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
