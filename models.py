"""
Flask Models and Database Connection
Movie Review & Recommendation System
"""

import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self):
        self.connection = None
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'movie_review_system'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            # Check if .env file exists
            if not os.path.exists('.env'):
                logger.error("❌ .env file not found! Please create it with your database configuration.")
                logger.error("Run: python create_env.py")
                return False
            
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info("Successfully connected to MySQL database")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            if "Access denied" in str(e) and "using password: NO" in str(e):
                logger.error("❌ Password not loaded from .env file!")
                logger.error("Please check your .env file and run: python create_env.py")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")
    
    def get_cursor(self):
        """Get database cursor"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params)
            query_upper = query.strip().upper()
            if (query_upper.startswith('SELECT') or 
                query_upper.startswith('SHOW') or 
                query_upper.startswith('DESCRIBE') or
                query_upper.startswith('EXPLAIN')):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.rowcount
        except Error as e:
            logger.error(f"Database error: {e}")
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_procedure(self, procedure_name, params=None):
        """Execute a stored procedure"""
        cursor = self.get_cursor()
        try:
            if params:
                cursor.callproc(procedure_name, params)
            else:
                cursor.callproc(procedure_name)
            
            # Get results from all result sets
            results = []
            for result in cursor.stored_results():
                results.extend(result.fetchall())
            
            self.connection.commit()
            return results
        except Error as e:
            logger.error(f"Procedure error: {e}")
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

# Global database instance
db = DatabaseConnection()

class User:
    """User model"""
    
    @staticmethod
    def create_user(name, email, password, role='normal_user', age=None, gender=None, 
                   verified_entity_type=None, verified_entity_id=None):
        """Create a new user using stored procedure"""
        try:
            password_hash = generate_password_hash(password)
            results = db.execute_procedure('sp_add_user', [
                name, age, role, email, password_hash, gender, 
                verified_entity_type, verified_entity_id
            ])
            return results[0]['new_user_id'] if results else None
        except Error as e:
            logger.error(f"Error creating user: {e}")
            raise e
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        query = "SELECT * FROM User WHERE Email = %s"
        results = db.execute_query(query, (email,))
        return results[0] if results else None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        query = "SELECT * FROM User WHERE User_ID = %s"
        results = db.execute_query(query, (user_id,))
        return results[0] if results else None
    
    @staticmethod
    def verify_password(user, password):
        """Verify user password"""
        return check_password_hash(user['PasswordHash'], password)
    
    @staticmethod
    def get_user_stats(user_id):
        """Get user statistics"""
        query = """
        SELECT 
            (SELECT COUNT(*) FROM Reviews WHERE User_ID = %s) as review_count,
            (SELECT COUNT(*) FROM Friends WHERE User_ID1 = %s OR User_ID2 = %s) as friend_count,
            (SELECT ROUND(AVG(Score), 2) FROM Reviews WHERE User_ID = %s) as avg_score
        """
        results = db.execute_query(query, (user_id, user_id, user_id, user_id))
        return results[0] if results else None

class Movie:
    """Movie model"""
    
    @staticmethod
    def get_all_movies():
        """Get all movies with basic info"""
        query = """
        SELECT m.*, 
               COUNT(r.Review_ID) as review_count,
               ROUND(AVG(r.Score), 2) as avg_rating
        FROM Movie m
        LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
        GROUP BY m.Movie_ID
        ORDER BY m.Title
        """
        return db.execute_query(query)

    @staticmethod
    def get_movies_filtered(genre_id=None, search_query=None):
        """Get movies filtered by optional genre and/or title search"""
        base = [
            "SELECT m.*,",
            "       COUNT(r.Review_ID) as review_count,",
            "       ROUND(AVG(r.Score), 2) as avg_rating",
            "FROM Movie m",
            "LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID"
        ]

        params = []
        where_clauses = []

        if genre_id:
            base.append("JOIN Movie_Genre mg ON m.Movie_ID = mg.Movie_ID")
            where_clauses.append("mg.Genre_ID = %s")
            params.append(genre_id)

        if search_query:
            where_clauses.append("m.Title LIKE %s")
            params.append(f"%{search_query}%")

        query = "\n".join(base)
        if where_clauses:
            query += "\nWHERE " + " AND ".join(where_clauses)
        query += "\nGROUP BY m.Movie_ID\nORDER BY m.Title"

        return db.execute_query(query, tuple(params) if params else None)
    
    @staticmethod
    def get_movie_by_id(movie_id):
        """Get movie by ID with detailed info"""
        query = """
        SELECT m.*, 
               COUNT(r.Review_ID) as review_count,
               ROUND(AVG(r.Score), 2) as avg_rating,
               (COUNT(r.Review_ID) * 0.7 + AVG(r.Score) * 0.3) as popularity_score
        FROM Movie m
        LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
        WHERE m.Movie_ID = %s
        GROUP BY m.Movie_ID
        """
        results = db.execute_query(query, (movie_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_movie_genres(movie_id):
        """Get genres for a movie"""
        query = """
        SELECT g.* FROM Genre g
        JOIN Movie_Genre mg ON g.Genre_ID = mg.Genre_ID
        WHERE mg.Movie_ID = %s
        """
        return db.execute_query(query, (movie_id,))
    
    @staticmethod
    def get_movie_celebrities(movie_id):
        """Get celebrities for a movie"""
        query = """
        SELECT c.*, mc.Role FROM Celebrity c
        JOIN Movie_Celebrity mc ON c.Celebrity_ID = mc.Celebrity_ID
        WHERE mc.Movie_ID = %s
        """
        return db.execute_query(query, (movie_id,))
    
    @staticmethod
    def get_movie_production_companies(movie_id):
        """Get production companies for a movie"""
        query = """
        SELECT pc.*, mp.Role
        FROM Production_Company pc
        JOIN Movie_Production mp ON pc.Company_ID = mp.Company_ID
        WHERE mp.Movie_ID = %s
        """
        return db.execute_query(query, (movie_id,))
    
    @staticmethod
    def create_movie_with_details(title, description, year, length, age_rating, genre_ids=None, celebrity_data=None, production_data=None):
        """Create a new movie with genres, celebrities, and production companies"""
        try:
            # Convert lists to comma-separated strings
            genre_str = ','.join(map(str, genre_ids)) if genre_ids else None
            celebrity_str = celebrity_data if celebrity_data else None
            production_str = production_data if production_data else None
            
            results = db.execute_procedure('sp_create_movie_with_details', [
                title, description, year, length, age_rating,
                genre_str, celebrity_str, production_str
            ])
            return results[0]['Movie_ID'] if results else None
        except Error as e:
            logger.error(f"Error creating movie with details: {e}")
            raise e
    
    @staticmethod
    def update_movie_with_details(movie_id, title, description, year, length, age_rating, genre_ids=None, celebrity_data=None, production_data=None):
        """Update a movie with genres, celebrities, and production companies"""
        try:
            # Convert lists to comma-separated strings
            genre_str = ','.join(map(str, genre_ids)) if genre_ids else None
            celebrity_str = celebrity_data if celebrity_data else None
            production_str = production_data if production_data else None
            
            results = db.execute_procedure('sp_update_movie_with_details', [
                movie_id, title, description, year, length, age_rating,
                genre_str, celebrity_str, production_str
            ])
            return True
        except Error as e:
            logger.error(f"Error updating movie with details: {e}")
            raise e
    
    @staticmethod
    def get_movie_reviews(movie_id):
        """Get reviews for a movie"""
        query = """
        SELECT r.*, u.Name as user_name
        FROM Reviews r
        JOIN User u ON r.User_ID = u.User_ID
        WHERE r.Movie_ID = %s
        ORDER BY r.Created_At DESC
        """
        return db.execute_query(query, (movie_id,))
    
    @staticmethod
    def create_movie(title, description=None, year=None, length=None, age_rating=None):
        """Create a new movie"""
        try:
            query = """
            INSERT INTO Movie (Title, Description, Year, Length, Age_Rating)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor = db.get_cursor()
            cursor.execute(query, (title, description, year, length, age_rating))
            db.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Error creating movie: {e}")
            raise e
    
    @staticmethod
    def update_movie(movie_id, title, description=None, year=None, length=None, age_rating=None):
        """Update a movie"""
        try:
            query = """
            UPDATE Movie 
            SET Title = %s, Description = %s, Year = %s, Length = %s, Age_Rating = %s,
                Updated_At = CURRENT_TIMESTAMP
            WHERE Movie_ID = %s
            """
            result = db.execute_query(query, (title, description, year, length, age_rating, movie_id))
            return result is not None
        except Error as e:
            logger.error(f"Error updating movie: {e}")
            raise e
    
    @staticmethod
    def delete_movie(movie_id):
        """Delete a movie"""
        try:
            query = "DELETE FROM Movie WHERE Movie_ID = %s"
            result = db.execute_query(query, (movie_id,))
            return result is not None
        except Error as e:
            logger.error(f"Error deleting movie: {e}")
            raise e

class TVShow:
    """TV Show model"""
    
    @staticmethod
    def get_all_shows():
        """Get all shows with basic info"""
        query = """
        SELECT s.*, 
               COUNT(r.Review_ID) as review_count,
               ROUND(AVG(r.Score), 2) as avg_rating
        FROM TV_Show s
        LEFT JOIN Reviews r ON s.Show_ID = r.Show_ID
        GROUP BY s.Show_ID
        ORDER BY s.Title
        """
        return db.execute_query(query)

    @staticmethod
    def get_shows_filtered(genre_id=None, search_query=None):
        """Get TV shows filtered by optional genre and/or title search"""
        base = [
            "SELECT s.*,",
            "       COUNT(r.Review_ID) as review_count,",
            "       ROUND(AVG(r.Score), 2) as avg_rating",
            "FROM TV_Show s",
            "LEFT JOIN Reviews r ON s.Show_ID = r.Show_ID"
        ]

        params = []
        where_clauses = []

        if genre_id:
            base.append("JOIN Show_Genre sg ON s.Show_ID = sg.Show_ID")
            where_clauses.append("sg.Genre_ID = %s")
            params.append(genre_id)

        if search_query:
            where_clauses.append("s.Title LIKE %s")
            params.append(f"%{search_query}%")

        query = "\n".join(base)
        if where_clauses:
            query += "\nWHERE " + " AND ".join(where_clauses)
        query += "\nGROUP BY s.Show_ID\nORDER BY s.Title"

        return db.execute_query(query, tuple(params) if params else None)
    
    @staticmethod
    def get_show_by_id(show_id):
        """Get show by ID with detailed info"""
        query = """
        SELECT s.*, 
               COUNT(r.Review_ID) as review_count,
               ROUND(AVG(r.Score), 2) as avg_rating
        FROM TV_Show s
        LEFT JOIN Reviews r ON s.Show_ID = r.Show_ID
        WHERE s.Show_ID = %s
        GROUP BY s.Show_ID
        """
        results = db.execute_query(query, (show_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_show_genres(show_id):
        """Get genres for a show"""
        query = """
        SELECT g.* FROM Genre g
        JOIN Show_Genre sg ON g.Genre_ID = sg.Genre_ID
        WHERE sg.Show_ID = %s
        """
        return db.execute_query(query, (show_id,))
    
    @staticmethod
    def get_show_reviews(show_id):
        """Get reviews for a show"""
        query = """
        SELECT r.*, u.Name as user_name
        FROM Reviews r
        JOIN User u ON r.User_ID = u.User_ID
        WHERE r.Show_ID = %s
        ORDER BY r.Created_At DESC
        """
        return db.execute_query(query, (show_id,))
    
    @staticmethod
    def create_show(title, description=None, year=None, seasons=None, episodes=None, age_rating=None):
        """Create a new TV show"""
        try:
            query = """
            INSERT INTO TV_Show (Title, Description, Year, Seasons, Episodes, Age_Rating)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor = db.get_cursor()
            cursor.execute(query, (title, description, year, seasons, episodes, age_rating))
            db.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Error creating TV show: {e}")
            raise e
    
    @staticmethod
    def update_show(show_id, title, description=None, year=None, seasons=None, episodes=None, age_rating=None):
        """Update a TV show"""
        try:
            query = """
            UPDATE TV_Show 
            SET Title = %s, Description = %s, Year = %s, Seasons = %s, Episodes = %s, Age_Rating = %s,
                Updated_At = CURRENT_TIMESTAMP
            WHERE Show_ID = %s
            """
            result = db.execute_query(query, (title, description, year, seasons, episodes, age_rating, show_id))
            return result is not None
        except Error as e:
            logger.error(f"Error updating TV show: {e}")
            raise e
    
    @staticmethod
    def delete_show(show_id):
        """Delete a TV show"""
        try:
            query = "DELETE FROM TV_Show WHERE Show_ID = %s"
            result = db.execute_query(query, (show_id,))
            return result is not None
        except Error as e:
            logger.error(f"Error deleting TV show: {e}")
            raise e

class Review:
    """Review model"""
    
    @staticmethod
    def create_review(user_id, score, title, content, movie_id=None, show_id=None):
        """Create a new review using stored procedure"""
        try:
            results = db.execute_procedure('sp_add_review', [
                user_id, movie_id, show_id, score, title, content
            ])
            return True
        except Error as e:
            logger.error(f"Error creating review: {e}")
            raise e
    
    @staticmethod
    def get_user_reviews(user_id):
        """Get all reviews by a user"""
        query = """
        SELECT r.*, 
               m.Title as movie_title,
               s.Title as show_title
        FROM Reviews r
        LEFT JOIN Movie m ON r.Movie_ID = m.Movie_ID
        LEFT JOIN TV_Show s ON r.Show_ID = s.Show_ID
        WHERE r.User_ID = %s
        ORDER BY r.Created_At DESC
        """
        return db.execute_query(query, (user_id,))
    
    @staticmethod
    def get_recent_reviews(limit=10):
        """Get recent reviews"""
        query = """
        SELECT r.*, 
               u.Name as user_name,
               m.Title as movie_title,
               s.Title as show_title
        FROM Reviews r
        JOIN User u ON r.User_ID = u.User_ID
        LEFT JOIN Movie m ON r.Movie_ID = m.Movie_ID
        LEFT JOIN TV_Show s ON r.Show_ID = s.Show_ID
        ORDER BY r.Created_At DESC
        LIMIT %s
        """
        return db.execute_query(query, (limit,))
    
    @staticmethod
    def get_review_by_id(review_id):
        """Get a review by ID"""
        try:
            query = """
            SELECT r.*, 
                   m.Title as movie_title,
                   s.Title as show_title
            FROM Reviews r
            LEFT JOIN Movie m ON r.Movie_ID = m.Movie_ID
            LEFT JOIN TV_Show s ON r.Show_ID = s.Show_ID
            WHERE r.Review_ID = %s
            """
            results = db.execute_query(query, (review_id,))
            return results[0] if results else None
        except Error as e:
            logger.error(f"Error getting review by ID: {e}")
            raise e
    
    @staticmethod
    def update_review(review_id, score, title, content):
        """Update an existing review"""
        try:
            query = """
            UPDATE Reviews 
            SET Score = %s, Title = %s, Content = %s, Updated_At = NOW()
            WHERE Review_ID = %s
            """
            db.execute_query(query, (score, title, content, review_id))
            return True
        except Error as e:
            logger.error(f"Error updating review: {e}")
            raise e
    
    @staticmethod
    def delete_review(review_id):
        """Delete a review"""
        try:
            query = "DELETE FROM Reviews WHERE Review_ID = %s"
            db.execute_query(query, (review_id,))
            return True
        except Error as e:
            logger.error(f"Error deleting review: {e}")
            raise e

class Friendship:
    """Friendship model"""
    
    @staticmethod
    def add_friendship(user1_id, user2_id):
        """Add friendship using stored procedure"""
        try:
            results = db.execute_procedure('sp_add_friendship', [user1_id, user2_id])
            return True
        except Error as e:
            logger.error(f"Error adding friendship: {e}")
            raise e
    
    @staticmethod
    def remove_friendship(user1_id, user2_id):
        """Remove friendship"""
        try:
            query = """
            DELETE FROM Friends 
            WHERE (User_ID1 = %s AND User_ID2 = %s) 
               OR (User_ID1 = %s AND User_ID2 = %s)
            """
            result = db.execute_query(query, (user1_id, user2_id, user2_id, user1_id))
            return result > 0
        except Error as e:
            logger.error(f"Error removing friendship: {e}")
            raise e
    
    @staticmethod
    def get_user_friends(user_id):
        """Get user friends"""
        try:
            query = """
            SELECT u.User_ID, u.Name, u.Email, u.Age, u.Gender, u.Role, 
                   u.Created_At as user_created_at, u.Updated_At as user_updated_at,
                   f.Created_At as friendship_date
            FROM User u
            JOIN Friends f ON (u.User_ID = f.User_ID2 AND f.User_ID1 = %s)
                          OR (u.User_ID = f.User_ID1 AND f.User_ID2 = %s)
            ORDER BY f.Created_At DESC
            """
            results = db.execute_query(query, (user_id, user_id))
            return results
        except Error as e:
            logger.error(f"Error getting friends: {e}")
            raise e

    @staticmethod
    def get_user_friends_filtered(user_id, search_query=None):
        """Get user friends filtered by search on name or email"""
        try:
            where_like = ""
            params = [user_id, user_id]
            if search_query:
                where_like = " AND (u.Name LIKE %s OR u.Email LIKE %s)"
                like = f"%{search_query}%"
                params.extend([like, like])

            query = (
                "SELECT u.User_ID, u.Name, u.Email, u.Age, u.Gender, u.Role, "
                "       u.Created_At as user_created_at, u.Updated_At as user_updated_at, "
                "       f.Created_At as friendship_date "
                "FROM User u "
                "JOIN Friends f ON (u.User_ID = f.User_ID2 AND f.User_ID1 = %s) "
                "              OR (u.User_ID = f.User_ID1 AND f.User_ID2 = %s) "
                "WHERE 1=1" + where_like + " "
                "ORDER BY f.Created_At DESC"
            )

            return db.execute_query(query, tuple(params))
        except Error as e:
            logger.error(f"Error getting filtered friends: {e}")
            raise e
    
    @staticmethod
    def are_friends(user1_id, user2_id):
        """Check if users are friends"""
        query = """
        SELECT COUNT(*) as are_friends
        FROM Friends 
        WHERE (User_ID1 = %s AND User_ID2 = %s) 
           OR (User_ID1 = %s AND User_ID2 = %s)
        """
        results = db.execute_query(query, (user1_id, user2_id, user2_id, user1_id))
        return results[0]['are_friends'] > 0 if results else False

class Recommendation:
    """Recommendation model"""
    
    @staticmethod
    def get_movie_recommendations(user_id, limit=10):
        """Get movie recommendations"""
        try:
            query = """
            SELECT DISTINCT
                m.Movie_ID,
                m.Title,
                m.Description,
                m.Year,
                m.Length,
                m.Age_Rating,
                ROUND(AVG(r.Score), 2) as avg_rating,
                COUNT(r.Review_ID) as review_count,
                COALESCE(MAX(up.Preference_Score), 0) as max_preference_score
            FROM Movie m
            LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
            LEFT JOIN User_Preferences up ON up.Genre_ID IN (
                SELECT mg.Genre_ID FROM Movie_Genre mg WHERE mg.Movie_ID = m.Movie_ID
            ) AND up.User_ID = %s
            WHERE m.Movie_ID NOT IN (
                SELECT Movie_ID FROM Reviews WHERE User_ID = %s AND Movie_ID IS NOT NULL
            )
            GROUP BY m.Movie_ID, m.Title, m.Description, m.Year, m.Length, m.Age_Rating
            ORDER BY 
                max_preference_score DESC,
                AVG(r.Score) DESC,
                COUNT(r.Review_ID) DESC
            LIMIT %s
            """
            results = db.execute_query(query, (user_id, user_id, limit))
            return results
        except Error as e:
            logger.error(f"Error getting movie recommendations: {e}")
            raise e
    
    @staticmethod
    def get_friend_recommendations(user_id, limit=10):
        """Get friend recommendations based on friends' liked content (movies and shows)"""
        try:
            # Simplified query to avoid cursor issues
            query = """
            SELECT DISTINCT
                m.Movie_ID,
                m.Title,
                m.Description,
                m.Year,
                m.Length,
                m.Age_Rating,
                ROUND(AVG(r.Score), 2) as avg_rating,
                COUNT(r.Review_ID) as review_count,
                COUNT(DISTINCT CASE 
                    WHEN f.User_ID1 = %s THEN f.User_ID2 
                    WHEN f.User_ID2 = %s THEN f.User_ID1 
                END) as friend_likes,
                'movie' as content_type
            FROM Movie m
            JOIN Reviews r ON m.Movie_ID = r.Movie_ID
            JOIN Friends f ON (f.User_ID1 = %s AND f.User_ID2 = r.User_ID) 
                          OR (f.User_ID2 = %s AND f.User_ID1 = r.User_ID)
            WHERE m.Movie_ID NOT IN (
                SELECT Movie_ID FROM Reviews WHERE User_ID = %s AND Movie_ID IS NOT NULL
            )
            AND r.Score >= 7.0
            GROUP BY m.Movie_ID, m.Title, m.Description, m.Year, m.Length, m.Age_Rating
            ORDER BY friend_likes DESC, avg_rating DESC
            LIMIT %s
            """
            
            results = db.execute_query(query, (user_id, user_id, user_id, user_id, user_id, limit))
            return results
        except Error as e:
            logger.error(f"Error getting friend recommendations: {e}")
            raise e

class Genre:
    """Genre model"""
    
    @staticmethod
    def get_all_genres():
        """Get all genres"""
        query = "SELECT * FROM Genre ORDER BY Name"
        return db.execute_query(query)
    
    @staticmethod
    def add_genre(name, description):
        """Add a new genre using stored procedure"""
        try:
            results = db.execute_procedure('sp_add_genre', [
                name, description
            ])
            return results[0] if results else None
        except Error as e:
            logger.error(f"Error adding genre: {e}")
            raise e
    
    @staticmethod
    def get_user_preferences(user_id):
        """Get user genre preferences"""
        query = """
        SELECT g.*, up.Preference_Score
        FROM Genre g
        LEFT JOIN User_Preferences up ON g.Genre_ID = up.Genre_ID AND up.User_ID = %s
        ORDER BY up.Preference_Score DESC, g.Name
        """
        return db.execute_query(query, (user_id,))
    
    @staticmethod
    def populate_user_preferences():
        """Populate User_Preferences from existing reviews"""
        try:
            results = db.execute_procedure('sp_populate_user_preferences', [])
            return results
        except Error as e:
            logger.error(f"Error populating user preferences: {e}")
            raise e

class ProductionCompany:
    """Production Company model"""
    
    @staticmethod
    def get_all_companies():
        """Get all production companies"""
        query = "SELECT * FROM Production_Company ORDER BY Name"
        return db.execute_query(query)
    
    @staticmethod
    def get_company_by_id(company_id):
        """Get company by ID"""
        query = "SELECT * FROM Production_Company WHERE Company_ID = %s"
        results = db.execute_query(query, (company_id,))
        return results[0] if results else None
    
    @staticmethod
    def add_company(name, founded_year, country, description):
        """Add a new production company using stored procedure"""
        try:
            results = db.execute_procedure('sp_add_production_company', [
                name, founded_year, country, description
            ])
            return results[0] if results else None
        except Error as e:
            logger.error(f"Error adding production company: {e}")
            raise e

class Celebrity:
    """Celebrity model"""
    
    @staticmethod
    def get_all_celebrities():
        """Get all celebrities"""
        query = "SELECT * FROM Celebrity ORDER BY Name"
        return db.execute_query(query)
    
    @staticmethod
    def get_celebrity_by_id(celebrity_id):
        """Get celebrity by ID"""
        query = "SELECT * FROM Celebrity WHERE Celebrity_ID = %s"
        results = db.execute_query(query, (celebrity_id,))
        return results[0] if results else None
    
    @staticmethod
    def add_celebrity(name, birth_year, nationality, bio):
        """Add a new celebrity using stored procedure"""
        try:
            results = db.execute_procedure('sp_add_celebrity', [
                name, birth_year, nationality, bio
            ])
            return results[0] if results else None
        except Error as e:
            logger.error(f"Error adding celebrity: {e}")
            raise e

# Utility functions for views and analytics
class Analytics:
    """Analytics and view queries"""
    
    @staticmethod
    def get_popular_movies():
        """Get popular movies and shows - always use combined query"""
        try:
            # Use combined query to include both movies and shows
            query = """
                SELECT 
                    m.Movie_ID,
                    m.Title,
                    m.Description,
                    m.Year,
                    m.Age_Rating,
                    COUNT(r.Review_ID) as review_count,
                    ROUND(AVG(r.Score), 2) as average_rating,
                    (COUNT(r.Review_ID) * COALESCE(AVG(r.Score), 0)) as popularity_score,
                    'movie' as content_type
                FROM Movie m
                LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
                GROUP BY m.Movie_ID, m.Title, m.Description, m.Year, m.Age_Rating
                
                UNION ALL
                
                SELECT 
                    s.Show_ID as Movie_ID,
                    s.Title,
                    s.Description,
                    s.Year,
                    s.Age_Rating,
                    COUNT(r.Review_ID) as review_count,
                    ROUND(AVG(r.Score), 2) as average_rating,
                    (COUNT(r.Review_ID) * COALESCE(AVG(r.Score), 0)) as popularity_score,
                    'show' as content_type
                FROM TV_Show s
                LEFT JOIN Reviews r ON s.Show_ID = r.Show_ID
                GROUP BY s.Show_ID, s.Title, s.Description, s.Year, s.Age_Rating
                
                ORDER BY popularity_score DESC
                LIMIT 20
            """
            return db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting popular content: {e}")
            raise e
    
    @staticmethod
    def get_top_rated_movies():
        """Get top rated movies from view or fallback to direct query"""
        try:
            # Try view first
            query = "SELECT * FROM vw_top_rated_movies LIMIT 20"
            return db.execute_query(query)
        except Exception as e:
            logger.warning(f"View query failed, using fallback: {e}")
            # Fallback to direct query
            query = """
                SELECT 
                    m.Movie_ID,
                    m.Title,
                    m.Description,
                    m.Year,
                    m.Age_Rating,
                    COUNT(r.Review_ID) as review_count,
                    ROUND(AVG(r.Score), 2) as average_rating
                FROM Movie m
                LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
                GROUP BY m.Movie_ID, m.Title, m.Description, m.Year, m.Age_Rating
                HAVING review_count >= 1
                ORDER BY average_rating DESC
                LIMIT 20
            """
            return db.execute_query(query)
    
    @staticmethod
    def get_top_rated_shows():
        """Get top rated shows from view"""
        query = "SELECT * FROM vw_top_rated_shows LIMIT 20"
        return db.execute_query(query)
    
    @staticmethod
    def get_active_users():
        """Get active users from view"""
        query = "SELECT * FROM vw_active_users LIMIT 20"
        return db.execute_query(query)
    
    @staticmethod
    def get_friendship_network():
        """Get friendship network from view"""
        query = "SELECT * FROM vw_friendship_network ORDER BY similarity_score DESC LIMIT 50"
        return db.execute_query(query)
    
    @staticmethod
    def get_movie_rating_stats(movie_id):
        """Get movie rating statistics"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_reviews,
                ROUND(AVG(Score), 2) as average_rating,
                MIN(Score) as min_rating,
                MAX(Score) as max_rating,
                ROUND(STDDEV(Score), 2) as rating_stddev
            FROM Reviews 
            WHERE Movie_ID = %s
            """
            results = db.execute_query(query, (movie_id,))
            return results[0] if results else None
        except Error as e:
            logger.error(f"Error getting movie rating stats: {e}")
            raise e
    
    @staticmethod
    def get_show_rating_stats(show_id):
        """Get show rating statistics"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_reviews,
                ROUND(AVG(Score), 2) as average_rating,
                MIN(Score) as min_rating,
                MAX(Score) as max_rating,
                ROUND(STDDEV(Score), 2) as rating_stddev
            FROM Reviews 
            WHERE Show_ID = %s
            """
            results = db.execute_query(query, (show_id,))
            return results[0] if results else None
        except Error as e:
            logger.error(f"Error getting show rating stats: {e}")
            raise e

# Role-based access control decorators
def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        user = User.get_user_by_id(session['user_id'])
        if not user or user['Role'] != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function

def verified_user_required(f):
    """Require verified user or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        user = User.get_user_by_id(session['user_id'])
        if not user or user['Role'] not in ['verified_user', 'admin']:
            flash('Verified user access required.', 'error')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function

def can_edit_content(content_owner_type, content_owner_id):
    """Check if current user can edit content"""
    if 'user_id' not in session:
        return False
    
    user = User.get_user_by_id(session['user_id'])
    if not user:
        return False
    
    # Admin can edit everything
    if user['Role'] == 'admin':
        return True
    
    # Verified users can edit their own content
    if user['Role'] == 'verified_user':
        if content_owner_type == 'company' and user['verified_entity_type'] == 'company':
            return user['verified_entity_id'] == content_owner_id
        elif content_owner_type == 'celebrity' and user['verified_entity_type'] == 'celebrity':
            return user['verified_entity_id'] == content_owner_id
    
    return False
