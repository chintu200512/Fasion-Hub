from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    email = data.get('email')
    password = data.get('password')
    
    user = User.authenticate(email, password)
    if user:
        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        return jsonify({'success': True, 'redirect': url_for('product.index')})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() if request.is_json else request.form
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    address = data.get('address')
    phone = data.get('phone')
    
    user, message = User.create_user(email, password, name, address, phone)
    if user:
        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        return jsonify({'success': True, 'redirect': url_for('product.index')})
    
    return jsonify({'success': False, 'message': message}), 400

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('product.index'))

@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.get_user_by_id(session['user_id'])
    return render_template('profile.html', user=user)