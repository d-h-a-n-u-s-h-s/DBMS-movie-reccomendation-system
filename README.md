# Movie Review & Recommendation System

A comprehensive movie and TV show review platform with recommendation engine, built with MySQL and Python Flask.

## Features

- **User Management**: Three user roles (Admin, Verified User, Normal User)
- **Content Management**: Movies and TV shows with genres, ratings, and reviews
- **Social Features**: User friendships and social recommendations
- **Recommendation Engine**: Personalized recommendations based on preferences and friends
- **Analytics Dashboard**: Admin analytics for content and user insights
- **Database Features**: Stored procedures, functions, triggers, and views

## Tech Stack

- **Backend**: Python Flask
- **Database**: MySQL 8.0+
- **Frontend**: HTML, CSS, Bootstrap, Jinja2 templates
- **Authentication**: Session-based with role-based access control

## 🚀 One-Command Setup

**Just run this single command to set up everything:**

```bash
python setup_complete.py
```

This script will:
- ✅ Check Python and MySQL installation
- ✅ Create the database and import schema
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Create configuration files
- ✅ Test database connection
- ✅ Clean up unnecessary files
- ✅ Start the application

**That's it!** The application will be available at `http://localhost:5000`

## Default Login Credentials

- **Admin**: `admin@movieapp.com` / `password123`
- **User**: `john@example.com` / `password123`

## Prerequisites

- Python 3.10+
- MySQL 8.0+
- Internet connection (for package installation)

## What the Setup Script Does

1. **Environment Check**: Verifies Python and MySQL are installed
2. **Database Setup**: Creates database and imports complete schema
3. **Python Environment**: Creates virtual environment and installs packages
4. **Configuration**: Creates `.env` file with your MySQL password
5. **Testing**: Verifies database connection works
6. **Cleanup**: Removes unnecessary setup files
7. **Launch**: Starts the Flask application

## Database Features Demonstrated

The application showcases advanced MySQL features:

### Stored Procedures
- `GetUserRecommendations(user_id)`: Get personalized recommendations
- `AddReview(user_id, content_id, rating, review_text)`: Add new review
- `GetPopularContent(limit)`: Get trending content
- `GetTopRatedContent(limit)`: Get highest rated content

### Functions
- `CalculateAverageRating(content_id)`: Calculate average rating
- `GetUserRole(user_id)`: Get user role
- `IsContentLiked(user_id, content_id)`: Check if user liked content

### Triggers
- `UpdateAverageRating`: Automatically update ratings when reviews change
- `ValidateReviewRating`: Ensure ratings are within valid range
- `LogUserActivity`: Track user actions for analytics

### Views
- `UserActivitySummary`: User activity overview
- `ContentAnalytics`: Content performance metrics
- `FriendshipNetwork`: Social network visualization

## User Roles

### Admin
- Full system access
- User management
- Content management
- Analytics dashboard
- System configuration

### Verified User
- Create reviews
- Add friends
- Access recommendations
- View analytics (limited)

### Normal User
- View content
- Create basic reviews
- Limited social features

## Project Structure

```
movie-review-system/
├── setup_complete.py      # One-command setup script
├── app.py                 # Main Flask application
├── models.py              # Database models and connection
├── requirements.txt       # Python dependencies
├── movie_review_system_complete.sql  # Complete database schema with all procedures
├── .env                   # Environment configuration (created by setup)
├── templates/             # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── movies.html
│   ├── shows.html
│   ├── admin_dashboard.html
│   └── ...
├── static/                # Static assets
│   ├── css/
│   └── js/
└── README.md
```

## Manual Setup (If Needed)

If the automated setup fails, you can set up manually:

1. **Database**: `mysql -u root -p movie_review_system < movie_review_system_complete.sql`
2. **Python**: `python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt`
3. **Config**: Create `.env` file with your MySQL password
4. **Run**: `python app.py`

## Troubleshooting

### Common Issues

1. **"Python not found"**
   - Install Python 3.10+ from python.org
   - Add Python to system PATH

2. **"MySQL not found"**
   - Install MySQL 8.0+ from mysql.com
   - Start MySQL service

3. **"Access denied"**
   - Check MySQL root password
   - Ensure MySQL service is running

4. **"Database connection failed"**
   - Verify `.env` file has correct password
   - Check MySQL service status

## Features in Action

The GUI demonstrates all database features:

- **Stored Procedures**: Recommendation engine, review management
- **Functions**: Rating calculations, user role checks
- **Triggers**: Automatic rating updates, validation
- **Views**: Analytics dashboards, user summaries
- **Complex Queries**: Social recommendations, content analytics

## License

Educational project - feel free to use and modify!

## Contributing

Issues and pull requests welcome!
