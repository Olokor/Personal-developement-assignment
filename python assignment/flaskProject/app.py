from datetime import datetime

from bson import ObjectId
from flask import Flask, render_template, jsonify, request, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

app = Flask(__name__)

# Configuration
app.secret_key = os.urandom(24)
app.config["MONGO_URI"] = 'mongodb://localhost:27017/user_db'  # Changed database name
mongo = PyMongo(app)

# Ensure the collection exists
try:
    mongo.db.create_collection('users')
    mongo.db.create_collection('auctions')
except:
    pass  # Collection already exists

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"status": 401, "message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function
# @app.route('/')
# def hello_world():
#     return render_template('create_user.html')
#
# @app.route("/home", methods=["GET", "POST"])
# def home():
#     if request.method == "POST":
#         # Check if form data exists
#         if not request.form:
#             return "No form data submitted", 400
#
#         # Get form data with error handling
#         username = request.form.get("username")
#         email = request.form.get("email")
#         password = request.form.get("password")
#
#         # Validate required fields
#         if not all([username, email, password]):
#             return "Missing required fields (username, email, password)", 400
#
#         try:
#             # Insert new user
#             mongo.db.users.insert_one({
#                 "username": username,
#                 "email": email,
#                 "password": generate_password_hash(password)
#             })
#             return "User created successfully"
#         except Exception as e:
#             return f"Error creating user: {str(e)}", 500
#
#     # For GET requests, show the form
#     return render_template('create_user.html')
@app.route("/create-user", methods=["POST"])
def add_user():
    try:
        _json = request.get_json()
        _name = _json["username"]
        _email = _json["email"]
        _password = _json["password"]

        if _name and _email and _password:
            # Using insert_one() and proper error handling
            mongo.db.users.insert_one({
                "username": _name,
                "email": _email,
                "password": generate_password_hash(_password)
            })

            return jsonify({"status": 200, "message": "User added successfully"}), 200
        else:
            return jsonify({"status": 400, "message": "Missing required fields"}), 400
    except Exception as e:
        return jsonify({"status": 500, "message": str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        _json = request.get_json()
        print(_json)

        # Check if JSON data exists and has required fields
        if not _json or 'email' not in _json or 'password' not in _json:
            return jsonify({
                "status": 400,
                "message": "Missing email or password in request"
            }), 400

        email = _json['email']
        password = _json['password']

        # Find user by email
        user = mongo.db.users.find_one({'email': email})

        # Verify user exists and password matches
        if not user:
            return jsonify({
                "status": 401,
                "message": "Invalid email or password"
            }), 401

        if not check_password_hash(user['password'], password):
            return jsonify({
                "status": 401,
                "message": "Invalid email or password"
            }), 401

        # Store user ID in session
        session['user_id'] = str(user['_id'])

        return jsonify({
            "status": 200,
            "message": "Login successful",
            "user": {
                "id": str(user['_id']),
                "username": user['username'],
                "email": user['email']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": 500,
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({"status": 200, "message": "Logged out"}), 200
@app.route("/create-auction", methods=["POST"])
@login_required
def create_auction():
    try:
        _json = request.get_json()
        required_field = ['auction_item_name', 'base_price']
        if not all(field in _json for field in required_field):
            return jsonify({"status": 400, "message": "Missing required fields"}), 400

        seller_id = session['user_id']
        auction_item_name = {
            "auction_item_name": _json["auction_item_name"],
            "base_price": _json["base_price"],
            "seller_id": seller_id,
            "active":True,
            "created_at":datetime.utcnow(),
            "bid":[]
        }
        result = mongo.db.auctions.insert_one(auction_item_name)
        return jsonify({
            "status": 201,
            "message": "Auction created successfully",
            "auction_id": str(result.inserted_id)
        }), 201
    except ValueError:
        return jsonify({"status": 400, "message": "Invalid price format"}), 400
    except Exception as e:
        return jsonify({"status": 500, "message": str(e)}), 500


@app.route('/get-all-auctions', methods=['GET'])
@login_required
def get_all_auctions():
    try:
        # Get pagination params with defaults
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        skip = (page - 1) * per_page

        # Get auctions from database
        auctions = list(mongo.db.auctions.find().skip(skip).limit(per_page))

        # Prepare response data
        data = []
        for auction in auctions:
            # Calculate current price (highest bid or base price)
            bids = auction.get('bids', [])
            current_price = auction.get('base_price')
            if bids:
                current_price = max(bid['amount'] for bid in bids if 'amount' in bid) if bids else current_price

            # Get seller info
            seller = mongo.db.users.find_one(
                {'_id': auction['seller_id']},
                {'username': 1, 'email': 1}
            ) if auction.get('seller_id') else None

            data.append({
                'auction_id': str(auction['_id']),
                'item_name': auction.get('auction_item_name'),
                'current_price': current_price,
                'base_price': auction.get('base_price'),
                'status': auction.get('status', 'active'),
                'created_at': auction.get('created_at', '').isoformat() if auction.get('created_at') else '',
                'seller': {
                    'id': str(seller['_id']) if seller else None,
                    'username': seller.get('username') if seller else None,
                    'email': seller.get('email') if seller else None
                } if seller else None,
                'bid_count': len(bids)
            })

        # Get total count
        total_auctions = mongo.db.auctions.count_documents({})

        return jsonify({
            'status': 200,
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': total_auctions,
                'total_pages': (total_auctions + per_page - 1) // per_page
            }
        })

    except Exception as e:
        return jsonify({
            'status': 500,
            'message': 'Server error',
            'error': str(e)  # Remove in production
        }), 500

@app.route('/auctions/<auction_id>/bids', methods=['POST'])
@login_required
def add_bid(auction_id):
    try:
        # 1. Validate input data
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        if not data or 'amount' not in data:
            return jsonify({'error': 'Missing bid amount'}), 400

        try:
            bid_amount = float(data['amount'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Bid amount must be a number'}), 400

        # 2. Validate auction exists
        if not ObjectId.is_valid(auction_id):
            return jsonify({'error': 'Invalid auction ID'}), 400

        auction = mongo.db.auctions.find_one({'_id': ObjectId(auction_id)})
        if not auction:
            return jsonify({'error': 'Auction not found'}), 404

        # 3. Get current price (base price or highest bid)
        current_price = auction['base_price']
        if auction.get('bids'):
            try:
                current_price = max(bid['amount'] for bid in auction['bids'])
            except (KeyError, ValueError):
                current_price = auction['base_price']

        # 4. Validate bid amount
        if bid_amount <= float(current_price):
            return jsonify({
                'error': f'Bid must be higher than {current_price}'
            }), 400

        # 5. Create and save bid
        new_bid = {
            'amount': bid_amount,
            'user_id': ObjectId(session['user_id']),
            'timestamp': datetime.utcnow(),
            'status': 'active'
        }

        result = mongo.db.auctions.update_one(
            {'_id': ObjectId(auction_id)},
            {'$push': {'bids': new_bid}}
        )

        if result.modified_count == 1:
            return jsonify({
                'success': True,
                'new_price': bid_amount,
                'bid': {
                    'id': str(new_bid.get('_id', '')),
                    'amount': bid_amount,
                    'timestamp': new_bid['timestamp'].isoformat()
                }
            }), 201

        return jsonify({'error': 'Failed to save bid'}), 500

    except Exception as e:
        app.logger.error(f"Error in add_bid: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500



@app.errorhandler(404)
def not_found(error=None)->jsonify:
    message = {
        'status': 404,
        'message': "NOT FOUND" + request.url
    }
    return jsonify(message), 404



if __name__ == '__main__':
    app.run(debug=True)