from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Enhanced database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 item_type TEXT,
                 title TEXT,
                 description TEXT,
                 date TEXT,
                 location TEXT,
                 status TEXT,
                 contact TEXT,
                 image_path TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 category TEXT
                 )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # Get recent items for preview
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM items ORDER BY created_at DESC LIMIT 6")
    recent_items = c.fetchall()
    
    # Get statistics
    c.execute("SELECT COUNT(*) FROM items WHERE item_type = 'Lost' AND status = 'Unclaimed'")
    lost_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM items WHERE item_type = 'Found' AND status = 'Unclaimed'")
    found_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM items WHERE status = 'Claimed'")
    claimed_count = c.fetchone()[0]
    
    conn.close()
    
    stats = {
        'lost': lost_count,
        'found': found_count,
        'claimed': claimed_count
    }
    
    return render_template('index.html', recent_items=recent_items, stats=stats)

@app.route('/report_lost', methods=['GET', 'POST'])
def report_lost():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        contact = request.form['contact']
        category = request.form['category']
        
        # Handle file upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_path = f'uploads/{filename}'

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO items (item_type, title, description, date, location, status, contact, image_path, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Lost', title, description, date, location, 'Unclaimed', contact, image_path, category))
        conn.commit()
        conn.close()
        
        flash('Lost item reported successfully!', 'success')
        return redirect(url_for('items'))
    return render_template('report_lost.html')

@app.route('/report_found', methods=['GET', 'POST'])
def report_found():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        contact = request.form['contact']
        category = request.form['category']
        
        # Handle file upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_path = f'uploads/{filename}'

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO items (item_type, title, description, date, location, status, contact, image_path, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Found', title, description, date, location, 'Unclaimed', contact, image_path, category))
        conn.commit()
        conn.close()
        
        flash('Found item reported successfully!', 'success')
        return redirect(url_for('items'))
    return render_template('report_found.html')

@app.route('/items')
def items():
    # Get filter parameters
    item_type = request.args.get('type', '')
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Build query with filters
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    
    if item_type:
        query += " AND item_type = ?"
        params.append(item_type)
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    query += " ORDER BY created_at DESC"
    
    c.execute(query, params)
    items = c.fetchall()
    
    # Get unique categories for filter dropdown
    c.execute("SELECT DISTINCT category FROM items WHERE category IS NOT NULL ORDER BY category")
    categories = [row[0] for row in c.fetchall()]
    
    conn.close()
    return render_template('items.html', items=items, categories=categories, 
                         current_type=item_type, current_category=category, current_search=search)

@app.route('/claim_item/<int:item_id>')
def claim_item(item_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE items SET status = 'Claimed' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    flash('Item marked as claimed!', 'success')
    return redirect(url_for('items'))

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get image path before deleting
    c.execute("SELECT image_path FROM items WHERE id = ?", (item_id,))
    result = c.fetchone()
    if result and result[0]:
        image_path = os.path.join('static', result[0])
        if os.path.exists(image_path):
            os.remove(image_path)
    
    c.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('items'))

if __name__ == '__main__':
    app.run(debug=True)