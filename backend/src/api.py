from functools import wraps
import os
import sys
from flask import Flask, request, jsonify, abort
# from matplotlib.pyplot import title
from sqlalchemy import exc
import json
from flask_cors import CORS
from jose import jwt
from urllib.request import urlopen

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth, get_token_auth_header, check_permissions, verify_decode_jwt

app = Flask(__name__)
setup_db(app)
CORS(app)

# class AuthError(Exception):
#     def __init__(self, error, status_code):
#         self.error = error
#         self.status_code = status_code

# def get_token_auth_header():
#   if 'Authorization' not in request.headers:
#     abort(401)
#   auth_headers = request.headers['Authorization']
#   headers_part = auth_headers.split(' ')
#   if len(headers_part) != 2:
#     abort(401)
#   if headers_part[0].lower() != 'bearer':
#     abort(401)
#   return headers_part[1]

# def verify_decode_jwt(token):
#     jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
#     jwks = json.loads(jsonurl.read())
#     unverified_header = jwt.get_unverified_header(token)
#     rsa_key = {}
#     if 'kid' not in unverified_header:
#         raise AuthError({
#             'code': 'invalid_header',
#             'description': 'Authorization malformed.'
#         }, 401)

#     for key in jwks['keys']:
#         if key['kid'] == unverified_header['kid']:
#             rsa_key = {
#                 'kty': key['kty'],
#                 'kid': key['kid'],
#                 'use': key['use'],
#                 'n': key['n'],
#                 'e': key['e']
#             }
#     if rsa_key:
#         try:
#             payload = jwt.decode(
#                 token,
#                 rsa_key,
#                 algorithms=ALGORITHMS,
#                 audience=API_AUDIENCE,
#                 issuer='https://' + AUTH0_DOMAIN + '/'
#             )

#             return payload

#         except jwt.ExpiredSignatureError:
#             raise AuthError({
#                 'code': 'token_expired',
#                 'description': 'Token expired.'
#             }, 401)

#         except jwt.JWTClaimsError:
#             raise AuthError({
#                 'code': 'invalid_claims',
#                 'description': 'Incorrect claims. Please, check the audience and issuer.'
#             }, 401)
#         except Exception:
#             raise AuthError({
#                 'code': 'invalid_header',
#                 'description': 'Unable to parse authentication token.'
#             }, 400)
#     raise AuthError({
#                 'code': 'invalid_header',
#                 'description': 'Unable to find the appropriate key.'
#             }, 400)

# def check_permissions(permission, payload):
#     if 'permissions' not in payload:
#       raise AuthError({
#           'code': 'invalid_claims',
#           'description': 'Permissions not included in JWT.'
#       }, 400)

#     if permission not in payload['permissions']:
#       raise AuthError({
#           'code': 'unauthorized',
#           'description': 'Permission not found.'
#       }, 403)
#     return True

# def requires_auth(permission=''):
#   def requires_auth_decorator(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):
#       jwt = get_token_auth_header()
#       try:
#         payload = verify_decode_jwt(jwt)
#       except:
#         abort(401)
      
#       check_permissions(permission, payload)
#       return f(payload, *args, **kwargs)
#     return wrapper
#   return requires_auth_decorator

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def fetch_drink():
    drink_raw = Drink.query.order_by(Drink.id).all()
    # drinks = [drink.short() for drink in drink_raw]
    # print(drinks)

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drink_raw]
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail')
@requires_auth('get:drinks-details')
def drinks_detail(jwt):
    drink_raw = Drink.query.order_by(Drink.id).all()
    drinks = [drink.long() for drink in drink_raw]
    # print(drinks)
    return jsonify({
        'success': True,
        'drinks': drinks
    })

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drinks(jwt):
    body = request.get_json()

    new_title = body['title']
    new_recipes = json.dumps(body['recipe'])
    print(new_recipes)

    try:
        new_drink = Drink(title=new_title, recipe=new_recipes)
        new_drink.insert()

        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        })
    except:
        print(sys.exc_info())
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(jwt, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)
    body = request.get_json()
    if 'title' in body:
        drink.title = body['title']

    if 'recipe' in body:
        drink.recipe = json.dumps(body['recipe'])

    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(jwt, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)
    drink.delete()

    return jsonify({
        'success' : True,
        'delete': id
    })


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def resource_unavailable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401

@app.errorhandler(AuthError)
def process_AuthError(error):
    response = jsonify(error.error)
    response.status_code = error.status_code

    return response
