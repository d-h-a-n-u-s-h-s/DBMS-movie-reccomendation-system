"""
Flask Application - Movie Review & Recommendation System
Main application file with routes and role-based access control
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import *
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize database connection
db.connect()

# Decorator for admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Admin access check for {f.__name__}")
        logger.info(f"Session user_id: {session.get('user_id')}")
        
        if not session.get('user_id'):
            logger.warning("No user_id in session")
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        try:
            user = User.get_user_by_id(session['user_id'])
            logger.info(f"User found: {user}")
            
            if not user:
                logger.warning("User not found in database")
                flash('User not found.', 'error')
                return redirect(url_for('login'))
            
            if user.get('Role') != 'admin':
                logger.warning(f"User role is {user.get('Role')}, admin required")
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('home'))
            
            logger.info("Admin access granted")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in admin_required decorator: {e}")
            flash(f'Error checking admin access: {str(e)}', 'error')
            return redirect(url_for('home'))
    
    return decorated_function

@app.route('/')
def home():
    """Home page with recent reviews and popular content"""
    try:
        # Get data with fallbacks
        recent_reviews = []
        popular_movies = []
        top_rated_movies = []
        
        try:
            recent_reviews = Review.get_recent_reviews(5)
        except Exception as e:
            logger.warning(f"Could not load recent reviews: {e}")
            recent_reviews = []
        
        try:
            popular_movies = Analytics.get_popular_movies()[:5]
        except Exception as e:
            logger.warning(f"Could not load popular movies: {e}")
            popular_movies = []
        
        try:
            top_rated_movies = Analytics.get_top_rated_movies()[:5]
        except Exception as e:
            logger.warning(f"Could not load top rated movies: {e}")
            top_rated_movies = []
        
        # Get total counts for quick stats
        total_movies = 0
        total_reviews = 0
        try:
            total_movies = db.execute_query("SELECT COUNT(*) as count FROM Movie")[0]['count']
            total_reviews = db.execute_query("SELECT COUNT(*) as count FROM Reviews")[0]['count']
        except Exception as e:
            logger.warning(f"Could not load total counts: {e}")
        
        return render_template('home.html', 
                             recent_reviews=recent_reviews,
                             popular_movies=popular_movies,
                             top_rated_movies=top_rated_movies,
                             total_movies=total_movies,
                             total_reviews=total_reviews)
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        # Return with empty data instead of showing error
        return render_template('home.html', 
                             recent_reviews=[],
                             popular_movies=[],
                             top_rated_movies=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        try:
            user = User.get_user_by_email(email)
            if user and User.verify_password(user, password):
                session['user_id'] = user['User_ID']
                session['user_name'] = user['Name']
                session['user_role'] = user['Role']
                flash(f'Welcome back, {user["Name"]}!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password.', 'error')
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        age = request.form.get('age', type=int)
        gender = request.form.get('gender')
        role = request.form.get('role', 'normal_user')
        verified_entity_type = request.form.get('verified_entity_type')
        verified_entity_id = request.form.get('verified_entity_id', type=int)
        
        # Convert empty strings to None for database
        if verified_entity_type == '':
            verified_entity_type = None
        if verified_entity_id == '' or verified_entity_id is None:
            verified_entity_id = None
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('Please fill in all required fields.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if age and (age < 13 or age > 120):
            flash('Age must be between 13 and 120.', 'error')
            return render_template('register.html')
        
        try:
            # Check if email already exists
            existing_user = User.get_user_by_email(email)
            if existing_user:
                flash('Email already registered.', 'error')
                return render_template('register.html')
            
            # Create user
            user_id = User.create_user(
                name=name,
                email=email,
                password=password,
                role=role,
                age=age,
                gender=gender,
                verified_entity_type=verified_entity_type,
                verified_entity_id=verified_entity_id
            )
            
            if user_id:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'error')
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash(f'Registration failed: {str(e)}', 'error')
    
    # Get data for dropdowns
    companies = ProductionCompany.get_all_companies()
    celebrities = Celebrity.get_all_celebrities()
    
    return render_template('register.html', companies=companies, celebrities=celebrities)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/movies')
def movies():
    """List all movies"""
    try:
        # Optional filters
        genre_id = request.args.get('genre', type=int)
        q = request.args.get('q', type=str)

        movies = Movie.get_movies_filtered(genre_id=genre_id, search_query=q) if (genre_id or q) else Movie.get_all_movies()
        genres = Genre.get_all_genres()
        return render_template('movies.html', movies=movies, genres=genres, selected_genre=genre_id, q=q or '')
    except Exception as e:
        logger.error(f"Error loading movies: {e}")
        flash('Error loading movies. Please try again.', 'error')
        return render_template('movies.html', movies=[], genres=[], selected_genre=None, q='')

@app.route('/movie/<int:movie_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_movie(movie_id):
    """Edit movie (admin only)"""
    try:
        movie = Movie.get_movie_by_id(movie_id)
        if not movie:
            flash('Movie not found.', 'error')
            return redirect(url_for('movies'))
        
        if request.method == 'POST':
            try:
                title = request.form.get('title')
                description = request.form.get('description')
                year = request.form.get('year', type=int)
                length = request.form.get('length', type=int)
                age_rating = request.form.get('age_rating')
                genre_ids = request.form.getlist('genres')
                
                # Get celebrity and production company data
                celebrity_data = request.form.get('celebrity_data')
                production_data = request.form.get('production_data')
                
                # Validation
                if not all([title, year]):
                    flash('Title and year are required.', 'error')
                    return redirect(url_for('edit_movie', movie_id=movie_id))
                
                if year < 1888 or year > 2030:
                    flash('Year must be between 1888 and 2030.', 'error')
                    return redirect(url_for('edit_movie', movie_id=movie_id))
                
                # Update movie with all details
                success = Movie.update_movie_with_details(
                    movie_id=movie_id,
                    title=title,
                    description=description,
                    year=year,
                    length=length,
                    age_rating=age_rating,
                    genre_ids=genre_ids,
                    celebrity_data=celebrity_data,
                    production_data=production_data
                )
                
                if success:
                    flash('Movie updated successfully!', 'success')
                    return redirect(url_for('movie_detail', movie_id=movie_id))
                else:
                    flash('Failed to update movie.', 'error')
                    
            except Exception as e:
                logger.error(f"Error updating movie: {e}")
                flash(f'Error updating movie: {str(e)}', 'error')
        
        # Get all data for the form
        genres = Genre.get_all_genres()
        celebrities = Celebrity.get_all_celebrities()
        production_companies = ProductionCompany.get_all_companies()
        movie_genres = Movie.get_movie_genres(movie_id)
        movie_celebrities = Movie.get_movie_celebrities(movie_id)
        movie_productions = Movie.get_movie_production_companies(movie_id)
        
        return render_template('edit_movie.html', 
                             movie=movie,
                             genres=genres,
                             celebrities=celebrities,
                             production_companies=production_companies,
                             movie_genres=movie_genres,
                             movie_celebrities=movie_celebrities,
                             movie_productions=movie_productions)
                             
    except Exception as e:
        logger.error(f"Error in edit movie: {e}")
        flash('Error loading edit form.', 'error')
        return redirect(url_for('movie_detail', movie_id=movie_id))

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    """Movie detail page"""
    try:
        movie = Movie.get_movie_by_id(movie_id)
        if not movie:
            flash('Movie not found.', 'error')
            return redirect(url_for('movies'))
        
        genres = Movie.get_movie_genres(movie_id)
        celebrities = Movie.get_movie_celebrities(movie_id)
        reviews = Movie.get_movie_reviews(movie_id)
        
        # Check if user can edit this movie (admin can edit all)
        can_edit = session.get('user_role') == 'admin'
        
        return render_template('movie_detail.html', 
                             movie=movie,
                             genres=genres,
                             celebrities=celebrities,
                             reviews=reviews,
                             can_edit=can_edit)
    except Exception as e:
        logger.error(f"Error loading movie detail: {e}")
        flash('Error loading movie details. Please try again.', 'error')
        return redirect(url_for('movies'))

@app.route('/shows')
def shows():
    """List all shows"""
    try:
        genre_id = request.args.get('genre', type=int)
        q = request.args.get('q', type=str)
        shows = TVShow.get_shows_filtered(genre_id=genre_id, search_query=q) if (genre_id or q) else TVShow.get_all_shows()
        genres = Genre.get_all_genres()
        return render_template('shows.html', shows=shows, genres=genres, selected_genre=genre_id, q=q or '')
    except Exception as e:
        logger.error(f"Error loading shows: {e}")
        flash('Error loading shows. Please try again.', 'error')
        return render_template('shows.html', shows=[], genres=[], selected_genre=None, q='')

@app.route('/show/<int:show_id>')
def show_detail(show_id):
    """Show detail page"""
    try:
        show = TVShow.get_show_by_id(show_id)
        if not show:
            flash('Show not found.', 'error')
            return redirect(url_for('shows'))
        
        genres = TVShow.get_show_genres(show_id)
        reviews = TVShow.get_show_reviews(show_id)
        
        # Check if user can edit this show (admin can edit all)
        can_edit = session.get('user_role') == 'admin'
        
        return render_template('show_detail.html', 
                             show=show,
                             genres=genres,
                             reviews=reviews,
                             can_edit=can_edit)
    except Exception as e:
        logger.error(f"Error loading show detail: {e}")
        flash('Error loading show details. Please try again.', 'error')
        return redirect(url_for('shows'))

@app.route('/add_review', methods=['GET', 'POST'])
@login_required
def add_review():
    """Add a new review"""
    if request.method == 'POST':
        score = request.form.get('score', type=float)
        title = request.form.get('title')
        content = request.form.get('content')
        # Get movie_id and show_id, handling None values properly
        movie_id_raw = request.form.get('movie_id')
        show_id_raw = request.form.get('show_id')
        
        movie_id = None
        show_id = None
        
        if movie_id_raw:
            try:
                movie_id = int(movie_id_raw)
            except (ValueError, TypeError):
                movie_id = None
        
        if show_id_raw:
            try:
                show_id = int(show_id_raw)
            except (ValueError, TypeError):
                show_id = None
        
        # Ensure only one of movie_id or show_id is set
        if movie_id and show_id:
            flash('Please review either a movie or a show, not both.', 'error')
            return redirect(request.referrer or url_for('home'))
        
        if not movie_id and not show_id:
            flash('Please select a movie or show to review.', 'error')
            return redirect(request.referrer or url_for('home'))
        
        if not all([score, title]):
            flash('Please fill in all required fields.', 'error')
            return redirect(request.referrer or url_for('home'))
        
        if score < 0 or score > 10:
            flash('Score must be between 0 and 10.', 'error')
            return redirect(request.referrer or url_for('home'))
        
        try:
            Review.create_review(
                user_id=session['user_id'],
                score=score,
                title=title,
                content=content,
                movie_id=movie_id if movie_id else None,
                show_id=show_id if show_id else None
            )
            flash('Review added successfully!', 'success')
            
            # Redirect back to the content page
            if movie_id:
                return redirect(url_for('movie_detail', movie_id=movie_id))
            elif show_id:
                return redirect(url_for('show_detail', show_id=show_id))
            else:
                return redirect(url_for('home'))
                
        except Exception as e:
            logger.error(f"Error adding review: {e}")
            flash('Failed to add review. You may have already reviewed this content.', 'error')
            return redirect(request.referrer or url_for('home'))
    
    # GET request - show form
    movie_id = request.args.get('movie_id', type=int)
    show_id = request.args.get('show_id', type=int)
    
    if movie_id:
        movie = Movie.get_movie_by_id(movie_id)
        return render_template('add_review.html', movie=movie, show=None)
    elif show_id:
        show = TVShow.get_show_by_id(show_id)
        return render_template('add_review.html', movie=None, show=show)
    else:
        flash('Please select a movie or show to review.', 'error')
        return redirect(url_for('home'))

@app.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    """Edit an existing review"""
    try:
        # Get the review and verify ownership
        review = Review.get_review_by_id(review_id)
        if not review:
            flash('Review not found.', 'error')
            return redirect(url_for('profile'))
        
        if review['User_ID'] != session['user_id']:
            flash('You can only edit your own reviews.', 'error')
            return redirect(url_for('profile'))
        
        if request.method == 'POST':
            score = request.form.get('score', type=float)
            title = request.form.get('title')
            content = request.form.get('content')
            
            if not all([score, title]):
                flash('Please fill in all required fields.', 'error')
                return redirect(url_for('edit_review', review_id=review_id))
            
            if score < 0 or score > 10:
                flash('Score must be between 0 and 10.', 'error')
                return redirect(url_for('edit_review', review_id=review_id))
            
            try:
                Review.update_review(review_id, score, title, content)
                flash('Review updated successfully!', 'success')
                return redirect(url_for('profile'))
            except Exception as e:
                logger.error(f"Error updating review: {e}")
                flash('Error updating review. Please try again.', 'error')
                return redirect(url_for('edit_review', review_id=review_id))
        
        # GET request - show edit form
        movie = None
        show = None
        
        if review['Movie_ID']:
            movie = Movie.get_movie_by_id(review['Movie_ID'])
        elif review['Show_ID']:
            show = TVShow.get_show_by_id(review['Show_ID'])
        
        return render_template('edit_review.html', review=review, movie=movie, show=show)
        
    except Exception as e:
        logger.error(f"Error loading edit review page: {e}")
        flash('Error loading review. Please try again.', 'error')
        return redirect(url_for('profile'))

@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    """Delete a review"""
    try:
        # Get the review and verify ownership
        review = Review.get_review_by_id(review_id)
        if not review:
            flash('Review not found.', 'error')
            return redirect(url_for('profile'))
        
        if review['User_ID'] != session['user_id']:
            flash('You can only delete your own reviews.', 'error')
            return redirect(url_for('profile'))
        
        Review.delete_review(review_id)
        flash('Review deleted successfully!', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        logger.error(f"Error deleting review: {e}")
        flash('Error deleting review. Please try again.', 'error')
        return redirect(url_for('profile'))

@app.route('/recommendations')
@login_required
def recommendations():
    """User recommendations page"""
    try:
        user_id = session['user_id']
        
        # Get movie recommendations
        movie_recommendations = Recommendation.get_movie_recommendations(user_id, 10)
        
        # Get friend recommendations
        friend_recommendations = Recommendation.get_friend_recommendations(user_id, 10)
        
        # Get user preferences
        user_preferences = Genre.get_user_preferences(user_id)
        
        return render_template('recommendations.html',
                             movie_recommendations=movie_recommendations,
                             friend_recommendations=friend_recommendations,
                             user_preferences=user_preferences)
    except Exception as e:
        logger.error(f"Error loading recommendations: {e}")
        flash('Error loading recommendations. Please try again.', 'error')
        return render_template('recommendations.html')

@app.route('/friends')
@login_required
def friends():
    """User friends page"""
    try:
        user_id = session['user_id']
        q = request.args.get('q', type=str)
        friends = Friendship.get_user_friends_filtered(user_id, search_query=q)
        
        # Get all users for adding friends
        all_users = db.execute_query("SELECT User_ID, Name, Email FROM User WHERE User_ID != %s ORDER BY Name", (user_id,))
        
        return render_template('friends.html', friends=friends, all_users=all_users, q=q or '')
    except Exception as e:
        logger.error(f"Error loading friends: {e}")
        flash('Error loading friends. Please try again.', 'error')
        return render_template('friends.html', friends=[], all_users=[], q='')

@app.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    """Add a friend"""
    friend_id = request.form.get('friend_id', type=int)
    
    if not friend_id:
        flash('Please select a user to add as friend.', 'error')
        return redirect(url_for('friends'))
    
    try:
        Friendship.add_friendship(session['user_id'], friend_id)
        flash('Friend added successfully!', 'success')
    except Exception as e:
        logger.error(f"Error adding friend: {e}")
        flash('Failed to add friend. You may already be friends.', 'error')
    
    return redirect(url_for('friends'))

@app.route('/remove_friend', methods=['POST'])
@login_required
def remove_friend():
    """Remove a friend"""
    friend_id = request.form.get('friend_id', type=int)
    
    if not friend_id:
        flash('Please select a friend to remove.', 'error')
        return redirect(url_for('friends'))
    
    try:
        Friendship.remove_friendship(session['user_id'], friend_id)
        flash('Friend removed successfully!', 'success')
    except Exception as e:
        logger.error(f"Error removing friend: {e}")
        flash('Failed to remove friend.', 'error')
    
    return redirect(url_for('friends'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        user_id = session['user_id']
        user = User.get_user_by_id(user_id)
        user_stats = User.get_user_stats(user_id)
        user_reviews = Review.get_user_reviews(user_id)
        
        # Ensure user_stats has default values
        if not user_stats:
            user_stats = {'review_count': 0, 'friend_count': 0, 'avg_score': 'N/A'}
        else:
            # Ensure all required fields exist
            user_stats.setdefault('review_count', 0)
            user_stats.setdefault('friend_count', 0)
            user_stats.setdefault('avg_score', 'N/A')
        
        return render_template('profile.html', 
                             user=user,
                             user_stats=user_stats,
                             user_reviews=user_reviews)
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('home'))

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        # Get statistics
        stats = {
            'total_users': db.execute_query("SELECT COUNT(*) as count FROM User")[0]['count'],
            'total_movies': db.execute_query("SELECT COUNT(*) as count FROM Movie")[0]['count'],
            'total_shows': db.execute_query("SELECT COUNT(*) as count FROM TV_Show")[0]['count'],
            'total_reviews': db.execute_query("SELECT COUNT(*) as count FROM Reviews")[0]['count'],
            'total_friendships': db.execute_query("SELECT COUNT(*) as count FROM Friends")[0]['count']
        }
        
        # Get recent activity
        recent_reviews = Review.get_recent_reviews(10)
        active_users = Analytics.get_active_users()[:10]
        
        return render_template('admin_dashboard.html', 
                             stats=stats,
                             recent_reviews=recent_reviews,
                             active_users=active_users)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        flash('Error loading admin dashboard.', 'error')
        # Provide default stats to prevent template errors
        default_stats = {
            'total_users': 0,
            'total_movies': 0,
            'total_shows': 0,
            'total_reviews': 0,
            'total_friendships': 0
        }
        return render_template('admin_dashboard.html', 
                             stats=default_stats,
                             recent_reviews=[],
                             active_users=[])

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users management"""
    try:
        users = db.execute_query("SELECT * FROM User ORDER BY Created_At DESC")
        return render_template('admin_users.html', users=users)
    except Exception as e:
        logger.error(f"Error loading admin users: {e}")
        flash('Error loading users.', 'error')
        return render_template('admin_users.html', users=[])

@app.route('/admin/movies')
@admin_required
def admin_movies():
    """Admin movies management"""
    try:
        logger.info("Loading admin movies...")
        movies = Movie.get_all_movies()
        logger.info(f"Found {len(movies)} movies")
        return render_template('admin_movies.html', movies=movies)
    except Exception as e:
        logger.error(f"Error loading admin movies: {e}")
        flash(f'Error displaying movies: {str(e)}', 'error')
        return render_template('admin_movies.html', movies=[])

@app.route('/admin/movies/add', methods=['GET', 'POST'])
@admin_required
def admin_add_movie():
    """Add new movie"""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            year = request.form.get('year', type=int)
            length = request.form.get('length', type=int)
            age_rating = request.form.get('age_rating')
            genre_ids = request.form.getlist('genres')
            
            # Get celebrity and production company data
            celebrity_data = request.form.get('celebrity_data')
            production_data = request.form.get('production_data')
            
            # Validation
            if not all([title, year]):
                flash('Title and year are required.', 'error')
                return render_template('admin_add_movie.html', 
                                     genres=Genre.get_all_genres(),
                                     celebrities=Celebrity.get_all_celebrities(),
                                     production_companies=ProductionCompany.get_all_companies())
            
            if year < 1888 or year > 2030:
                flash('Year must be between 1888 and 2030.', 'error')
                return render_template('admin_add_movie.html',
                                     genres=Genre.get_all_genres(),
                                     celebrities=Celebrity.get_all_celebrities(),
                                     production_companies=ProductionCompany.get_all_companies())
            
            # Create movie with all details
            movie_id = Movie.create_movie_with_details(
                title=title,
                description=description,
                year=year,
                length=length,
                age_rating=age_rating,
                genre_ids=genre_ids,
                celebrity_data=celebrity_data,
                production_data=production_data
            )
            
            if movie_id:
                flash('Movie added successfully!', 'success')
                return redirect(url_for('admin_movies'))
            else:
                flash('Failed to add movie.', 'error')
                
        except Exception as e:
            logger.error(f"Error adding movie: {e}")
            flash(f'Error adding movie: {str(e)}', 'error')
    
    # Get all data for the form
    genres = Genre.get_all_genres()
    celebrities = Celebrity.get_all_celebrities()
    production_companies = ProductionCompany.get_all_companies()
    
    return render_template('admin_add_movie.html', 
                         genres=genres,
                         celebrities=celebrities,
                         production_companies=production_companies)

@app.route('/admin/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_movie(movie_id):
    """Edit movie"""
    movie = Movie.get_movie_by_id(movie_id)
    if not movie:
        flash('Movie not found.', 'error')
        return redirect(url_for('admin_movies'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            year = request.form.get('year', type=int)
            length = request.form.get('length', type=int)
            age_rating = request.form.get('age_rating')
            genre_ids = request.form.getlist('genres')
            
            # Get celebrity and production company data
            celebrity_data = request.form.get('celebrity_data')
            production_data = request.form.get('production_data')
            
            # Validation
            if not all([title, year]):
                flash('Title and year are required.', 'error')
                return render_template('admin_edit_movie.html', 
                                     movie=movie,
                                     genres=Genre.get_all_genres(),
                                     celebrities=Celebrity.get_all_celebrities(),
                                     production_companies=ProductionCompany.get_all_companies(),
                                     movie_genres=Movie.get_movie_genres(movie_id),
                                     movie_celebrities=Movie.get_movie_celebrities(movie_id),
                                     movie_productions=Movie.get_movie_production_companies(movie_id))
            
            if year < 1888 or year > 2030:
                flash('Year must be between 1888 and 2030.', 'error')
                return render_template('admin_edit_movie.html',
                                     movie=movie,
                                     genres=Genre.get_all_genres(),
                                     celebrities=Celebrity.get_all_celebrities(),
                                     production_companies=ProductionCompany.get_all_companies(),
                                     movie_genres=Movie.get_movie_genres(movie_id),
                                     movie_celebrities=Movie.get_movie_celebrities(movie_id),
                                     movie_productions=Movie.get_movie_production_companies(movie_id))
            
            # Update movie with all details
            success = Movie.update_movie_with_details(
                movie_id=movie_id,
                title=title,
                description=description,
                year=year,
                length=length,
                age_rating=age_rating,
                genre_ids=genre_ids,
                celebrity_data=celebrity_data,
                production_data=production_data
            )
            
            if success:
                flash('Movie updated successfully!', 'success')
                return redirect(url_for('admin_movies'))
            else:
                flash('Failed to update movie.', 'error')
                
        except Exception as e:
            logger.error(f"Error updating movie: {e}")
            flash(f'Error updating movie: {str(e)}', 'error')
    
    # Get all data for the form
    genres = Genre.get_all_genres()
    celebrities = Celebrity.get_all_celebrities()
    production_companies = ProductionCompany.get_all_companies()
    movie_genres = Movie.get_movie_genres(movie_id)
    movie_celebrities = Movie.get_movie_celebrities(movie_id)
    movie_productions = Movie.get_movie_production_companies(movie_id)
    
    return render_template('admin_edit_movie.html', 
                         movie=movie,
                         genres=genres,
                         celebrities=celebrities,
                         production_companies=production_companies,
                         movie_genres=movie_genres,
                         movie_celebrities=movie_celebrities,
                         movie_productions=movie_productions)

@app.route('/admin/movies/delete/<int:movie_id>', methods=['POST'])
@admin_required
def admin_delete_movie(movie_id):
    """Delete movie"""
    try:
        success = Movie.delete_movie(movie_id)
        if success:
            flash('Movie deleted successfully!', 'success')
        else:
            flash('Failed to delete movie.', 'error')
    except Exception as e:
        logger.error(f"Error deleting movie: {e}")
        flash(f'Error deleting movie: {str(e)}', 'error')
    
    return redirect(url_for('admin_movies'))

@app.route('/admin/shows/add', methods=['GET', 'POST'])
@admin_required
def admin_add_show():
    """Add new TV show"""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            year = request.form.get('year', type=int)
            seasons = request.form.get('seasons', type=int)
            episodes = request.form.get('episodes', type=int)
            age_rating = request.form.get('age_rating')
            
            # Validation
            if not all([title, year]):
                flash('Title and year are required.', 'error')
                return render_template('admin_add_show.html')
            
            if year < 1888 or year > 2030:
                flash('Year must be between 1888 and 2030.', 'error')
                return render_template('admin_add_show.html')
            
            # Create show
            show_id = TVShow.create_show(
                title=title,
                description=description,
                year=year,
                seasons=seasons,
                episodes=episodes,
                age_rating=age_rating
            )
            
            if show_id:
                flash('TV Show added successfully!', 'success')
                return redirect(url_for('admin_shows'))
            else:
                flash('Failed to add TV show.', 'error')
                
        except Exception as e:
            logger.error(f"Error adding TV show: {e}")
            flash(f'Error adding TV show: {str(e)}', 'error')
    
    return render_template('admin_add_show.html')

@app.route('/admin/shows')
@admin_required
def admin_shows():
    """Admin shows management"""
    try:
        shows = TVShow.get_all_shows()
        return render_template('admin_shows.html', shows=shows)
    except Exception as e:
        logger.error(f"Error loading admin shows: {e}")
        flash('Error loading shows.', 'error')
        return render_template('admin_shows.html', shows=[])

# Analytics and views routes
@app.route('/analytics/popular')
def analytics_popular():
    """Popular movies analytics"""
    try:
        popular_movies = Analytics.get_popular_movies()
        return render_template('analytics_popular.html', movies=popular_movies)
    except Exception as e:
        logger.error(f"Error loading popular movies: {e}")
        flash('Error loading popular movies.', 'error')
        return render_template('analytics_popular.html', movies=[])

@app.route('/analytics/top-rated')
def analytics_top_rated():
    """Top rated content analytics"""
    try:
        top_movies = Analytics.get_top_rated_movies()
        top_shows = Analytics.get_top_rated_shows()
        return render_template('analytics_top_rated.html', 
                             top_movies=top_movies,
                             top_shows=top_shows)
    except Exception as e:
        logger.error(f"Error loading top rated content: {e}")
        flash('Error loading top rated content.', 'error')
        return render_template('analytics_top_rated.html', top_movies=[], top_shows=[])

@app.route('/analytics/users')
def analytics_users():
    """User analytics"""
    try:
        active_users = Analytics.get_active_users()
        return render_template('analytics_users.html', users=active_users)
    except Exception as e:
        logger.error(f"Error loading user analytics: {e}")
        flash('Error loading user analytics.', 'error')
        return render_template('analytics_users.html', users=[])

@app.route('/analytics/friendships')
def analytics_friendships():
    """Friendship network analytics"""
    try:
        friendship_network = Analytics.get_friendship_network()
        return render_template('analytics_friendships.html', friendships=friendship_network)
    except Exception as e:
        logger.error(f"Error loading friendship analytics: {e}")
        flash('Error loading friendship analytics.', 'error')
        return render_template('analytics_friendships.html', friendships=[])

# API endpoints for AJAX requests
@app.route('/api/movie/<int:movie_id>/rating')
def api_movie_rating(movie_id):
    """API endpoint for movie rating stats"""
    try:
        stats = Analytics.get_movie_rating_stats(movie_id)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting movie rating stats: {e}")
        return jsonify({'error': 'Failed to get rating stats'}), 500

@app.route('/api/show/<int:show_id>/rating')
def api_show_rating(show_id):
    """API endpoint for show rating stats"""
    try:
        stats = Analytics.get_show_rating_stats(show_id)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting show rating stats: {e}")
        return jsonify({'error': 'Failed to get rating stats'}), 500

@app.route('/api/user/<int:user_id>/preferences')
@login_required
def api_user_preferences(user_id):
    """API endpoint for user preferences"""
    try:
        preferences = Genre.get_user_preferences(user_id)
        return jsonify(preferences)
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return jsonify({'error': 'Failed to get preferences'}), 500

@app.route('/admin/add_genre', methods=['GET', 'POST'])
@admin_required
def admin_add_genre():
    """Add a new genre (admin only)"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Genre name is required.', 'error')
            return redirect(url_for('admin_add_genre'))
        
        try:
            Genre.add_genre(name, description)
            flash(f'Genre "{name}" added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            logger.error(f"Error adding genre: {e}")
            flash('Error adding genre. Please try again.', 'error')
            return redirect(url_for('admin_add_genre'))
    
    return render_template('admin_add_genre.html')

@app.route('/admin/add_celebrity', methods=['GET', 'POST'])
@admin_required
def admin_add_celebrity():
    """Add a new celebrity (admin only)"""
    if request.method == 'POST':
        name = request.form.get('name')
        birth_year = request.form.get('birth_year')
        nationality = request.form.get('nationality')
        bio = request.form.get('bio')
        
        if not all([name, birth_year]):
            flash('Name and birth year are required.', 'error')
            return redirect(url_for('admin_add_celebrity'))
        
        try:
            birth_year = int(birth_year)
            Celebrity.add_celebrity(name, birth_year, nationality, bio)
            flash(f'Celebrity "{name}" added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            logger.error(f"Error adding celebrity: {e}")
            flash('Error adding celebrity. Please try again.', 'error')
            return redirect(url_for('admin_add_celebrity'))
    
    return render_template('admin_add_celebrity.html')

@app.route('/admin/add_production_company', methods=['GET', 'POST'])
@admin_required
def admin_add_production_company():
    """Add a new production company (admin only)"""
    if request.method == 'POST':
        name = request.form.get('name')
        founded_year = request.form.get('founded_year')
        country = request.form.get('country')
        description = request.form.get('description')
        
        if not name:
            flash('Company name is required.', 'error')
            return redirect(url_for('admin_add_production_company'))
        
        try:
            founded_year = int(founded_year) if founded_year else None
            ProductionCompany.add_company(name, founded_year, country, description)
            flash(f'Production company "{name}" added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            logger.error(f"Error adding production company: {e}")
            flash('Error adding production company. Please try again.', 'error')
            return redirect(url_for('admin_add_production_company'))
    
    return render_template('admin_add_production_company.html')

@app.route('/admin/populate_preferences', methods=['POST'])
@admin_required
def admin_populate_preferences():
    """Populate user preferences from existing reviews (admin only)"""
    try:
        Genre.populate_user_preferences()
        flash('User preferences populated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        logger.error(f"Error populating preferences: {e}")
        flash('Error populating preferences. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.connection.rollback()
    return render_template('500.html'), 500

# Template filters
@app.template_filter('datetime')
def datetime_filter(timestamp):
    """Format timestamp for display"""
    if timestamp:
        return timestamp.strftime('%Y-%m-%d %H:%M')
    return ''

@app.template_filter('date')
def date_filter(timestamp):
    """Format timestamp as date only"""
    if timestamp:
        return timestamp.strftime('%Y-%m-%d')
    return ''

if __name__ == '__main__':
    # Ensure database connection
    if db.connect():
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        logger.error("Failed to connect to database. Exiting.")
        exit(1)
