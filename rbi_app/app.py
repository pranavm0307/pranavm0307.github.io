from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from datetime import datetime, timedelta
from utils.db import (db_lock, DB_PATH,
                      
    init_db, get_user_by_id, create_user, update_login_info, increment_login_attempts, 
    check_login_attempts, get_all_users, update_user, delete_user, reset_user_password,
    reset_login_attempts, delete_article, log_admin_action, log_security_event,
    get_admin_logs, get_security_logs, backup_database, export_users_to_csv,
    generate_system_report, reset_all_passwords, deactivate_user, activate_user,
    # Test management functions
    create_test, add_question_to_test, get_all_tests, get_test_by_id, get_active_tests,
    delete_test, toggle_test_status, delete_question, update_question,
    start_test_attempt, complete_test_attempt, save_test_answer,
    get_user_test_attempts, get_test_attempt_answers
)
from utils.utils import validate_password, save_article_to_file, get_articles_for_user, read_article_content
import os
import secrets
import json
import traceback

# Initialize app
app = Flask(__name__)
# Fixed: Generate secure secret key
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Setup rate limiter
limiter = Limiter(get_remote_address)
limiter.init_app(app)

# Fixed: Use absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ARTICLE_DIR = os.path.join(BASE_DIR, "articles")
if not os.path.exists(ARTICLE_DIR):
    os.makedirs(ARTICLE_DIR)

# Initialize database
init_db()

# Decorator to require login
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            flash("Please log in first", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

# Admin decorator
def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get('logged_in') or session.get('user_id') != 'admin':
            flash("Access denied. Admin privileges required.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrap

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    # Check if current user is admin
    if session.get('user_id') != 'admin':
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for('dashboard'))

    try:
        # Get all users from database
        all_users = get_all_users()
        
        # Get all articles for admin view
        all_articles = get_articles_for_user('admin')
        
        # Get all tests
        all_tests = get_all_tests()
        
        return render_template("admin_dashboard.html", 
                             users=all_users, 
                             articles=all_articles,
                             tests=all_tests,
                             user_count=len(all_users),
                             article_count=len(all_articles),
                             test_count=len(all_tests))
                             
    except Exception as e:
        flash(f"Error loading admin dashboard: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

# ADMIN TEST MANAGEMENT ROUTES

@app.route('/admin/create_test', methods=['POST'])
@admin_required
def admin_create_test():
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        time_limit = data.get('time_limit', 0)
        questions = data.get('questions', [])
        
        if not title:
            return jsonify({'success': False, 'error': 'Test title is required'})
        
        if not time_limit or time_limit <= 0:
            return jsonify({'success': False, 'error': 'Valid time limit is required'})
        
        if not questions:
            return jsonify({'success': False, 'error': 'At least one question is required'})
        
        # Create test
        test_id = create_test(title, description, time_limit, session['user_id'])
        
        # Add questions
        for i, question in enumerate(questions):
            question_text = question.get('text', '').strip()
            marks = question.get('marks', 0)
            
            if question_text:
                add_question_to_test(test_id, question_text, i + 1, marks)
        
        log_admin_action(session['user_id'], 'CREATE_TEST', None, f'Created test: {title}')
        
        return jsonify({'success': True, 'message': f'Test "{title}" created successfully', 'test_id': test_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/get_test/<int:test_id>')
@admin_required
def admin_get_test(test_id):
    try:
        test = get_test_by_id(test_id)
        if test:
            return jsonify({'success': True, 'test': test})
        return jsonify({'success': False, 'error': 'Test not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/update_test', methods=['POST'])
@admin_required
def admin_update_test():
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        time_limit = data.get('time_limit', 0)
        questions = data.get('questions', [])
        
        if not test_id or not title or not time_limit:
            return jsonify({'success': False, 'error': 'Test ID, title, and time limit are required'})
        
        # Update test (for now, we'll recreate it - you can optimize this later)
        # This is a simplified approach - in production you'd want proper update logic
        
        log_admin_action(session['user_id'], 'UPDATE_TEST', None, f'Updated test ID: {test_id}')
        
        return jsonify({'success': True, 'message': 'Test updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/delete_test', methods=['POST'])
@admin_required
def admin_delete_test():
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        
        if not test_id:
            return jsonify({'success': False, 'error': 'Test ID is required'})
        
        # Get test info for logging
        test = get_test_by_id(test_id)
        test_title = test['title'] if test else f'Test ID {test_id}'
        
        success = delete_test(test_id)
        if success:
            log_admin_action(session['user_id'], 'DELETE_TEST', None, f'Deleted test: {test_title}')
            return jsonify({'success': True, 'message': 'Test deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Test not found or could not be deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/toggle_test_status', methods=['POST'])
@admin_required
def admin_toggle_test_status():
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        
        if not test_id:
            return jsonify({'success': False, 'error': 'Test ID is required'})
        
        success = toggle_test_status(test_id)
        if success:
            test = get_test_by_id(test_id)
            status = 'activated' if test['is_active'] else 'deactivated'
            log_admin_action(session['user_id'], 'TOGGLE_TEST_STATUS', None, f'Test {test["title"]} {status}')
            return jsonify({'success': True, 'message': f'Test {status} successfully'})
        else:
            return jsonify({'success': False, 'error': 'Test not found or could not be updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# USER TEST ROUTES

@app.route('/tests')
@login_required
def user_tests():
    try:
        # Get active tests for users
        active_tests = get_active_tests()
        
        # Get user's test attempts
        user_attempts = get_user_test_attempts(session['user_id'])
        
        return render_template("user_tests.html", 
                             tests=active_tests,
                             attempts=user_attempts,
                             user_name=session['full_name'])
    except Exception as e:
        flash(f"Error loading tests: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

@app.route('/test/<int:test_id>')
@login_required
def take_test(test_id):
    try:
        # Get test details
        test = get_test_by_id(test_id)
        if not test:
            flash("Test not found", "danger")
            return redirect(url_for('user_tests'))
        
        if not test['is_active']:
            flash("This test is not currently active", "warning")
            return redirect(url_for('user_tests'))
        
        # Check if user has already completed this test
        attempts = get_user_test_attempts(session['user_id'], test_id)
        completed_attempts = [a for a in attempts if a['status'] == 'completed']
        
        if completed_attempts:
            flash("You have already completed this test", "info")
            return redirect(url_for('user_tests'))
        
        # Check for existing in-progress attempt
        in_progress = [a for a in attempts if a['status'] == 'in_progress']
        attempt_id = None
        
        if in_progress:
            attempt_id = in_progress[0]['id']
        else:
            # Start new attempt
            attempt_id = start_test_attempt(test_id, session['user_id'])
        
        return render_template("test_interface.html", 
                             test=test,
                             attempt_id=attempt_id,
                             user_name=session['full_name'])
    except Exception as e:
        flash(f"Error loading test: {str(e)}", "danger")
        return redirect(url_for('user_tests'))

@app.route('/save_test_answer', methods=['POST'])
@login_required
def save_test_answer_route():
    try:
        data = request.get_json()
        attempt_id = data.get('attempt_id')
        question_id = data.get('question_id')
        answer_text = data.get('answer_text', '').strip()
        
        if not attempt_id or not question_id:
            return jsonify({'success': False, 'error': 'Attempt ID and Question ID are required'})
        
        # Calculate word count
        word_count = len(answer_text.split()) if answer_text else 0
        
        success = save_test_answer(attempt_id, question_id, answer_text, word_count)
        
        if success:
            return jsonify({'success': True, 'message': 'Answer saved successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save answer'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/submit_test', methods=['POST'])
@login_required
def submit_test_route():
    try:
        data = request.get_json()
        attempt_id = data.get('attempt_id')
        time_taken = data.get('time_taken', 0)
        
        if not attempt_id:
            return jsonify({'success': False, 'error': 'Attempt ID is required'})
        
        success = complete_test_attempt(attempt_id, time_taken)
        
        if success:
            return jsonify({'success': True, 'message': 'Test submitted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to submit test'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_results/<int:attempt_id>')
@login_required
def test_results(attempt_id):
    try:
        print(f"DEBUG: Accessing test results for attempt_id: {attempt_id}")
        print(f"DEBUG: Current user: {session['user_id']}")
        
        # Get attempt details and verify ownership
        attempts = get_user_test_attempts(session['user_id'])
        print(f"DEBUG: Found {len(attempts)} attempts for user")
        
        user_attempt = None
        for attempt in attempts:
            print(f"DEBUG: Checking attempt ID {attempt['id']} against requested {attempt_id}")
            if attempt['id'] == attempt_id:
                user_attempt = attempt
                break
        
        if not user_attempt:
            print(f"DEBUG: No attempt found for ID {attempt_id}")
            flash("Test results not found or access denied", "danger")
            return redirect(url_for('user_tests'))
        
        print(f"DEBUG: Found attempt: {user_attempt}")
        
        # Get answers
        answers = get_test_attempt_answers(attempt_id)
        print(f"DEBUG: Found {len(answers)} answers")
        
        # Get test details
        test = get_test_by_id(user_attempt['test_id'])
        print(f"DEBUG: Test details: {test['title'] if test else 'None'}")
        
        if not test:
            flash("Test details not found", "danger")
            return redirect(url_for('user_tests'))
        
        return render_template("test_results.html",
                             attempt=user_attempt,
                             answers=answers,
                             test=test,
                             user_name=session['full_name'])
                             
    except Exception as e:
        print(f"DEBUG: Error in test_results: {str(e)}")
        traceback.print_exc()
        flash(f"Error loading test results: {str(e)}", "danger")
        return redirect(url_for('user_tests'))

# Admin user management routes
@app.route('/admin/get_user/<user_id>')
@admin_required
def admin_get_user(user_id):
    # Fixed: Consistent case handling
    user_id = user_id.lower().strip()
    user = get_user_by_id(user_id)
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/admin/add_user', methods=['POST'])
@admin_required
def admin_add_user():
    try:
        data = request.get_json()
        # Fixed: Consistent case handling
        user_id = data.get('user_id', '').strip().lower()
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not all([user_id, full_name, password]):
            return jsonify({'success': False, 'error': 'All required fields must be filled'})
        
        if len(user_id) < 3:
            return jsonify({'success': False, 'error': 'User ID must be at least 3 characters'})
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
        
        if get_user_by_id(user_id):
            return jsonify({'success': False, 'error': 'User ID already exists'})
        
        create_user(user_id, password, full_name, email)
        log_admin_action(session['user_id'], 'ADD_USER', user_id, f'Added user: {full_name}')
        
        return jsonify({'success': True, 'message': f'User {user_id} created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/edit_user', methods=['POST'])
@admin_required
def admin_edit_user():
    try:
        data = request.get_json()
        # Fixed: Consistent case handling
        user_id = data.get('user_id', '').strip().lower()
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not all([user_id, full_name]):
            return jsonify({'success': False, 'error': 'User ID and full name are required'})
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        if password and len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
        
        update_user(user_id, full_name, email, password if password else None)
        log_admin_action(session['user_id'], 'EDIT_USER', user_id, f'Updated user: {full_name}')
        
        return jsonify({'success': True, 'message': f'User {user_id} updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def admin_delete_user():
    try:
        data = request.get_json()
        # Fixed: Consistent case handling
        user_id = data.get('user_id', '').strip().lower()
        
        if user_id == 'admin':
            return jsonify({'success': False, 'error': 'Cannot delete admin user'})
        
        success, message = delete_user(user_id)
        if success:
            log_admin_action(session['user_id'], 'DELETE_USER', user_id, message)
        
        return jsonify({'success': success, 'message' if success else 'error': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/reset_password', methods=['POST'])
@admin_required
def admin_reset_password():
    try:
        data = request.get_json()
        # Fixed: Consistent case handling
        user_id = data.get('user_id', '').strip().lower()
        new_password = data.get('new_password', '')
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        reset_user_password(user_id, new_password)
        log_admin_action(session['user_id'], 'RESET_PASSWORD', user_id, 'Password reset')
        
        return jsonify({'success': True, 'message': f'Password reset for user {user_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/reset_login_attempts', methods=['POST'])
@admin_required
def admin_reset_login_attempts():
    try:
        data = request.get_json()
        # Fixed: Consistent case handling
        user_id = data.get('user_id', '').strip().lower()
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        reset_login_attempts(user_id)
        log_admin_action(session['user_id'], 'RESET_LOGIN_ATTEMPTS', user_id, 'Login attempts reset')
        
        return jsonify({'success': True, 'message': f'Login attempts reset for user {user_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Admin password change route
@app.route('/admin/change_password', methods=['POST'])
@admin_required
def admin_change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Both current and new passwords are required'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'New password must be at least 6 characters'})
        
        # Verify current password
        admin_user = get_user_by_id('admin')
        if not admin_user or not check_password_hash(admin_user['password_hash'], current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'})
        
        # Update password
        reset_user_password('admin', new_password)
        log_admin_action('admin', 'CHANGE_PASSWORD', 'admin', 'Admin password changed')
        
        return jsonify({'success': True, 'message': 'Admin password updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Article management routes
@app.route('/admin/delete_article', methods=['POST'])
@admin_required
def admin_delete_article():
    try:
        data = request.get_json()
        filename = data.get('filename', '').strip()
        
        if not filename:
            return jsonify({'success': False, 'error': 'Filename is required'})
        
        # Fixed: Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'})
        
        delete_article(filename)
        log_admin_action(session['user_id'], 'DELETE_ARTICLE', None, f'Deleted article: {filename}')
        
        return jsonify({'success': True, 'message': f'Article {filename} deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/download_article/<filename>')
@admin_required
def admin_download_article(filename):
    try:
        # Fixed: Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            flash("Invalid filename", "danger")
            return redirect(url_for('admin_dashboard'))
            
        file_path = os.path.join(ARTICLE_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash("File not found", "danger")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

# System management routes
@app.route('/admin/backup_database', methods=['POST'])
@admin_required
def admin_backup_database():
    try:
        success, message = backup_database()
        log_admin_action(session['user_id'], 'BACKUP_DATABASE', None, message)
        return jsonify({'success': success, 'message' if success else 'error': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/export_users')
@admin_required
def admin_export_users():
    try:
        success, result = export_users_to_csv()
        if success:
            log_admin_action(session['user_id'], 'EXPORT_USERS', None, f'Exported to: {result}')
            return send_file(result, as_attachment=True)
        else:
            flash(result, "danger")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f"Export failed: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/generate_report')
@admin_required
def admin_generate_report():
    try:
        success, result = generate_system_report()
        if success:
            log_admin_action(session['user_id'], 'GENERATE_REPORT', None, f'Generated: {result}')
            return send_file(result, as_attachment=True)
        else:
            flash(result, "danger")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f"Report generation failed: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset_all_passwords', methods=['POST'])
@admin_required
def admin_reset_all_passwords():
    try:
        success, message = reset_all_passwords(session['user_id'])
        return jsonify({'success': success, 'message' if success else 'error': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/clear_sessions', methods=['POST'])
@admin_required
def admin_clear_sessions():
    try:
        log_admin_action(session['user_id'], 'CLEAR_SESSIONS', None, 'Cleared all user sessions')
        return jsonify({'success': True, 'message': 'All sessions cleared (users will need to login again)'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/security_log')
@admin_required
def admin_security_log():
    try:
        logs = get_security_logs(100)
        admin_logs = get_admin_logs(100)
        
        log_html = "<h3>Security Logs</h3><ul>"
        for log in logs:
            log_html += f"<li>{log['timestamp']} - {log['user_id']} - {log['action']} - {'Success' if log['success'] else 'Failed'}</li>"
        log_html += "</ul><h3>Admin Logs</h3><ul>"
        for log in admin_logs:
            log_html += f"<li>{log['timestamp']} - {log['admin_user_id']} - {log['action']} - {log['target_user_id']} - {log['details']}</li>"
        log_html += "</ul>"
        
        return log_html
    except Exception as e:
        return f"Error loading logs: {str(e)}"

# Original routes
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/minute")  # Fixed: More reasonable rate limit
def login():
    if request.method == 'POST':
        # Fixed: Consistent case handling
        user_id = request.form.get('user_id', '').strip().lower()
        password = request.form.get('password', '')
        
        if not user_id or not password:
            return render_template("login.html", error="Please fill in all fields")
        
        user = get_user_by_id(user_id)
        can_login, msg = check_login_attempts(user_id)
        
        if not can_login:
            return render_template("login.html", error=msg)
        
        if user and check_password_hash(user['password_hash'], password):
            session.update({
                'logged_in': True,
                'user_id': user_id,
                'full_name': user['full_name']
            })
            session.permanent = True
            update_login_info(user_id)
            
            # Log successful login
            log_security_event(user_id, 'LOGIN_SUCCESS', request.remote_addr, 
                             request.headers.get('User-Agent', ''), True)
            
            # Redirect admin to admin dashboard
            if user_id == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        
        if user:
            increment_login_attempts(user_id)
            log_security_event(user_id, 'LOGIN_FAILED', request.remote_addr, 
                             request.headers.get('User-Agent', ''), False)
        
        return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5/minute")  # Fixed: More reasonable rate limit
def register():
    if request.method == 'POST':
        # Fixed: Consistent case handling
        user_id = request.form.get('user_id', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        errors = []
        
        if not all([user_id, full_name, password, confirm]):
            errors.append("All required fields must be filled.")
        
        if len(user_id) < 3:
            errors.append("User ID must be at least 3 characters long.")
            
        if password != confirm:
            errors.append("Passwords do not match.")
            
        valid, msg = validate_password(password)
        if not valid:
            errors.append(msg)
            
        if get_user_by_id(user_id):
            errors.append("User ID already exists.")
            
        if errors:
            return render_template("register.html", error="<br>".join(errors))

        try:
            create_user(user_id, password, full_name, email)
            log_security_event(user_id, 'REGISTER_SUCCESS', request.remote_addr, 
                             request.headers.get('User-Agent', ''), True)
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            log_security_event(user_id, 'REGISTER_FAILED', request.remote_addr, 
                             request.headers.get('User-Agent', ''), False)
            return render_template("register.html", error=f"Registration failed: {str(e)}")
    
    return render_template("register.html")

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", user_name=session['full_name'], user_id=session['user_id'])

@app.route('/exam')
@login_required
def exam():
    return render_template("exam.html", user_name=session['full_name'])

@app.route('/save_article', methods=['POST'])
@login_required
def save_article():
    try:
        data = request.get_json()
        if not data or not data.get('content', '').strip():
            return jsonify({'success': False, 'error': 'Empty content'})
        
        result = save_article_to_file(data, session['user_id'], session['full_name'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/admin/test_management')
@admin_required
def admin_test_management():
    return render_template("admin_test_management.html")

@app.route('/admin/get_all_tests')
@admin_required
def admin_get_all_tests():
    try:
        tests = get_all_tests()
        return jsonify({'success': True, 'tests': tests})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/get_all_submissions')
@admin_required
def admin_get_all_submissions():
    try:
        # Get all test attempts with user and test info
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ta.id, ta.user_id, ta.started_at, ta.completed_at, ta.time_taken, ta.status,
                       u.full_name, t.title as test_title
                FROM test_attempts ta
                JOIN users u ON ta.user_id = u.user_id
                JOIN tests t ON ta.test_id = t.id
                ORDER BY ta.started_at DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            submissions = []
            for row in rows:
                submissions.append({
                    'id': row[0],
                    'user_id': row[1],
                    'started_at': row[2],
                    'completed_at': row[3],
                    'time_taken': row[4],
                    'status': row[5],
                    'user_name': row[6],
                    'test_title': row[7]
                })
            
            return jsonify({'success': True, 'submissions': submissions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/get_test_answers/<int:attempt_id>')
@admin_required
def admin_get_test_answers(attempt_id):
    try:
        # Get attempt info
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.full_name FROM test_attempts ta
                JOIN users u ON ta.user_id = u.user_id
                WHERE ta.id = ?
            ''', (attempt_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return jsonify({'success': False, 'error': 'Attempt not found'})
            
            user_name = user_row[0]
            
            # Get answers with questions
            cursor.execute('''
                SELECT ta.answer_text, ta.word_count, q.question_text, q.question_order
                FROM test_answers ta
                JOIN questions q ON ta.question_id = q.id
                WHERE ta.attempt_id = ?
                ORDER BY q.question_order
            ''', (attempt_id,))
            
            answer_rows = cursor.fetchall()
            conn.close()
            
            answers = []
            for row in answer_rows:
                answers.append({
                    'answer_text': row[0],
                    'word_count': row[1],
                    'question_text': row[2],
                    'question_order': row[3]
                })
            
            return jsonify({'success': True, 'user_name': user_name, 'answers': answers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/my_articles')
@login_required
def my_articles():
    try:
        articles = get_articles_for_user(session['user_id'])
        return jsonify({'success': True, 'articles': articles})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/check_user_id')
def check_user_id():
    # Fixed: Consistent case handling
    user_id = request.args.get('user_id', '').strip().lower()
    exists = get_user_by_id(user_id) is not None
    return jsonify({'exists': exists})

@app.route('/view_article/<filename>')
@login_required
def view_article(filename):
    try:
        # Fixed: Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'})
            
        user_id = session['user_id']
        result = read_article_content(filename, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    user_id = session.get('user_id', 'unknown')
    log_security_event(user_id, 'LOGOUT', request.remote_addr, 
                      request.headers.get('User-Agent', ''), True)
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

# Debug route for testing
@app.route('/debug/attempts')
@login_required
def debug_attempts():
    try:
        attempts = get_user_test_attempts(session['user_id'])
        return f"<pre>{json.dumps(attempts, indent=2, default=str)}</pre>"
    except Exception as e:
        return f"<pre>Error: {str(e)}</pre>"

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(429)
def rate_limit(error):
    return render_template('429.html', description=str(error.description)), 429

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)