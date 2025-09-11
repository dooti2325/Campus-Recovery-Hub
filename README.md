# Campus Recovery Hub

A comprehensive web-based platform designed to streamline the management of lost and found items within campus communities. Built using Flask, this application serves as a centralized hub where students, faculty, and staff can report, search, and reunite with misplaced belongings.

## Features

- **Report Lost Items**: Users can submit detailed reports of lost items including descriptions, dates, locations, and contact information
- **Report Found Items**: Users can report found items with the same level of detail
- **Browse Items**: Comprehensive item database with advanced search and filtering capabilities
- **Image Uploads**: Secure file upload system for item photos
- **Real-time Statistics**: Dashboard showing lost, found, and reunited item counts
- **Responsive Design**: Mobile-friendly interface that works across all devices
- **Item Management**: Mark items as claimed or delete entries
- **Category System**: Organize items by categories for better filtering

## Technologies Used

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Inter)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Campus Recovery Hub
   ```

2. Install dependencies:
   ```bash
   pip install flask
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

### Reporting Items
1. Navigate to the homepage
2. Click "Report Lost Item" or "Report Found Item"
3. Fill in the required details (title, description, date, location, contact, category)
4. Optionally upload an image of the item
5. Submit the form

### Browsing Items
1. Click "View Items" from the navigation
2. Use the search bar to find specific items
3. Apply filters by type (Lost/Found), category, or location
4. Click on items to view full details

### Managing Items
- **Claim Item**: Click the claim button to mark an item as reunited
- **Delete Item**: Use the delete button to remove an item from the database

## Project Structure

```
Campus Recovery Hub/
├── app.py                 # Main Flask application
├── database.db           # SQLite database (created automatically)
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── uploads/          # Uploaded item images
└── templates/
    ├── index.html        # Homepage
    ├── items.html        # Items listing page
    ├── report_lost.html  # Lost item report form
    └── report_found.html # Found item report form
```

## Database Schema

The application uses SQLite with the following table structure:

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT,           -- 'Lost' or 'Found'
    title TEXT,               -- Item title
    description TEXT,         -- Item description
    date TEXT,                -- Date when item was lost/found
    location TEXT,            -- Location where item was lost/found
    status TEXT,              -- 'Unclaimed' or 'Claimed'
    contact TEXT,             -- Contact information
    image_path TEXT,          -- Path to uploaded image
    created_at TIMESTAMP,     -- Record creation timestamp
    category TEXT             -- Item category
);
```

## Security Features

- Input validation and sanitization
- Secure file upload handling
- Protection against common web vulnerabilities
- CSRF protection through Flask-WTF (if implemented)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please contact:
- Email: support@campusrecovery.edu
- Phone: (555) 123-4567

## Future Enhancements

- User authentication and profiles
- Email notifications for matches
- QR code generation for items
- Admin dashboard for moderation
- API endpoints for mobile app integration
- Multi-language support

---

Campus Recovery Hub - Helping reunite lost belongings with their owners, one item at a time.
