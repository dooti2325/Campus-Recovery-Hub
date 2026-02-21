from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import sqlite3
import os
import qrcode
from io import BytesIO, StringIO
import csv
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security Configuration
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-this-in-production')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
QR_CODE_FOLDER = 'static/qr_codes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@campusrecoveryhub.com')

# Initialize extensions
csrf = CSRFProtect(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_CODE_FOLDER, exist_ok=True)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, is_admin=0):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin == 1

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, is_admin FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()

    if result:
        return User(result[0], result[1], result[2], result[3])
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Enhanced database setup with user authentication, indexing, and improved schema
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Enable foreign keys
    c.execute('PRAGMA foreign_keys = ON')

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL,
                 profile_picture TEXT,
                 bio TEXT,
                 reputation_score INTEGER DEFAULT 0,
                 is_admin INTEGER DEFAULT 0,
                 is_banned INTEGER DEFAULT 0,
                 ban_reason TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')

    # Items table with user tracking
    c.execute('''CREATE TABLE IF NOT EXISTS items (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 item_type TEXT NOT NULL,
                 title TEXT NOT NULL,
                 description TEXT,
                 date TEXT,
                 location TEXT,
                 status TEXT DEFAULT 'Unclaimed',
                 contact TEXT,
                 image_path TEXT,
                 qr_code_path TEXT,
                 is_verified INTEGER DEFAULT 0,
                 flagged INTEGER DEFAULT 0,
                 flagged_reason TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 category TEXT,
                 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                 )''')

    # Notifications table
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 item_id INTEGER NOT NULL,
                 notification_type TEXT,
                 message TEXT,
                 is_read BOOLEAN DEFAULT 0,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                 FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
                 )''')

    # Activity logs table
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 action TEXT NOT NULL,
                 description TEXT,
                 ip_address TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                 )''')

    # System settings table
    c.execute('''CREATE TABLE IF NOT EXISTS system_settings (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 setting_key TEXT UNIQUE NOT NULL,
                 setting_value TEXT,
                 setting_type TEXT,
                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')

    # User preferences table
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
                 user_id INTEGER PRIMARY KEY,
                 email_notifications INTEGER DEFAULT 1,
                 sms_notifications INTEGER DEFAULT 0,
                 theme TEXT DEFAULT 'system',
                 items_per_page INTEGER DEFAULT 12,
                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                 )''')

    # Create indexes for better performance
    c.execute('''CREATE INDEX IF NOT EXISTS idx_items_user_id ON items(user_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_items_status ON items(status)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_items_verified ON items(is_verified)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_items_flagged ON items(flagged)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned)''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

init_db()

# Helper function to handle file uploads (refactored from duplicate code)
def handle_file_upload(file):
    """Handle file upload and return the image path."""
    image_path = None
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(file_path)
            image_path = f'uploads/{filename}'
            logger.info(f"File uploaded successfully: {filename}")
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            flash('Error uploading file. Please try again.', 'error')
    return image_path

# Helper function to save item (refactored from duplicate code)
def save_item(item_type, title, description, date, location, contact, category, image_path, user_id):
    """Save item to database and return item ID."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""INSERT INTO items
                     (user_id, item_type, title, description, date, location, status, contact, image_path, category)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (user_id, item_type, title, description, date, location, 'Unclaimed', contact, image_path, category))
        conn.commit()
        item_id = c.lastrowid
        conn.close()
        logger.info(f"Item {item_id} saved to database by user {user_id}")
        return item_id
    except Exception as e:
        logger.error(f"Error saving item: {str(e)}")
        flash('Error saving item. Please try again.', 'error')
        return None

# Helper function to generate QR code
def generate_qr_code(item_id):
    """Generate QR code for item and return the path."""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"{request.host_url}items/{item_id}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        filename = f"qr_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = os.path.join(app.config['QR_CODE_FOLDER'], filename)
        img.save(file_path)

        qr_code_path = f'qr_codes/{filename}'
        logger.info(f"QR code generated for item {item_id}")
        return qr_code_path
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None

# Helper function to send email notification
def send_email_notification(recipient_email, subject, template_path, **kwargs):
    """Send email notification to user."""
    try:
        if not app.config['MAIL_USERNAME']:
            logger.warning("Email configuration not set. Skipping email notification.")
            return False

        msg = Message(subject=subject, recipients=[recipient_email])
        msg.html = render_template(template_path, **kwargs)
        mail.send(msg)
        logger.info(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

# Helper function for paginated queries
def get_paginated_items(page=1, per_page=12, item_type='', category='', search=''):
    """Get paginated items with filters."""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Build query
    query = "SELECT * FROM items WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM items WHERE 1=1"
    params = []

    if item_type:
        query += " AND item_type = ?"
        count_query += " AND item_type = ?"
        params.append(item_type)

    if category:
        query += " AND category = ?"
        count_query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        count_query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    # Get total count
    c.execute(count_query, params)
    total_items = c.fetchone()[0]
    total_pages = (total_items + per_page - 1) // per_page

    # Get paginated results
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    c.execute(query, params)
    items = c.fetchall()

    conn.close()

    return items, total_items, total_pages

# Helper function to check if user is admin
def is_admin(user_id):
    """Check if user has admin privileges."""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

# Helper function to log activity
def log_activity(user_id, action, description, ip_address=None):
    """Log user activity."""
    try:
        if ip_address is None:
            ip_address = request.remote_addr

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""INSERT INTO activity_logs (user_id, action, description, ip_address)
                     VALUES (?, ?, ?, ?)""",
                  (user_id, action, description, ip_address))
        conn.commit()
        conn.close()
        logger.info(f"Activity logged: {action} by user {user_id}")
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")

def admin_users_redirect():
    """Redirect back to user management while preventing external redirects."""
    next_url = request.form.get('next_url') or request.args.get('next_url')
    if next_url and (next_url.startswith('/admin/users') or next_url.startswith('/admin/user-management')):
        return redirect(next_url)
    return redirect(url_for('admin_users'))

# Helper function to get system settings
def get_setting(key, default=None):
    """Get system setting by key."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT setting_value FROM system_settings WHERE setting_key = ?", (key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else default
    except Exception as e:
        logger.error(f"Error getting setting: {str(e)}")
        return default

# Helper function to set system settings
def set_setting(key, value, setting_type='string'):
    """Set system setting."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO system_settings (setting_key, setting_value, setting_type)
                     VALUES (?, ?, ?)""",
                  (key, value, setting_type))
        conn.commit()
        conn.close()
        logger.info(f"Setting updated: {key}")
        return True
    except Exception as e:
        logger.error(f"Error setting value: {str(e)}")
        return False

def get_user_preferences(user_id):
    """Get user preferences with defaults."""
    default_preferences = {
        'email_notifications': 1,
        'sms_notifications': 0,
        'theme': 'system',
        'items_per_page': 12
    }
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""SELECT email_notifications, sms_notifications, theme, items_per_page
                     FROM user_preferences WHERE user_id = ?""", (user_id,))
        result = c.fetchone()
        conn.close()
        if not result:
            return default_preferences
        return {
            'email_notifications': result[0],
            'sms_notifications': result[1],
            'theme': result[2],
            'items_per_page': result[3]
        }
    except Exception as e:
        logger.error(f"Error loading user preferences: {str(e)}")
        return default_preferences

def save_user_preferences(user_id, email_notifications, sms_notifications, theme, items_per_page):
    """Create or update user preferences."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""INSERT INTO user_preferences
                     (user_id, email_notifications, sms_notifications, theme, items_per_page, updated_at)
                     VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                     ON CONFLICT(user_id) DO UPDATE SET
                         email_notifications = excluded.email_notifications,
                         sms_notifications = excluded.sms_notifications,
                         theme = excluded.theme,
                         items_per_page = excluded.items_per_page,
                         updated_at = CURRENT_TIMESTAMP""",
                  (user_id, email_notifications, sms_notifications, theme, items_per_page))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving user preferences: {str(e)}")
        return False

def build_admin_logs_filters(action_filter, user_query):
    """Build SQL filter clauses for activity logs reports."""
    where_clauses = []
    params = []
    if action_filter:
        where_clauses.append("activity_logs.action = ?")
        params.append(action_filter)
    if user_query:
        where_clauses.append("COALESCE(users.username, 'System') LIKE ?")
        params.append(f"%{user_query}%")
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    return where_sql, params

# Routes

@app.route('/')
def index():
    """Homepage with statistics and recent items preview."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get recent items for preview (limit 6)
        c.execute("""SELECT i.*, u.username FROM items i
                     JOIN users u ON i.user_id = u.id
                     ORDER BY i.created_at DESC LIMIT 6""")
        recent_items = c.fetchall()

        # Get statistics
        c.execute("SELECT COUNT(*) FROM items WHERE item_type = 'Lost' AND status = 'Unclaimed'")
        lost_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM items WHERE item_type = 'Found' AND status = 'Unclaimed'")
        found_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM items WHERE status = 'Claimed'")
        claimed_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]

        conn.close()

        stats = {
            'lost': lost_count,
            'found': found_count,
            'claimed': claimed_count,
            'users': user_count
        }

        return render_template('index.html', recent_items=recent_items, stats=stats)
    except Exception as e:
        logger.error(f"Error loading homepage: {str(e)}")
        flash('Error loading homepage.', 'error')
        return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()

            # Check if user exists
            c.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if c.fetchone():
                flash('Username or email already exists.', 'error')
                conn.close()
                return redirect(url_for('register'))

            # Create new user
            password_hash = generate_password_hash(password)
            c.execute("""INSERT INTO users (username, email, password_hash)
                         VALUES (?, ?, ?)""",
                      (username, email, password_hash))
            conn.commit()
            user_id = c.lastrowid
            conn.close()

            logger.info(f"New user registered: {username}")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('login'))

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("""SELECT id, username, email, password_hash, is_admin
                         FROM users WHERE username = ?""", (username,))
            result = c.fetchone()
            conn.close()

            if result and check_password_hash(result[3], password):
                user = User(result[0], result[1], result[2], result[4])
                login_user(user, remember=request.form.get('remember'))
                logger.info(f"User logged in: {username}")
                flash(f'Welcome back, {username}!', 'success')
                return redirect(request.args.get('next') or url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
                return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get user info
        c.execute("""SELECT username, email, bio, reputation_score, created_at, profile_picture
                     FROM users WHERE id = ?""", (current_user.id,))
        user_info = c.fetchone()

        # Get user's items
        c.execute("""SELECT id, item_type, title, status, created_at FROM items
                     WHERE user_id = ?
                     ORDER BY created_at DESC""", (current_user.id,))
        user_items = c.fetchall()

        # Get user's notifications
        c.execute("""SELECT id, message, is_read, created_at FROM notifications
                     WHERE user_id = ?
                     ORDER BY created_at DESC LIMIT 10""", (current_user.id,))
        notifications = c.fetchall()

        conn.close()

        return render_template('profile.html', user_info=user_info, user_items=user_items,
                             notifications=notifications)
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        flash('Error loading profile.', 'error')
        return redirect(url_for('index'))

@app.route('/report_lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    """Report a lost item."""
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            date = request.form.get('date', '')
            location = request.form.get('location', '').strip()
            contact = request.form.get('contact', '').strip()
            category = request.form.get('category', '')

            # Validation
            if not all([title, location, contact]):
                flash('Title, location, and contact are required.', 'error')
                return redirect(url_for('report_lost'))

            # Handle file upload
            image_path = None
            if 'image' in request.files:
                image_path = handle_file_upload(request.files['image'])

            # Save item
            item_id = save_item('Lost', title, description, date, location, contact,
                               category, image_path, current_user.id)

            if item_id:
                # Generate QR code
                qr_code_path = generate_qr_code(item_id)
                if qr_code_path:
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute("UPDATE items SET qr_code_path = ? WHERE id = ?",
                             (qr_code_path, item_id))
                    conn.commit()
                    conn.close()

                flash('Lost item reported successfully!', 'success')
                return redirect(url_for('items'))
        except Exception as e:
            logger.error(f"Error reporting lost item: {str(e)}")
            flash('Error reporting item. Please try again.', 'error')

    return render_template('report_lost.html')

@app.route('/report_found', methods=['GET', 'POST'])
@login_required
def report_found():
    """Report a found item."""
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            date = request.form.get('date', '')
            location = request.form.get('location', '').strip()
            contact = request.form.get('contact', '').strip()
            category = request.form.get('category', '')

            # Validation
            if not all([title, location, contact]):
                flash('Title, location, and contact are required.', 'error')
                return redirect(url_for('report_found'))

            # Handle file upload
            image_path = None
            if 'image' in request.files:
                image_path = handle_file_upload(request.files['image'])

            # Save item
            item_id = save_item('Found', title, description, date, location, contact,
                               category, image_path, current_user.id)

            if item_id:
                # Generate QR code
                qr_code_path = generate_qr_code(item_id)
                if qr_code_path:
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute("UPDATE items SET qr_code_path = ? WHERE id = ?",
                             (qr_code_path, item_id))
                    conn.commit()
                    conn.close()

                flash('Found item reported successfully!', 'success')
                return redirect(url_for('items'))
        except Exception as e:
            logger.error(f"Error reporting found item: {str(e)}")
            flash('Error reporting item. Please try again.', 'error')

    return render_template('report_found.html')

@app.route('/items')
def items():
    """Browse items with pagination and filters."""
    try:
        page = request.args.get('page', 1, type=int)
        item_type = request.args.get('type', '')
        category = request.args.get('category', '')
        search = request.args.get('search', '')

        # Get paginated items
        items_list, total_items, total_pages = get_paginated_items(
            page=page, per_page=12, item_type=item_type,
            category=category, search=search
        )

        # Get unique categories
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT category FROM items WHERE category IS NOT NULL ORDER BY category")
        categories = [row[0] for row in c.fetchall()]

        # Enhance items with user info
        items_with_users = []
        for item in items_list:
            c.execute("SELECT username FROM users WHERE id = ?", (item[1],))
            user_result = c.fetchone()
            items_with_users.append((*item, user_result[0] if user_result else 'Unknown'))

        conn.close()

        return render_template('items.html', items=items_with_users, categories=categories,
                             current_type=item_type, current_category=category,
                             current_search=search, page=page, total_pages=total_pages,
                             total_items=total_items)
    except Exception as e:
        logger.error(f"Error loading items: {str(e)}")
        flash('Error loading items.', 'error')
        return redirect(url_for('index'))

@app.route('/items/<int:item_id>')
def item_detail(item_id):
    """View item details."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""SELECT i.*, u.username, u.email FROM items i
                     JOIN users u ON i.user_id = u.id
                     WHERE i.id = ?""", (item_id,))
        item = c.fetchone()
        conn.close()

        if not item:
            flash('Item not found.', 'error')
            return redirect(url_for('items'))

        return render_template('item_detail.html', item=item)
    except Exception as e:
        logger.error(f"Error loading item details: {str(e)}")
        flash('Error loading item details.', 'error')
        return redirect(url_for('items'))

@app.route('/claim_item/<int:item_id>', methods=['POST'])
@login_required
def claim_item(item_id):
    """Mark an item as claimed."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get item info
        c.execute("SELECT user_id, title FROM items WHERE id = ?", (item_id,))
        result = c.fetchone()

        if not result:
            flash('Item not found.', 'error')
            return redirect(url_for('items'))

        item_user_id, item_title = result

        # Update item status
        c.execute("UPDATE items SET status = 'Claimed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                 (item_id,))

        # Create notification for item reporter
        c.execute("""INSERT INTO notifications (user_id, item_id, notification_type, message)
                     VALUES (?, ?, ?, ?)""",
                 (item_user_id, item_id, 'claimed',
                  f"Great news! Someone has claimed your '{item_title}' item or found a match!"))

        conn.commit()
        conn.close()

        # Send email notification
        item_owner = load_user(item_user_id)
        if item_owner:
            send_email_notification(
                item_owner.email,
                'Item Claimed - Campus Recovery Hub',
                'email/item_claimed.html',
                item_title=item_title,
                claimer_username=current_user.username
            )

        logger.info(f"Item {item_id} claimed by user {current_user.id}")
        flash('Item marked as claimed!', 'success')
        return redirect(url_for('items'))
    except Exception as e:
        logger.error(f"Error claiming item: {str(e)}")
        flash('Error claiming item. Please try again.', 'error')
        return redirect(url_for('items'))

@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    """Delete an item (only by owner)."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Check if user owns the item
        c.execute("SELECT user_id, image_path, qr_code_path FROM items WHERE id = ?", (item_id,))
        result = c.fetchone()

        if not result:
            flash('Item not found.', 'error')
            return redirect(url_for('items'))

        user_id, image_path, qr_code_path = result

        if user_id != current_user.id:
            flash('You can only delete your own items.', 'error')
            return redirect(url_for('items'))

        # Delete associated files
        if image_path:
            file_path = os.path.join('static', image_path)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting image file: {str(e)}")

        if qr_code_path:
            file_path = os.path.join('static', qr_code_path)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting QR code file: {str(e)}")

        # Delete item from database
        c.execute("DELETE FROM items WHERE id = ?", (item_id,))

        # Delete associated notifications
        c.execute("DELETE FROM notifications WHERE item_id = ?", (item_id,))

        conn.commit()
        conn.close()

        logger.info(f"Item {item_id} deleted by user {current_user.id}")
        flash('Item deleted successfully!', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        flash('Error deleting item. Please try again.', 'error')
        return redirect(url_for('items'))

@app.route('/notifications')
@login_required
def notifications():
    """View user notifications."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get notifications
        c.execute("""SELECT id, message, is_read, created_at FROM notifications
                     WHERE user_id = ?
                     ORDER BY created_at DESC""", (current_user.id,))
        user_notifications = c.fetchall()

        # Mark all as read
        c.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                 (current_user.id,))
        conn.commit()
        conn.close()

        return render_template('notifications.html', notifications=user_notifications)
    except Exception as e:
        logger.error(f"Error loading notifications: {str(e)}")
        flash('Error loading notifications.', 'error')
        return redirect(url_for('index'))

# ==================== ADMIN DASHBOARD ====================

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard with statistics."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get statistics
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM items")
        total_items = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM items WHERE status = 'Unclaimed'")
        unclaimed_items = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM items WHERE flagged = 1")
        flagged_items = c.fetchone()[0]

        c.execute("""SELECT item_type, COUNT(*) as count FROM items GROUP BY item_type""")
        items_by_type = c.fetchall()

        c.execute("""SELECT category, COUNT(*) as count FROM items GROUP BY category""")
        items_by_category = c.fetchall()

        # Recent activity
        c.execute("""SELECT username, action, description, created_at FROM activity_logs
                     JOIN users ON activity_logs.user_id = users.id
                     ORDER BY activity_logs.created_at DESC
                     LIMIT 20""")
        recent_activity = c.fetchall()

        conn.close()

        log_activity(current_user.id, 'ADMIN_DASHBOARD_ACCESS', 'Accessed admin dashboard')

        return render_template('admin_dashboard.html',
                             total_users=total_users,
                             banned_users=banned_users,
                             total_items=total_items,
                             unclaimed_items=unclaimed_items,
                             flagged_items=flagged_items,
                             items_by_type=items_by_type,
                             items_by_category=items_by_category,
                             recent_activity=recent_activity)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading admin dashboard.', 'error')
        return redirect(url_for('index'))

# ==================== ANALYTICS & STATISTICS ====================

@app.route('/admin/statistics')
@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """View admin analytics and statistics."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        period = request.args.get('period', '30').strip()
        if period not in {'7', '30', '90', '365'}:
            period = '30'
        period_days = int(period)
        period_filter = f'-{period_days} days'

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("""SELECT COUNT(*) FROM users
                     WHERE datetime(created_at) >= datetime('now', ?)""", (period_filter,))
        new_users = c.fetchone()[0]

        c.execute("""SELECT COUNT(*) FROM items
                     WHERE datetime(created_at) >= datetime('now', ?)""", (period_filter,))
        new_items = c.fetchone()[0]

        c.execute("""SELECT COUNT(*) FROM items
                     WHERE item_type = 'Lost' AND datetime(created_at) >= datetime('now', ?)""", (period_filter,))
        lost_reports = c.fetchone()[0]

        c.execute("""SELECT COUNT(*) FROM items
                     WHERE item_type = 'Found' AND datetime(created_at) >= datetime('now', ?)""", (period_filter,))
        found_reports = c.fetchone()[0]

        c.execute("""SELECT COUNT(*) FROM items
                     WHERE status = 'Claimed' AND datetime(created_at) >= datetime('now', ?)""", (period_filter,))
        claimed_items = c.fetchone()[0]

        claim_rate = round((claimed_items / new_items) * 100, 1) if new_items else 0

        c.execute("""SELECT date(created_at) as day, COUNT(*) as count
                     FROM items
                     WHERE datetime(created_at) >= datetime('now', ?)
                     GROUP BY date(created_at)
                     ORDER BY day DESC
                     LIMIT 14""", (period_filter,))
        daily_item_activity = c.fetchall()

        c.execute("""SELECT COALESCE(category, 'Uncategorized') as category, COUNT(*) as count
                     FROM items
                     WHERE datetime(created_at) >= datetime('now', ?)
                     GROUP BY category
                     ORDER BY count DESC
                     LIMIT 10""", (period_filter,))
        top_categories = c.fetchall()

        c.execute("""SELECT users.username, COUNT(items.id) as count
                     FROM items
                     JOIN users ON items.user_id = users.id
                     WHERE datetime(items.created_at) >= datetime('now', ?)
                     GROUP BY users.id
                     ORDER BY count DESC
                     LIMIT 10""", (period_filter,))
        top_reporters = c.fetchall()

        c.execute("""SELECT action, COUNT(*) as count
                     FROM activity_logs
                     WHERE datetime(created_at) >= datetime('now', ?)
                     GROUP BY action
                     ORDER BY count DESC
                     LIMIT 12""", (period_filter,))
        top_actions = c.fetchall()

        conn.close()

        log_activity(current_user.id, 'ADMIN_VIEW_ANALYTICS', f'Viewed analytics for {period} days')

        return render_template(
            'admin_analytics.html',
            period=period,
            period_days=period_days,
            new_users=new_users,
            new_items=new_items,
            lost_reports=lost_reports,
            found_reports=found_reports,
            claimed_items=claimed_items,
            claim_rate=claim_rate,
            daily_item_activity=daily_item_activity,
            top_categories=top_categories,
            top_reporters=top_reporters,
            top_actions=top_actions
        )
    except Exception as e:
        logger.error(f"Error loading analytics: {str(e)}")
        flash('Error loading analytics.', 'error')
        return redirect(url_for('admin_dashboard'))

# ==================== USER MANAGEMENT ====================

@app.route('/admin/user-management')
@app.route('/admin/users')
@login_required
def admin_users():
    """View and manage all users."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        page = max(request.args.get('page', 1, type=int), 1)
        per_page = 20
        search_query = request.args.get('q', '').strip()
        role_filter = request.args.get('role', 'all').strip().lower()
        status_filter = request.args.get('status', 'all').strip().lower()

        if role_filter not in {'all', 'admin', 'user'}:
            role_filter = 'all'
        if status_filter not in {'all', 'active', 'banned'}:
            status_filter = 'all'

        where_clauses = []
        params = []

        if search_query:
            where_clauses.append("(username LIKE ? OR email LIKE ?)")
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term])

        if role_filter == 'admin':
            where_clauses.append("is_admin = 1")
        elif role_filter == 'user':
            where_clauses.append("is_admin = 0")

        if status_filter == 'active':
            where_clauses.append("is_banned = 0")
        elif status_filter == 'banned':
            where_clauses.append("is_banned = 1")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get overall user count and filtered count
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]

        c.execute(f"SELECT COUNT(*) FROM users {where_sql}", params)
        filtered_users = c.fetchone()[0]
        total_pages = max((filtered_users + per_page - 1) // per_page, 1)
        if page > total_pages:
            page = total_pages

        # Get filtered, paginated users
        offset = (page - 1) * per_page
        c.execute(f"""SELECT id, username, email, reputation_score, is_admin, is_banned,
                             ban_reason, created_at
                     FROM users
                     {where_sql}
                     ORDER BY created_at DESC
                     LIMIT ? OFFSET ?""", params + [per_page, offset])
        users = c.fetchall()

        conn.close()

        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)
        page_numbers = list(range(start_page, end_page + 1))
        log_activity(
            current_user.id,
            'ADMIN_VIEW_USERS',
            f'Viewed users page {page} (q="{search_query}", role="{role_filter}", status="{status_filter}")'
        )

        return render_template(
            'admin_users.html',
            users=users,
            page=page,
            total_pages=total_pages,
            page_numbers=page_numbers,
            search_query=search_query,
            role_filter=role_filter,
            status_filter=status_filter,
            filtered_users=filtered_users,
            total_users=total_users
        )
    except Exception as e:
        logger.error(f"Error loading user list: {str(e)}")
        flash('Error loading user list.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
def admin_update_user_role(user_id):
    """Update a user's role (admin/user)."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        if user_id == current_user.id:
            flash('You cannot change your own role.', 'error')
            return admin_users_redirect()

        new_role = request.form.get('role', '').strip().lower()
        if new_role not in {'admin', 'user'}:
            flash('Invalid role selected.', 'error')
            return admin_users_redirect()

        new_role_value = 1 if new_role == 'admin' else 0

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT username, is_admin FROM users WHERE id = ?", (user_id,))
        user_record = c.fetchone()

        if not user_record:
            conn.close()
            flash('User not found.', 'error')
            return admin_users_redirect()

        username, current_role = user_record
        if current_role == new_role_value:
            conn.close()
            flash(f'{username} already has this role.', 'info')
            return admin_users_redirect()

        if current_role == 1 and new_role_value == 0:
            c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
            admin_count = c.fetchone()[0]
            if admin_count <= 1:
                conn.close()
                flash('Cannot demote the last admin account.', 'error')
                return admin_users_redirect()

        c.execute("""UPDATE users
                     SET is_admin = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?""", (new_role_value, user_id))
        conn.commit()
        conn.close()

        role_label = 'Admin' if new_role_value == 1 else 'User'
        action = 'USER_PROMOTED_TO_ADMIN' if new_role_value == 1 else 'USER_DEMOTED_FROM_ADMIN'
        log_activity(current_user.id, action, f'Set role for {username} to {role_label}')
        flash(f'Updated role for {username} to {role_label}.', 'success')
        return admin_users_redirect()
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        flash('Error updating user role.', 'error')
        return admin_users_redirect()

@app.route('/admin/users/<int:user_id>/ban', methods=['POST'])
@app.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@login_required
def admin_ban_user(user_id):
    """Ban a user."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        if user_id == current_user.id:
            flash('You cannot ban your own account.', 'error')
            return admin_users_redirect()

        reason = request.form.get('ban_reason', 'Violation of terms')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT username, is_banned FROM users WHERE id = ?", (user_id,))
        user_record = c.fetchone()

        if not user_record:
            conn.close()
            flash('User not found.', 'error')
            return admin_users_redirect()

        username, is_banned = user_record
        if is_banned == 1:
            conn.close()
            flash(f'User {username} is already banned.', 'info')
            return admin_users_redirect()

        c.execute("""UPDATE users
                     SET is_banned = 1, ban_reason = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?""", (reason, user_id))
        conn.commit()

        log_activity(current_user.id, 'USER_BANNED', f'Banned user {username}: {reason}')

        conn.close()

        flash(f'User {username} has been banned.', 'success')
        return admin_users_redirect()
    except Exception as e:
        logger.error(f"Error banning user: {str(e)}")
        flash('Error banning user.', 'error')
        return admin_users_redirect()

@app.route('/admin/users/<int:user_id>/unban', methods=['POST'])
@app.route('/admin/user/<int:user_id>/unban', methods=['POST'])
@login_required
def admin_unban_user(user_id):
    """Unban a user."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT username, is_banned FROM users WHERE id = ?", (user_id,))
        user_record = c.fetchone()

        if not user_record:
            conn.close()
            flash('User not found.', 'error')
            return admin_users_redirect()

        username, is_banned = user_record
        if is_banned == 0:
            conn.close()
            flash(f'User {username} is already active.', 'info')
            return admin_users_redirect()

        c.execute("""UPDATE users
                     SET is_banned = 0, ban_reason = NULL, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?""", (user_id,))
        conn.commit()

        log_activity(current_user.id, 'USER_UNBANNED', f'Unbanned user {username}')

        conn.close()

        flash(f'User {username} has been unbanned.', 'success')
        return admin_users_redirect()
    except Exception as e:
        logger.error(f"Error unbanning user: {str(e)}")
        flash('Error unbanning user.', 'error')
        return admin_users_redirect()

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete a user account."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        if user_id == current_user.id:
            flash('You cannot delete your own account.', 'error')
            return admin_users_redirect()

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT username, is_admin FROM users WHERE id = ?", (user_id,))
        user_record = c.fetchone()

        if not user_record:
            conn.close()
            flash('User not found.', 'error')
            return admin_users_redirect()

        username, user_is_admin = user_record

        if user_is_admin == 1:
            c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
            admin_count = c.fetchone()[0]
            if admin_count <= 1:
                conn.close()
                flash('Cannot delete the last admin account.', 'error')
                return admin_users_redirect()

        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

        log_activity(current_user.id, 'USER_DELETED', f'Deleted user {username}')

        conn.close()

        flash(f'User {username} has been deleted.', 'success')
        return admin_users_redirect()
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        flash('Error deleting user.', 'error')
        return admin_users_redirect()

# ==================== ITEM MANAGEMENT ====================

@app.route('/admin/item-management')
@app.route('/admin/items')
@login_required
def admin_items():
    """View and manage all items."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get total items
        c.execute("SELECT COUNT(*) FROM items")
        total_items = c.fetchone()[0]
        total_pages = (total_items + per_page - 1) // per_page

        # Get paginated items with user info
        offset = (page - 1) * per_page
        c.execute("""SELECT items.id, items.title, items.item_type, items.status,
                            items.is_verified, items.flagged, items.created_at,
                            users.username
                     FROM items
                     JOIN users ON items.user_id = users.id
                     ORDER BY items.created_at DESC
                     LIMIT ? OFFSET ?""", (per_page, offset))
        items = c.fetchall()

        conn.close()

        log_activity(current_user.id, 'ADMIN_VIEW_ITEMS', f'Viewed items page {page}')

        return render_template('admin_items.html', items=items, page=page, total_pages=total_pages)
    except Exception as e:
        logger.error(f"Error loading item list: {str(e)}")
        flash('Error loading item list.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/item/<int:item_id>/verify', methods=['POST'])
@login_required
def admin_verify_item(item_id):
    """Verify an item."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""UPDATE items SET is_verified = 1, flagged = 0, flagged_reason = NULL WHERE id = ?""",
                 (item_id,))
        conn.commit()

        c.execute("SELECT title FROM items WHERE id = ?", (item_id,))
        title = c.fetchone()[0]

        log_activity(current_user.id, 'ITEM_VERIFIED', f'Verified item: {title}')

        conn.close()

        flash(f'Item "{title}" has been verified.', 'success')
        return redirect(url_for('admin_items'))
    except Exception as e:
        logger.error(f"Error verifying item: {str(e)}")
        flash('Error verifying item.', 'error')
        return redirect(url_for('admin_items'))

@app.route('/admin/item/<int:item_id>/flag', methods=['POST'])
@login_required
def admin_flag_item(item_id):
    """Flag an item as inappropriate."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        reason = request.form.get('flag_reason', 'Inappropriate content')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""UPDATE items SET flagged = 1, flagged_reason = ? WHERE id = ?""",
                 (reason, item_id))
        conn.commit()

        c.execute("SELECT title FROM items WHERE id = ?", (item_id,))
        title = c.fetchone()[0]

        log_activity(current_user.id, 'ITEM_FLAGGED', f'Flagged item: {title} ({reason})')

        conn.close()

        flash(f'Item "{title}" has been flagged.', 'success')
        return redirect(url_for('admin_items'))
    except Exception as e:
        logger.error(f"Error flagging item: {str(e)}")
        flash('Error flagging item.', 'error')
        return redirect(url_for('admin_items'))

@app.route('/admin/item/<int:item_id>/delete', methods=['POST'])
@login_required
def admin_delete_item(item_id):
    """Delete an item."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT title FROM items WHERE id = ?", (item_id,))
        title = c.fetchone()[0]

        c.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()

        log_activity(current_user.id, 'ITEM_DELETED', f'Deleted item: {title}')

        conn.close()

        flash(f'Item "{title}" has been deleted.', 'success')
        return redirect(url_for('admin_items'))
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        flash('Error deleting item.', 'error')
        return redirect(url_for('admin_items'))

# ==================== SYSTEM SETTINGS ====================

@app.route('/admin/system-settings')
@app.route('/admin/settings')
@login_required
def admin_settings():
    """View and manage system settings."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT setting_key, setting_value, setting_type FROM system_settings")
        settings = {row[0]: row[1] for row in c.fetchall()}

        conn.close()

        log_activity(current_user.id, 'ADMIN_VIEW_SETTINGS', 'Viewed system settings')

        return render_template('admin_settings.html', settings=settings)
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        flash('Error loading settings.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings/update', methods=['POST'])
@login_required
def admin_update_settings():
    """Update system settings."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        # Update settings from form
        max_file_size = request.form.get('max_file_size', '')
        maintenance_mode = request.form.get('maintenance_mode', '0')
        mail_server = request.form.get('mail_server', '')
        mail_port = request.form.get('mail_port', '')

        if max_file_size:
            set_setting('max_file_size', max_file_size, 'int')

        set_setting('maintenance_mode', maintenance_mode, 'bool')

        if mail_server:
            set_setting('mail_server', mail_server, 'string')

        if mail_port:
            set_setting('mail_port', mail_port, 'int')

        log_activity(current_user.id, 'SETTINGS_UPDATED', 'Updated system settings')

        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin_settings'))
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        flash('Error updating settings.', 'error')
        return redirect(url_for('admin_settings'))

# ==================== ACTIVITY LOGS ====================

@app.route('/admin/activity-logs')
@app.route('/admin/reports')
@app.route('/admin/logs')
@login_required
def admin_logs():
    """View activity logs and reports."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        page = max(request.args.get('page', 1, type=int), 1)
        per_page = 50
        action_filter = request.args.get('action', '').strip().upper()
        user_query = request.args.get('user', '').strip()
        where_sql, params = build_admin_logs_filters(action_filter, user_query)

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute(f"""SELECT COUNT(*)
                      FROM activity_logs
                      LEFT JOIN users ON activity_logs.user_id = users.id
                      {where_sql}""", params)
        total_logs = c.fetchone()[0]

        total_pages = max((total_logs + per_page - 1) // per_page, 1)
        if page > total_pages:
            page = total_pages

        offset = (page - 1) * per_page
        query_params = params + [per_page, offset]
        c.execute(f"""SELECT id, COALESCE(users.username, 'System'), activity_logs.action,
                             activity_logs.description, activity_logs.ip_address, activity_logs.created_at
                      FROM activity_logs
                      LEFT JOIN users ON activity_logs.user_id = users.id
                      {where_sql}
                      ORDER BY activity_logs.created_at DESC
                      LIMIT ? OFFSET ?""", query_params)
        logs = c.fetchall()

        c.execute(f"""SELECT activity_logs.action, COUNT(*) as count
                      FROM activity_logs
                      LEFT JOIN users ON activity_logs.user_id = users.id
                      {where_sql}
                      GROUP BY activity_logs.action
                      ORDER BY count DESC
                      LIMIT 12""", params)
        action_counts = c.fetchall()

        conn.close()

        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)
        page_numbers = list(range(start_page, end_page + 1))

        log_activity(current_user.id, 'ADMIN_VIEW_LOGS', f'Viewed logs page {page}')

        return render_template(
            'admin_logs.html',
            logs=logs,
            action_counts=action_counts,
            action_filter=action_filter,
            user_query=user_query,
            page=page,
            total_pages=total_pages,
            page_numbers=page_numbers
        )
    except Exception as e:
        logger.error(f"Error loading activity logs: {str(e)}")
        flash('Error loading activity logs.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/reports/export')
@login_required
def admin_export_reports():
    """Export filtered activity logs as CSV."""
    if not is_admin(current_user.id):
        flash('You do not have admin privileges.', 'error')
        return redirect(url_for('index'))

    try:
        action_filter = request.args.get('action', '').strip().upper()
        user_query = request.args.get('user', '').strip()
        where_sql, params = build_admin_logs_filters(action_filter, user_query)

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(f"""SELECT COALESCE(users.username, 'System'), activity_logs.action,
                             activity_logs.description, activity_logs.ip_address, activity_logs.created_at
                      FROM activity_logs
                      LEFT JOIN users ON activity_logs.user_id = users.id
                      {where_sql}
                      ORDER BY activity_logs.created_at DESC
                      LIMIT 5000""", params)
        rows = c.fetchall()
        conn.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['User', 'Action', 'Description', 'IP Address', 'Timestamp'])
        for row in rows:
            writer.writerow(row)

        filename = f"activity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    except Exception as e:
        logger.error(f"Error exporting reports: {str(e)}")
        flash('Error exporting report.', 'error')
        return redirect(url_for('admin_logs'))

# ==================== USER SETTINGS ====================

@app.route('/settings')
@app.route('/user/settings')
@login_required
def user_settings():
    """User settings page."""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT username, email, bio FROM users WHERE id = ?", (current_user.id,))
        user_data = c.fetchone()

        conn.close()
        preferences = get_user_preferences(current_user.id)

        log_activity(current_user.id, 'VIEW_SETTINGS', 'Viewed user settings')

        return render_template('user_settings.html', user_data=user_data, preferences=preferences)
    except Exception as e:
        logger.error(f"Error loading user settings: {str(e)}")
        flash('Error loading settings.', 'error')
        return redirect(url_for('profile'))

@app.route('/user/settings/update', methods=['POST'])
@login_required
def user_update_settings():
    """Update user settings."""
    try:
        email = request.form.get('email', '').strip()
        bio = request.form.get('bio', '').strip()
        theme = request.form.get('theme', 'system').strip().lower()
        items_per_page = request.form.get('items_per_page', '12').strip()
        email_notifications = 1 if request.form.get('email_notifications') else 0
        sms_notifications = 1 if request.form.get('sms_notifications') else 0

        if not email:
            flash('Email is required.', 'error')
            return redirect(url_for('user_settings'))

        if theme not in {'system', 'light', 'dark'}:
            theme = 'system'

        try:
            items_per_page = int(items_per_page)
        except ValueError:
            items_per_page = 12

        items_per_page = min(max(items_per_page, 6), 50)

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Check if email already exists (and belongs to different user)
        c.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, current_user.id))
        if c.fetchone():
            flash('Email already in use.', 'error')
            conn.close()
            return redirect(url_for('user_settings'))

        c.execute("""UPDATE users
                     SET email = ?, bio = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?""",
                  (email, bio, current_user.id))
        conn.commit()

        # Update current_user object
        current_user.email = email

        save_user_preferences(
            current_user.id,
            email_notifications,
            sms_notifications,
            theme,
            items_per_page
        )

        log_activity(current_user.id, 'SETTINGS_UPDATED', 'Updated profile settings and preferences')

        conn.close()

        flash('Settings updated successfully.', 'success')
        return redirect(url_for('user_settings'))
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        flash('Error updating settings.', 'error')
        return redirect(url_for('user_settings'))

@app.route('/user/settings/change-password', methods=['POST'])
@login_required
def user_change_password():
    """Change user password."""
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_password or not new_password:
            flash('All fields are required.', 'error')
            return redirect(url_for('user_settings'))

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('user_settings'))

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('user_settings'))

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Verify current password
        c.execute("SELECT password_hash FROM users WHERE id = ?", (current_user.id,))
        result = c.fetchone()

        if not result or not check_password_hash(result[0], current_password):
            flash('Current password is incorrect.', 'error')
            conn.close()
            return redirect(url_for('user_settings'))

        # Update password
        new_hash = generate_password_hash(new_password)
        c.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                 (new_hash, current_user.id))
        conn.commit()

        log_activity(current_user.id, 'PASSWORD_CHANGED', 'Changed password')

        conn.close()

        flash('Password changed successfully.', 'success')
        return redirect(url_for('user_settings'))
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        flash('Error changing password.', 'error')
        return redirect(url_for('user_settings'))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

# CLI command to create admin user (optional)
@app.cli.command()
def create_admin():
    """Create an admin user."""
    import getpass
    username = input('Enter admin username: ')
    email = input('Enter admin email: ')
    password = getpass.getpass('Enter admin password: ')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    password_hash = generate_password_hash(password)
    c.execute("""INSERT INTO users (username, email, password_hash)
                 VALUES (?, ?, ?)""",
              (username, email, password_hash))
    conn.commit()
    conn.close()
    print(f"Admin user '{username}' created successfully!")

if __name__ == '__main__':
    # IMPORTANT: Set debug=False in production!
    # Use environment variable to control debug mode
    DEBUG_MODE = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=DEBUG_MODE, host='0.0.0.0', port=5000)
