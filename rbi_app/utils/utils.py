import os
import re
import json
import threading
from datetime import datetime
from pathlib import Path

# Fixed: Use absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ARTICLES_DIR = os.path.join(BASE_DIR, '..', 'articles')
METADATA_FILE = os.path.join(ARTICLES_DIR, 'articles_metadata.json')

# Fixed: Thread lock for file operations
file_lock = threading.Lock()

def validate_password(password):
    """Enhanced password validation"""
    if not password:
        return False, "Password is required."
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    # Additional validation can be added here
    if len(password) > 128:
        return False, "Password is too long."
    
    return True, ""

def sanitize_filename(name):
    """Enhanced filename sanitization"""
    if not name:
        return "untitled"
    
    # Remove dangerous characters and limit length
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\s]', '_', name)
    sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
    sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
    
    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    return sanitized if sanitized else "untitled"

def save_article_to_file(data, user_id, full_name):
    """Save article with improved error handling and file locking"""
    if not data or not user_id or not full_name:
        return {'success': False, 'error': 'Missing required data'}
    
    content = data.get('content', '').strip()
    if not content:
        return {'success': False, 'error': 'Content cannot be empty'}
    
    try:
        os.makedirs(ARTICLES_DIR, exist_ok=True)
        
        title = sanitize_filename(data.get('title', 'Untitled'))
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d_%H-%M-%S')
        date_display = now.strftime('%d/%m/%Y %H:%M:%S')
        
        # Ensure user_id is lowercase for consistency
        user_id = user_id.lower()
        filename = f'{user_id}_{title}_{date_str}.txt'
        filepath = os.path.join(ARTICLES_DIR, filename)

        # Validate data types and provide defaults
        time_spent = data.get('timeSpent', '0:00')
        word_count = data.get('wordCount', 0)
        typing_speed = data.get('typingSpeed', 0)
        
        # Validate numeric values
        try:
            word_count = int(word_count) if word_count else 0
            typing_speed = int(typing_speed) if typing_speed else 0
        except (ValueError, TypeError):
            word_count = 0
            typing_speed = 0

        # Format content in specified order
        formatted_content = f"""Student ID: {user_id}
Student Name: {full_name}
Date: {date_display}
Time Spent: {time_spent}
Word Count: {word_count}
Typing Speed: {typing_speed} WPM
Title: {data.get('title', 'Untitled')}

Content:
{content}

---
End of Article
"""

        # Save content to text file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
        except IOError as e:
            return {'success': False, 'error': f'Failed to save file: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error saving file: {str(e)}'}

        # Save metadata with file locking for concurrent access
        preview = content[:100] + '...' if len(content) > 100 else content
        metadata = {
            'filename': filename,
            'user_id': user_id,
            'full_name': full_name,
            'title': data.get('title', 'Untitled'),
            'date': date_display,
            'time_spent': time_spent,
            'word_count': word_count,
            'typing_speed': typing_speed,
            'content_preview': preview
        }

        try:
            with file_lock:
                # Load existing metadata
                existing = []
                if os.path.exists(METADATA_FILE):
                    try:
                        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                            content_str = f.read().strip()
                            existing = json.loads(content_str) if content_str else []
                    except json.JSONDecodeError:
                        print("Warning: Metadata file was corrupted, creating new one")
                        existing = []
                    except Exception as e:
                        print(f"Error reading metadata file: {e}")
                        existing = []

                existing.append(metadata)
                
                # Save updated metadata
                with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            # If metadata save fails, at least the article file exists
            print(f"Warning: Failed to save metadata: {e}")
            return {'success': True, 'message': 'Article saved but metadata update failed', 'filename': filename}

        return {'success': True, 'message': 'Article saved successfully.', 'filename': filename}
        
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}

def get_articles_for_user(user_id):
    """Get articles for user with improved error handling"""
    if not user_id:
        return []
    
    try:
        if not os.path.exists(METADATA_FILE):
            return []
            
        with file_lock:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                content_str = f.read().strip()
                if not content_str:
                    return []
                    
                try:
                    articles = json.loads(content_str)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error in metadata file: {e}")
                    return []
        
        # Validate articles structure
        valid_articles = []
        for article in articles:
            if isinstance(article, dict) and 'user_id' in article:
                # If admin, return all articles; otherwise filter by user_id
                if user_id.lower() == 'admin' or article['user_id'].lower() == user_id.lower():
                    valid_articles.append(article)
        
        return valid_articles
        
    except FileNotFoundError:
        return []
    except PermissionError:
        print("Permission denied reading articles metadata")
        return []
    except Exception as e:
        print(f"Unexpected error loading articles: {e}")
        return []

def read_article_content(filename, user_id):
    """Read article content with enhanced security and error handling"""
    if not filename or not user_id:
        return {'success': False, 'error': 'Filename and user ID are required'}
    
    # Enhanced security: validate filename
    if '..' in filename or '/' in filename or '\\' in filename:
        return {'success': False, 'error': 'Invalid filename'}
    
    # Ensure filename has safe extension
    if not filename.endswith('.txt'):
        return {'success': False, 'error': 'Invalid file type'}
    
    filepath = os.path.join(ARTICLES_DIR, filename)
    
    if not os.path.exists(filepath):
        return {'success': False, 'error': 'File not found'}
    
    # Enhanced security check: only allow user to read their own files (or admin can read all)
    user_id = user_id.lower()
    if user_id != 'admin':
        if not filename.lower().startswith(user_id + '_'):
            return {'success': False, 'error': 'Access denied'}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate file size (prevent reading extremely large files)
        if len(content) > 1024 * 1024:  # 1MB limit
            return {'success': False, 'error': 'File too large'}
            
        return {'success': True, 'content': content}
        
    except FileNotFoundError:
        return {'success': False, 'error': 'File not found'}
    except PermissionError:
        return {'success': False, 'error': 'Permission denied'}
    except UnicodeDecodeError:
        return {'success': False, 'error': 'File encoding error'}
    except Exception as e:
        return {'success': False, 'error': f'Error reading file: {str(e)}'}

def validate_article_data(data):
    """Validate article data before saving"""
    if not isinstance(data, dict):
        return False, "Invalid data format"
    
    required_fields = ['content']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    content = data.get('content', '').strip()
    if not content:
        return False, "Content cannot be empty"
    
    if len(content) > 50000:  # 50KB limit
        return False, "Content too long"
    
    # Validate title if provided
    title = data.get('title', '')
    if title and len(title) > 200:
        return False, "Title too long"
    
    return True, ""

def cleanup_old_articles(days=365):
    """Clean up old article files (optional maintenance function)"""
    if days < 30:  # Safety: don't delete articles newer than 30 days
        return False, "Minimum retention period is 30 days"
    
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted_count = 0
        
        # Clean up files
        if os.path.exists(ARTICLES_DIR):
            for filename in os.listdir(ARTICLES_DIR):
                if filename.endswith('.txt'):
                    filepath = os.path.join(ARTICLES_DIR, filename)
                    try:
                        file_stat = os.path.stat(filepath)
                        file_date = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if file_date < cutoff_date:
                            os.remove(filepath)
                            deleted_count += 1
                    except Exception as e:
                        print(f"Error processing file {filename}: {e}")
        
        # Clean up metadata
        if os.path.exists(METADATA_FILE):
            try:
                with file_lock:
                    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                        articles = json.load(f)
                    
                    # Keep only recent articles
                    recent_articles = []
                    for article in articles:
                        try:
                            article_date = datetime.strptime(article['date'], '%d/%m/%Y %H:%M:%S')
                            if article_date >= cutoff_date:
                                recent_articles.append(article)
                        except (KeyError, ValueError):
                            # Keep articles with invalid dates
                            recent_articles.append(article)
                    
                    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                        json.dump(recent_articles, f, indent=2, ensure_ascii=False)
                        
            except Exception as e:
                print(f"Error cleaning metadata: {e}")
        
        return True, f"Deleted {deleted_count} old article files"
        
    except Exception as e:
        return False, f"Cleanup failed: {str(e)}"

def get_article_statistics():
    """Get statistics about articles"""
    try:
        articles = get_articles_for_user('admin')  # Get all articles
        
        if not articles:
            return {
                'total_articles': 0,
                'total_words': 0,
                'average_words': 0,
                'total_users': 0
            }
        
        total_words = sum(article.get('word_count', 0) for article in articles)
        users = set(article.get('user_id', '') for article in articles)
        
        return {
            'total_articles': len(articles),
            'total_words': total_words,
            'average_words': total_words // len(articles) if articles else 0,
            'total_users': len(users)
        }
        
    except Exception as e:
        print(f"Error getting article statistics: {e}")
        return {
            'total_articles': 0,
            'total_words': 0,
            'average_words': 0,
            'total_users': 0
        }

def repair_metadata_file():
    """Repair corrupted metadata file by scanning article files"""
    try:
        print("Attempting to repair metadata file...")
        
        if not os.path.exists(ARTICLES_DIR):
            return False, "Articles directory not found"
        
        repaired_metadata = []
        
        # Scan all .txt files in articles directory
        for filename in os.listdir(ARTICLES_DIR):
            if filename.endswith('.txt'):
                filepath = os.path.join(ARTICLES_DIR, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract metadata from file content
                    lines = content.split('\n')
                    metadata = {'filename': filename}
                    
                    for line in lines[:10]:  # Check first 10 lines
                        if line.startswith('Student ID: '):
                            metadata['user_id'] = line.replace('Student ID: ', '').strip()
                        elif line.startswith('Student Name: '):
                            metadata['full_name'] = line.replace('Student Name: ', '').strip()
                        elif line.startswith('Date: '):
                            metadata['date'] = line.replace('Date: ', '').strip()
                        elif line.startswith('Time Spent: '):
                            metadata['time_spent'] = line.replace('Time Spent: ', '').strip()
                        elif line.startswith('Word Count: '):
                            try:
                                metadata['word_count'] = int(line.replace('Word Count: ', '').strip())
                            except ValueError:
                                metadata['word_count'] = 0
                        elif line.startswith('Typing Speed: '):
                            try:
                                speed_str = line.replace('Typing Speed: ', '').replace(' WPM', '').strip()
                                metadata['typing_speed'] = int(speed_str)
                            except ValueError:
                                metadata['typing_speed'] = 0
                        elif line.startswith('Title: '):
                            metadata['title'] = line.replace('Title: ', '').strip()
                    
                    # Generate preview
                    content_start = content.find('Content:\n')
                    if content_start != -1:
                        article_content = content[content_start + 9:].strip()
                        if article_content.endswith('\n---\nEnd of Article'):
                            article_content = article_content[:-19].strip()
                        
                        preview = article_content[:100] + '...' if len(article_content) > 100 else article_content
                        metadata['content_preview'] = preview
                    
                    # Set defaults for missing fields
                    metadata.setdefault('user_id', 'unknown')
                    metadata.setdefault('full_name', 'Unknown User')
                    metadata.setdefault('title', 'Untitled')
                    metadata.setdefault('date', 'Unknown')
                    metadata.setdefault('time_spent', '0:00')
                    metadata.setdefault('word_count', 0)
                    metadata.setdefault('typing_speed', 0)
                    metadata.setdefault('content_preview', '')
                    
                    repaired_metadata.append(metadata)
                    
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
        
        # Save repaired metadata
        with file_lock:
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(repaired_metadata, f, indent=2, ensure_ascii=False)
        
        return True, f"Repaired metadata for {len(repaired_metadata)} articles"
        
    except Exception as e:
        return False, f"Repair failed: {str(e)}"