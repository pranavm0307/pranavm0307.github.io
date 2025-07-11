# Enhanced db.py with full admin functionality and test management features
import sqlite3
import os
import shutil
import csv
import json
import threading
from datetime import datetime
from werkzeug.security import generate_password_hash
from pathlib import Path

# Fixed: Use absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, '..', 'db')
DB_PATH = os.path.join(DB_DIR, 'users.db')
BACKUP_DIR = os.path.join(BASE_DIR, '..', 'backups')
ARTICLES_DIR = os.path.join(BASE_DIR, '..', 'articles')

# Fixed: Thread lock for database operations
db_lock = threading.Lock()

def init_db():
    """Initialize database with enhanced tables including test system"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Enhanced users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                login_attempts INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                role TEXT DEFAULT 'user'
            )
        ''')

        # Admin logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                target_user_id TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Security logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                time_limit INTEGER NOT NULL,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_order INTEGER NOT NULL,
                marks INTEGER DEFAULT 0,
                FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
            )
        ''')
        
        # User test attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                time_taken INTEGER,
                status TEXT DEFAULT 'in_progress',
                FOREIGN KEY (test_id) REFERENCES tests (id) ON DELETE CASCADE
            )
        ''')
        
        # User answers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                word_count INTEGER DEFAULT 0,
                FOREIGN KEY (attempt_id) REFERENCES test_attempts (id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
            )
        ''')

        # Create admin user if doesn't exist
        cursor.execute('SELECT * FROM users WHERE user_id = ?', ('admin',))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            admin_password_hash = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO users (user_id, password_hash, full_name, email, role) 
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', admin_password_hash, 'System Administrator', 'admin@example.com', 'admin'))
            print("✅ Admin user created: admin/admin123")

        conn.commit()
        conn.close()
        print("✅ Database initialized with test system")

def get_user_by_id(user_id):
    """Get user by ID with proper error handling"""
    if not user_id:
        return None
        
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id.lower(),))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0], 'user_id': row[1], 'password_hash': row[2],
                    'full_name': row[3], 'email': row[4], 'login_attempts': row[5],
                    'last_login': row[6], 'created_at': row[7], 'is_active': row[8],
                    'role': row[9] if len(row) > 9 else 'user'
                }
            return None
    except sqlite3.Error as e:
        print(f"Database error in get_user_by_id: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_user_by_id: {e}")
        return None

def get_all_users():
    """Get all users with enhanced info and error handling"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            users = []
            for row in rows:
                users.append({
                    'id': row[0], 'user_id': row[1], 'password_hash': row[2],
                    'full_name': row[3], 'email': row[4], 'login_attempts': row[5],
                    'last_login': row[6], 'created_at': row[7], 'is_active': row[8],
                    'role': row[9] if len(row) > 9 else 'user'
                })
            return users
    except sqlite3.Error as e:
        print(f"Database error in get_all_users: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in get_all_users: {e}")
        return []

def create_user(user_id, password, full_name, email, role='user'):
    """Create new user with validation"""
    if not user_id or not password or not full_name:
        raise ValueError("User ID, password, and full name are required")
    
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (user_id, password_hash, full_name, email, role) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id.lower(), password_hash, full_name, email, role))
            conn.commit()
            conn.close()
    except sqlite3.IntegrityError:
        raise ValueError("User ID already exists")
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def update_user(user_id, full_name, email, password=None):
    """Update user information with validation"""
    if not user_id or not full_name:
        raise ValueError("User ID and full name are required")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if password:
                if len(password) < 6:
                    raise ValueError("Password must be at least 6 characters")
                password_hash = generate_password_hash(password)
                cursor.execute('''
                    UPDATE users SET full_name = ?, email = ?, password_hash = ? WHERE user_id = ?
                ''', (full_name, email, password_hash, user_id.lower()))
            else:
                cursor.execute('''
                    UPDATE users SET full_name = ?, email = ? WHERE user_id = ?
                ''', (full_name, email, user_id.lower()))
            
            if cursor.rowcount == 0:
                raise ValueError("User not found")
                
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def delete_user(user_id):
    """Delete user and their articles with safety checks"""
    if not user_id:
        return False, "User ID is required"
        
    if user_id.lower() == 'admin':
        return False, "Cannot delete admin user"
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id.lower(),))
            if not cursor.fetchone():
                conn.close()
                return False, "User not found"
            
            # Delete user
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id.lower(),))
            conn.commit()
            conn.close()
        
        # Delete user's articles
        delete_user_articles(user_id.lower())
        
        return True, f"User {user_id} deleted successfully"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def reset_user_password(user_id, new_password):
    """Reset user password with validation"""
    if not user_id or not new_password:
        raise ValueError("User ID and new password are required")
    
    if len(new_password) < 6:
        raise ValueError("Password must be at least 6 characters")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            password_hash = generate_password_hash(new_password)
            cursor.execute('UPDATE users SET password_hash = ?, login_attempts = 0 WHERE user_id = ?', 
                           (password_hash, user_id.lower()))
            
            if cursor.rowcount == 0:
                raise ValueError("User not found")
                
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def reset_login_attempts(user_id):
    """Reset login attempts for user"""
    if not user_id:
        raise ValueError("User ID is required")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET login_attempts = 0 WHERE user_id = ?', (user_id.lower(),))
            
            if cursor.rowcount == 0:
                raise ValueError("User not found")
                
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def update_login_info(user_id):
    """Update login info with error handling"""
    if not user_id:
        return
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET login_attempts = 0, last_login = CURRENT_TIMESTAMP WHERE user_id = ?
            ''', (user_id.lower(),))
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        print(f"Database error in update_login_info: {e}")

def increment_login_attempts(user_id):
    """Increment login attempts with error handling"""
    if not user_id:
        return
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET login_attempts = login_attempts + 1 WHERE user_id = ?', (user_id.lower(),))
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        print(f"Database error in increment_login_attempts: {e}")

def check_login_attempts(user_id):
    """Check login attempts with improved logic"""
    if not user_id:
        return False, "User ID is required"
    
    try:
        user = get_user_by_id(user_id)
        if user and user['login_attempts'] >= 5:
            return False, "Account locked due to too many failed login attempts. Contact admin to unlock."
        return True, ""
    except Exception as e:
        print(f"Error checking login attempts: {e}")
        return True, ""  # Allow login if there's an error checking

# Enhanced Article Management Functions
def delete_user_articles(user_id):
    """Delete all articles for a specific user with file locking"""
    if not user_id:
        return
    
    metadata_file = os.path.join(ARTICLES_DIR, 'articles_metadata.json')
    
    if not os.path.exists(metadata_file):
        return
    
    try:
        # Use file locking for concurrent access
        import fcntl
        with open(metadata_file, 'r+', encoding='utf-8') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                articles = json.load(f) if f.read().strip() else []
                f.seek(0)
                f.truncate()
            except json.JSONDecodeError:
                articles = []
        
            # Remove user's articles from metadata and delete files
            remaining_articles = []
            for article in articles:
                if article.get('user_id', '').lower() == user_id.lower():
                    # Delete the actual file
                    file_path = os.path.join(ARTICLES_DIR, article['filename'])
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError as e:
                            print(f"Error deleting file {file_path}: {e}")
                else:
                    remaining_articles.append(article)
            
            # Save updated metadata
            json.dump(remaining_articles, f, indent=2)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
    except ImportError:
        # Fallback for systems without fcntl (Windows)
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                articles = json.load(f) if f.read().strip() else []
        except (FileNotFoundError, json.JSONDecodeError):
            articles = []
        
        # Remove user's articles from metadata and delete files
        remaining_articles = []
        for article in articles:
            if article.get('user_id', '').lower() == user_id.lower():
                # Delete the actual file
                file_path = os.path.join(ARTICLES_DIR, article['filename'])
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Error deleting file {file_path}: {e}")
            else:
                remaining_articles.append(article)
        
        # Save updated metadata
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(remaining_articles, f, indent=2)
        except Exception as e:
            print(f"Error updating metadata: {e}")
            
    except Exception as e:
        print(f"Error deleting user articles: {e}")

def delete_article(filename):
    """Delete a specific article with improved error handling"""
    if not filename:
        raise ValueError("Filename is required")
    
    # Validate filename to prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename")
    
    metadata_file = os.path.join(ARTICLES_DIR, 'articles_metadata.json')
    file_path = os.path.join(ARTICLES_DIR, filename)
    
    # Delete the file
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            raise Exception(f"Error deleting file: {e}")
    
    # Remove from metadata
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            
            articles = [a for a in articles if a.get('filename') != filename]
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2)
                
        except json.JSONDecodeError:
            print("Warning: Metadata file was corrupted, recreated as empty")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
        except Exception as e:
            print(f"Error updating metadata: {e}")

# Admin Logging Functions
def log_admin_action(admin_user_id, action, target_user_id=None, details=None):
    """Log admin actions with error handling"""
    if not admin_user_id or not action:
        return
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_logs (admin_user_id, action, target_user_id, details)
                VALUES (?, ?, ?, ?)
            ''', (admin_user_id, action, target_user_id, details))
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        print(f"Error logging admin action: {e}")

def log_security_event(user_id, action, ip_address=None, user_agent=None, success=True):
    """Log security events with error handling"""
    if not action:
        return
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO security_logs (user_id, action, ip_address, user_agent, success)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, action, ip_address, user_agent, success))
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        print(f"Error logging security event: {e}")

def get_admin_logs(limit=100):
    """Get admin logs with error handling"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0], 'admin_user_id': row[1], 'action': row[2],
                    'target_user_id': row[3], 'details': row[4], 'timestamp': row[5]
                })
            return logs
    except sqlite3.Error as e:
        print(f"Error getting admin logs: {e}")
        return []

def get_security_logs(limit=100):
    """Get security logs with error handling"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM security_logs ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0], 'user_id': row[1], 'action': row[2],
                    'ip_address': row[3], 'user_agent': row[4], 'success': row[5],
                    'timestamp': row[6]
                })
            return logs
    except sqlite3.Error as e:
        print(f"Error getting security logs: {e}")
        return []

# Database Backup and Export Functions
def backup_database():
    """Create database backup with better error handling"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'users_backup_{timestamp}.db')
    
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy2(DB_PATH, backup_file)
        return True, f"Database backed up to {backup_file}"
    except FileNotFoundError:
        return False, "Database file not found"
    except PermissionError:
        return False, "Permission denied creating backup"
    except Exception as e:
        return False, f"Backup failed: {str(e)}"

def export_users_to_csv():
    """Export users to CSV with better error handling"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = os.path.join(BACKUP_DIR, f'users_export_{timestamp}.csv')
    
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        users = get_all_users()
        
        if not users:
            return False, "No users found to export"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'user_id', 'full_name', 'email', 'login_attempts', 
                         'last_login', 'created_at', 'is_active', 'role']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for user in users:
                # Remove password_hash for security
                user_data = {k: v for k, v in user.items() if k != 'password_hash'}
                writer.writerow(user_data)
                
        return True, csv_file
    except PermissionError:
        return False, "Permission denied creating export file"
    except Exception as e:
        return False, f"Export failed: {str(e)}"

def generate_system_report():
    """Generate comprehensive system report with better error handling"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(BACKUP_DIR, f'system_report_{timestamp}.json')
    
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        users = get_all_users()
        admin_logs = get_admin_logs(50)
        security_logs = get_security_logs(50)
        
        # Get article statistics
        metadata_file = os.path.join(ARTICLES_DIR, 'articles_metadata.json')
        articles = []
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    articles = json.loads(content) if content else []
            except json.JSONDecodeError:
                articles = []
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': {
                'total_users': len(users),
                'active_users': len([u for u in users if u.get('is_active', True)]),
                'locked_users': len([u for u in users if u.get('login_attempts', 0) >= 5]),
                'total_articles': len(articles),
                'articles_by_user': {}
            },
            'users_summary': [
                {k: v for k, v in user.items() if k != 'password_hash'} 
                for user in users
            ],
            'recent_admin_actions': admin_logs,
            'recent_security_events': security_logs,
            'article_statistics': {}
        }
        
        # Calculate articles by user
        for article in articles:
            user_id = article.get('user_id', 'unknown')
            if user_id not in report['statistics']['articles_by_user']:
                report['statistics']['articles_by_user'][user_id] = 0
            report['statistics']['articles_by_user'][user_id] += 1
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
            
        return True, report_file
    except PermissionError:
        return False, "Permission denied creating report file"
    except Exception as e:
        return False, f"Report generation failed: {str(e)}"

def reset_all_passwords(admin_user_id, new_password="temp123"):
    """Reset all user passwords except admin with validation"""
    if not admin_user_id:
        return False, "Admin user ID is required"
    
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(new_password)
            cursor.execute('''
                UPDATE users SET password_hash = ?, login_attempts = 0 
                WHERE user_id != 'admin'
            ''', (password_hash,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
        
        # Log the action
        log_admin_action(admin_user_id, "RESET_ALL_PASSWORDS", 
                        details=f"Reset {affected_rows} user passwords")
        
        return True, f"Reset passwords for {affected_rows} users. New password: {new_password}"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    except Exception as e:
        return False, f"Password reset failed: {str(e)}"

def deactivate_user(user_id):
    """Deactivate user account with validation"""
    if not user_id:
        raise ValueError("User ID is required")
    
    if user_id.lower() == 'admin':
        raise ValueError("Cannot deactivate admin user")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id.lower(),))
            
            if cursor.rowcount == 0:
                raise ValueError("User not found")
                
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def activate_user(user_id):
    """Activate user account with validation"""
    if not user_id:
        raise ValueError("User ID is required")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = 1 WHERE user_id = ?', (user_id.lower(),))
            
            if cursor.rowcount == 0:
                raise ValueError("User not found")
                
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def cleanup_old_logs(days=30):
    """Clean up old logs with parameterized queries (Fixed SQL injection)"""
    if days < 1:
        raise ValueError("Days must be positive")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Fixed: Use parameterized queries instead of string formatting
            cursor.execute('''
                DELETE FROM admin_logs 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            admin_deleted = cursor.rowcount
            
            cursor.execute('''
                DELETE FROM security_logs 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            security_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return True, f"Cleaned up {admin_deleted} admin logs and {security_deleted} security logs"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    except Exception as e:
        return False, f"Cleanup failed: {e}"

# TEST MANAGEMENT FUNCTIONS

def create_test(title, description, time_limit, created_by):
    """Create a new test"""
    if not title or not time_limit or not created_by:
        raise ValueError("Title, time limit, and creator are required")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tests (title, description, time_limit, created_by)
                VALUES (?, ?, ?, ?)
            ''', (title, description, time_limit, created_by))
            test_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return test_id
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def add_question_to_test(test_id, question_text, question_order, marks=0):
    """Add a question to a test"""
    if not test_id or not question_text:
        raise ValueError("Test ID and question text are required")
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO questions (test_id, question_text, question_order, marks)
                VALUES (?, ?, ?, ?)
            ''', (test_id, question_text, question_order, marks))
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def get_all_tests():
    """Get all tests"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.time_limit, t.created_by, t.created_at, t.is_active,
                       COUNT(q.id) as question_count
                FROM tests t
                LEFT JOIN questions q ON t.id = q.test_id
                GROUP BY t.id
                ORDER BY t.created_at DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            tests = []
            for row in rows:
                tests.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'time_limit': row[3],
                    'created_by': row[4],
                    'created_at': row[5],
                    'is_active': row[6],
                    'question_count': row[7]
                })
            return tests
    except sqlite3.Error as e:
        print(f"Database error in get_all_tests: {e}")
        return []

def get_test_by_id(test_id):
    """Get test by ID with questions"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get test details
            cursor.execute('''
                SELECT id, title, description, time_limit, created_by, created_at, is_active
                FROM tests WHERE id = ?
            ''', (test_id,))
            test_row = cursor.fetchone()
            
            if not test_row:
                return None
            
            # Get questions for this test
            cursor.execute('''
                SELECT id, question_text, question_order, marks
                FROM questions WHERE test_id = ? ORDER BY question_order
            ''', (test_id,))
            question_rows = cursor.fetchall()
            
            conn.close()
            
            test = {
                'id': test_row[0],
                'title': test_row[1],
                'description': test_row[2],
                'time_limit': test_row[3],
                'created_by': test_row[4],
                'created_at': test_row[5],
                'is_active': test_row[6],
                'questions': []
            }
            
            for q_row in question_rows:
                test['questions'].append({
                    'id': q_row[0],
                    'question_text': q_row[1],
                    'question_order': q_row[2],
                    'marks': q_row[3]
                })
            
            return test
    except sqlite3.Error as e:
        print(f"Database error in get_test_by_id: {e}")
        return None

def get_active_tests():
    """Get only active tests for users"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.time_limit, t.created_by, t.created_at,
                       COUNT(q.id) as question_count
                FROM tests t
                LEFT JOIN questions q ON t.id = q.test_id
                WHERE t.is_active = 1
                GROUP BY t.id
                ORDER BY t.created_at DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            tests = []
            for row in rows:
                tests.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'time_limit': row[3],
                    'created_by': row[4],
                    'created_at': row[5],
                    'question_count': row[6]
                })
            return tests
    except sqlite3.Error as e:
        print(f"Database error in get_active_tests: {e}")
        return []

def delete_test(test_id):
    """Delete a test and all associated data"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count > 0
    except sqlite3.Error as e:
        print(f"Database error in delete_test: {e}")
        return False

def toggle_test_status(test_id):
    """Toggle test active/inactive status"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tests SET is_active = NOT is_active WHERE id = ?
            ''', (test_id,))
            updated_count = cursor.rowcount
            conn.commit()
            conn.close()
            return updated_count > 0
    except sqlite3.Error as e:
        print(f"Database error in toggle_test_status: {e}")
        return False

def delete_question(question_id):
    """Delete a specific question"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count > 0
    except sqlite3.Error as e:
        print(f"Database error in delete_question: {e}")
        return False

def update_question(question_id, question_text, marks=0):
    """Update a question"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE questions SET question_text = ?, marks = ? WHERE id = ?
            ''', (question_text, marks, question_id))
            updated_count = cursor.rowcount
            conn.commit()
            conn.close()
            return updated_count > 0
    except sqlite3.Error as e:
        print(f"Database error in update_question: {e}")
        return False

def start_test_attempt(test_id, user_id):
    """Start a new test attempt for a user"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO test_attempts (test_id, user_id, status)
                VALUES (?, ?, 'in_progress')
            ''', (test_id, user_id))
            attempt_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return attempt_id
    except sqlite3.Error as e:
        print(f"Database error in start_test_attempt: {e}")
        return None

def complete_test_attempt(attempt_id, time_taken):
    """Complete a test attempt"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE test_attempts 
                SET completed_at = CURRENT_TIMESTAMP, time_taken = ?, status = 'completed'
                WHERE id = ?
            ''', (time_taken, attempt_id))
            conn.commit()
            conn.close()
            return True
    except sqlite3.Error as e:
        print(f"Database error in complete_test_attempt: {e}")
        return False

def save_test_answer(attempt_id, question_id, answer_text, word_count=0):
    """Save or update an answer for a test question"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if answer already exists
            cursor.execute('''
                SELECT id FROM test_answers WHERE attempt_id = ? AND question_id = ?
            ''', (attempt_id, question_id))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing answer
                cursor.execute('''
                    UPDATE test_answers SET answer_text = ?, word_count = ?
                    WHERE attempt_id = ? AND question_id = ?
                ''', (answer_text, word_count, attempt_id, question_id))
            else:
                # Insert new answer
                cursor.execute('''
                    INSERT INTO test_answers (attempt_id, question_id, answer_text, word_count)
                    VALUES (?, ?, ?, ?)
                ''', (attempt_id, question_id, answer_text, word_count))
            
            conn.commit()
            conn.close()
            return True
    except sqlite3.Error as e:
        print(f"Database error in save_test_answer: {e}")
        return False

def get_user_test_attempts(user_id, test_id=None):
    """Get test attempts for a user"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if test_id:
                cursor.execute('''
                    SELECT ta.id, ta.test_id, ta.started_at, ta.completed_at, ta.time_taken, ta.status,
                           t.title, t.time_limit
                    FROM test_attempts ta
                    JOIN tests t ON ta.test_id = t.id
                    WHERE ta.user_id = ? AND ta.test_id = ?
                    ORDER BY ta.started_at DESC
                ''', (user_id, test_id))
            else:
                cursor.execute('''
                    SELECT ta.id, ta.test_id, ta.started_at, ta.completed_at, ta.time_taken, ta.status,
                           t.title, t.time_limit
                    FROM test_attempts ta
                    JOIN tests t ON ta.test_id = t.id
                    WHERE ta.user_id = ?
                    ORDER BY ta.started_at DESC
                ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            attempts = []
            for row in rows:
                attempts.append({
                    'id': row[0],
                    'test_id': row[1],
                    'started_at': row[2],
                    'completed_at': row[3],
                    'time_taken': row[4],
                    'status': row[5],
                    'test_title': row[6],
                    'test_time_limit': row[7]
                })
            return attempts
    except sqlite3.Error as e:
        print(f"Database error in get_user_test_attempts: {e}")
        return []

def get_test_attempt_answers(attempt_id):
    """Get all answers for a test attempt"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ta.question_id, ta.answer_text, ta.word_count, q.question_text, q.marks
                FROM test_answers ta
                JOIN questions q ON ta.question_id = q.id
                WHERE ta.attempt_id = ?
                ORDER BY q.question_order
            ''', (attempt_id,))
            rows = cursor.fetchall()
            conn.close()
            
            answers = []
            for row in rows:
                answers.append({
                    'question_id': row[0],
                    'answer_text': row[1],
                    'word_count': row[2],
                    'question_text': row[3],
                    'marks': row[4]
                })
            return answers
    except sqlite3.Error as e:
        print(f"Database error in get_test_attempt_answers: {e}")
        return []