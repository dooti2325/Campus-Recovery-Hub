# Campus Recovery Hub

A modern, secure web platform to help campus communities reunite lost items with their owners.

## 🌟 Features

### Core Functionality
- ✅ **Report Lost Items** - Post items you've lost with details and photos
- ✅ **Report Found Items** - Help the community by reporting found items
- ✅ **Browse Items** - Search and filter items by type, category, and location
- ✅ **Item Details** - View complete item information with images and QR codes
- ✅ **Claim Items** - Match lost/found items and notify owners
- ✅ **User Profiles** - Track your items and statistics
- ✅ **QR Codes** - Share items via scannable QR codes
- ✅ **Email Notifications** - Get notified when your items are claimed
- ✅ **Pagination** - Browse large lists efficiently

### Security Features
- 🔐 **User Authentication** - Secure login and registration
- 🔐 **Password Hashing** - Industry-standard encryption
- 🔐 **CSRF Protection** - Protection against cross-site attacks
- 🔐 **SQL Injection Prevention** - Parameterized queries
- 🔐 **Secure Sessions** - HTTPOnly, secure cookies
- 🔐 **Authorization** - User ownership validation

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   cd Campus-Recovery-Hub
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set:
   - `SECRET_KEY` - Generate a random string
   - `FLASK_DEBUG` - Set to `False` for production
   - Email settings (optional, for notifications)

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   ```
   Open your browser: http://localhost:5000
   ```

## 📝 Creating Your Account

1. Click **Sign Up** on the homepage
2. Enter username, email, and password (minimum 6 characters)
3. Click **Create Account**
4. Log in with your credentials
5. Start reporting items!

## 📋 How to Use

### Report a Lost Item
1. Log in to your account
2. Click **Report Lost** in the navigation
3. Fill in the form:
   - **Title** - Name of the item (required)
   - **Description** - Details about the item
   - **Date** - When it was lost
   - **Location** - Where it was lost (required)
   - **Contact** - How to reach you (required)
   - **Category** - Type of item
   - **Image** - Upload a photo (optional)
4. Click **Report** to submit

### Report a Found Item
Same as above, but click **Report Found** instead.

### Browse Items
1. Click **Browse Items** to see all items
2. Use filters to find specific items
3. Click an item to view full details
4. Click **Claim Item** if you can help

### Manage Your Items
1. Click your username → **Profile**
2. View all your items
3. Click **Delete** to remove an item

### Check Notifications
1. Click your username → **Notifications**
2. View updates on your items

## 📧 Email Notifications (Optional)

To enable email notifications:

### Gmail Setup
1. Enable 2-factor authentication on your Gmail
2. Generate an app password
3. Edit `.env`:
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

## 📁 Project Structure

```
Campus-Recovery-Hub/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
├── database.db                # SQLite database (auto-created)
│
├── templates/                 # HTML templates
│   ├── base.html             # Master template
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── profile.html          # User profile
│   ├── items.html            # Items listing
│   ├── item_detail.html      # Item details with QR code
│   ├── report_lost.html      # Report lost form
│   ├── report_found.html     # Report found form
│   ├── notifications.html    # Notifications
│   ├── 404.html / 500.html   # Error pages
│   └── email/
│       └── item_claimed.html # Email template
│
└── static/                    # Static files
    ├── css/style.css         # Main stylesheet
    ├── uploads/              # User-uploaded images
    └── qr_codes/             # Generated QR codes
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-key-here

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@campusrecoveryhub.com
```

## 📊 Database

### Tables
- **users** - User accounts and profiles
- **items** - Lost and found items
- **notifications** - User notifications

Database is automatically created on first run with:
- 7 performance indexes
- Foreign key relationships
- Cascade delete

## 🔐 Security

### Implemented Features
- ✅ Password hashing with Werkzeug
- ✅ CSRF tokens on all forms
- ✅ Parameterized SQL queries
- ✅ Secure session management
- ✅ User authorization checks
- ✅ XSS protection

### Best Practices
- Never share your `SECRET_KEY`
- Use HTTPS in production
- Keep dependencies updated
- Use strong passwords

## 🐛 Troubleshooting

### Database Error
```bash
rm database.db
python app.py
```

### Email Not Working
- Verify SMTP credentials
- For Gmail: Use app passwords, not regular password
- Check firewall settings

### Port Already in Use
Change port in `app.py` or run:
```bash
python app.py --port 5001
```

## 📈 Performance

- 7 database indexes for fast queries
- Pagination support (12 items per page)
- Efficient code without duplication
- Optimized database schema

## 🚀 Deployment

### Local Development
```bash
FLASK_DEBUG=True python app.py
```

### Production
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Deploy to Heroku, Vercel, AWS, or your own server.

## 📚 Technologies

| Component | Technology |
|-----------|-----------|
| Backend | Flask 3.1.2 |
| Authentication | Flask-Login |
| CSRF Protection | Flask-WTF |
| Email | Flask-Mail |
| QR Codes | qrcode |
| Database | SQLite |
| Frontend | HTML5/CSS3/JavaScript |

## 📖 API Routes

| Route | Method | Auth |
|-------|--------|------|
| `/register` | POST | No |
| `/login` | POST | No |
| `/logout` | GET | Yes |
| `/profile` | GET | Yes |
| `/items` | GET | No |
| `/report_lost` | POST | Yes |
| `/report_found` | POST | Yes |
| `/claim_item/<id>` | POST | Yes |

## 💡 Tips for Success

1. **Be specific** - More details help find items faster
2. **Upload photos** - Images improve match rates
3. **Use QR codes** - Share on social media
4. **Check notifications** - Stay updated on your items
5. **Share the platform** - Encourage your community

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Fork the repository and submit pull requests for improvements.

## ✨ What's New in v2.0

- ✅ User authentication system
- ✅ CSRF protection enabled
- ✅ QR code generation
- ✅ Email notifications
- ✅ Database optimization (7 indexes)
- ✅ Code refactoring (46 lines duplicate removed)
- ✅ Enhanced security features
- ✅ Professional UI/UX
- ✅ Pagination support

## 🎯 About Campus Recovery Hub

Dedicated to:
- Reuniting lost items with their owners
- Building community trust
- Reducing waste through recovery
- Making campus life easier

---

**Version**: 2.0.0 | **Status**: Production Ready | **License**: MIT

Campus Recovery Hub - Helping reunite lost belongings with their owners! 🎉
