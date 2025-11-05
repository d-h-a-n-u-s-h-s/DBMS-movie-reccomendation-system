-- =============================================
-- MOVIE REVIEW SYSTEM - COMPLETE DATABASE SETUP
-- =============================================
-- This file contains the complete database schema with all fixes
-- Run this single file to set up everything

-- Create database
CREATE DATABASE IF NOT EXISTS movie_review_system;
USE movie_review_system;

-- =============================================
-- TABLES
-- =============================================

-- User table
CREATE TABLE User (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Age INT CHECK (Age >= 13 AND Age <= 120),
    Role ENUM('admin', 'verified_user', 'normal_user') NOT NULL DEFAULT 'normal_user',
    Email VARCHAR(255) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    Gender ENUM('M', 'F', 'Other'),
    verified_entity_type ENUM('company', 'celebrity') NULL,
    verified_entity_id INT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (Email),
    INDEX idx_role (Role),
    INDEX idx_created_at (Created_At)
);

-- Genre table
CREATE TABLE Genre (
    Genre_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) UNIQUE NOT NULL,
    Description TEXT,
    INDEX idx_name (Name)
);

-- Production Company table
CREATE TABLE Production_Company (
    Company_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Founded_Year INT,
    Country VARCHAR(50),
    Description TEXT,
    INDEX idx_name (Name)
);

-- Celebrity table
CREATE TABLE Celebrity (
    Celebrity_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Birth_Year INT,
    Nationality VARCHAR(50),
    Bio TEXT,
    INDEX idx_name (Name)
);

-- Movie table
CREATE TABLE Movie (
    Movie_ID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(200) NOT NULL,
    Description TEXT,
    Year INT CHECK (Year >= 1888 AND Year <= 2030),
    Length INT, -- in minutes
    Age_Rating VARCHAR(10),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_title (Title),
    INDEX idx_year (Year),
    INDEX idx_created_at (Created_At)
);

-- TV Show table
CREATE TABLE TV_Show (
    Show_ID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(200) NOT NULL,
    Description TEXT,
    Year INT CHECK (Year >= 1888 AND Year <= 2030),
    Seasons INT DEFAULT 1,
    Episodes INT,
    Age_Rating VARCHAR(10),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_title (Title),
    INDEX idx_year (Year),
    INDEX idx_created_at (Created_At)
);

-- Reviews table
CREATE TABLE Reviews (
    Review_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT NOT NULL,
    Score DECIMAL(3,1) CHECK (Score >= 1.0 AND Score <= 10.0),
    Title VARCHAR(200),
    Content TEXT,
    Movie_ID INT NULL,
    Show_ID INT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Movie_ID) REFERENCES Movie(Movie_ID) ON DELETE CASCADE,
    FOREIGN KEY (Show_ID) REFERENCES TV_Show(Show_ID) ON DELETE CASCADE,
    UNIQUE KEY unique_user_movie (User_ID, Movie_ID),
    UNIQUE KEY unique_user_show (User_ID, Show_ID),
    INDEX idx_score (Score),
    INDEX idx_created_at (Created_At),
    INDEX idx_movie_id (Movie_ID),
    INDEX idx_show_id (Show_ID)
);

-- Friends table
CREATE TABLE Friends (
    Friendship_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID1 INT NOT NULL,
    User_ID2 INT NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID1) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (User_ID2) REFERENCES User(User_ID) ON DELETE CASCADE,
    UNIQUE KEY unique_friendship (User_ID1, User_ID2),
    CHECK (User_ID1 != User_ID2),
    INDEX idx_user1 (User_ID1),
    INDEX idx_user2 (User_ID2),
    INDEX idx_created_at (Created_At)
);

-- Movie Genre junction table
CREATE TABLE Movie_Genre (
    Movie_ID INT NOT NULL,
    Genre_ID INT NOT NULL,
    PRIMARY KEY (Movie_ID, Genre_ID),
    FOREIGN KEY (Movie_ID) REFERENCES Movie(Movie_ID) ON DELETE CASCADE,
    FOREIGN KEY (Genre_ID) REFERENCES Genre(Genre_ID) ON DELETE CASCADE
);

-- Show Genre junction table
CREATE TABLE Show_Genre (
    Show_ID INT NOT NULL,
    Genre_ID INT NOT NULL,
    PRIMARY KEY (Show_ID, Genre_ID),
    FOREIGN KEY (Show_ID) REFERENCES TV_Show(Show_ID) ON DELETE CASCADE,
    FOREIGN KEY (Genre_ID) REFERENCES Genre(Genre_ID) ON DELETE CASCADE
);


-- Movie Celebrity junction table
CREATE TABLE Movie_Celebrity (
    Movie_ID INT NOT NULL,
    Celebrity_ID INT NOT NULL,
    Role VARCHAR(100) NOT NULL,
    PRIMARY KEY (Movie_ID, Celebrity_ID, Role),
    FOREIGN KEY (Movie_ID) REFERENCES Movie(Movie_ID) ON DELETE CASCADE,
    FOREIGN KEY (Celebrity_ID) REFERENCES Celebrity(Celebrity_ID) ON DELETE CASCADE
);

-- Movie Production Company junction table
CREATE TABLE Movie_Production (
    Movie_ID INT NOT NULL,
    Company_ID INT NOT NULL,
    Role VARCHAR(100) DEFAULT 'Producer',
    PRIMARY KEY (Movie_ID, Company_ID),
    FOREIGN KEY (Movie_ID) REFERENCES Movie(Movie_ID) ON DELETE CASCADE,
    FOREIGN KEY (Company_ID) REFERENCES Production_Company(Company_ID) ON DELETE CASCADE
);

-- Show Celebrity junction table
CREATE TABLE Show_Celebrity (
    Show_ID INT NOT NULL,
    Celebrity_ID INT NOT NULL,
    Role VARCHAR(100) NOT NULL,
    PRIMARY KEY (Show_ID, Celebrity_ID, Role),
    FOREIGN KEY (Show_ID) REFERENCES TV_Show(Show_ID) ON DELETE CASCADE,
    FOREIGN KEY (Celebrity_ID) REFERENCES Celebrity(Celebrity_ID) ON DELETE CASCADE
);

-- User Preferences table
CREATE TABLE User_Preferences (
    User_ID INT NOT NULL,
    Genre_ID INT NOT NULL,
    Preference_Score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    PRIMARY KEY (User_ID, Genre_ID),
    FOREIGN KEY (User_ID) REFERENCES User(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Genre_ID) REFERENCES Genre(Genre_ID) ON DELETE CASCADE,
    INDEX idx_preference_score (Preference_Score)
);

-- =============================================
-- STORED PROCEDURES
-- =============================================

DELIMITER //

-- Procedure to add a new user (FIXED VERSION)
CREATE PROCEDURE sp_add_user(
    IN p_name VARCHAR(100),
    IN p_age INT,
    IN p_role ENUM('admin', 'verified_user', 'normal_user'),
    IN p_email VARCHAR(255),
    IN p_password VARCHAR(255),
    IN p_gender ENUM('M', 'F', 'Other'),
    IN p_verified_entity_type VARCHAR(20),
    IN p_verified_entity_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Validate email format
    IF p_email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid email format';
    END IF;
    
    -- Validate age
    IF p_age < 13 OR p_age > 120 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Age must be between 13 and 120';
    END IF;
    
    -- Validate verified user requirements
    IF p_role = 'verified_user' AND (p_verified_entity_type IS NULL OR p_verified_entity_type = '' OR p_verified_entity_id IS NULL) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Verified users must specify entity type and ID';
    END IF;
    
    -- Convert empty strings to NULL
    IF p_verified_entity_type = '' THEN
        SET p_verified_entity_type = NULL;
    END IF;
    
    INSERT INTO User (Name, Age, Role, Email, PasswordHash, Gender, verified_entity_type, verified_entity_id)
    VALUES (p_name, p_age, p_role, p_email, p_password, p_gender, p_verified_entity_type, p_verified_entity_id);
    
    SELECT LAST_INSERT_ID() AS new_user_id;
    
    COMMIT;
END //

-- Procedure to add friendship
CREATE PROCEDURE sp_add_friendship(
    IN p_user1 INT,
    IN p_user2 INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Check if users exist
    IF NOT EXISTS (SELECT 1 FROM User WHERE User_ID = p_user1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User 1 does not exist';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM User WHERE User_ID = p_user2) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User 2 does not exist';
    END IF;
    
    -- Check if friendship already exists
    IF EXISTS (SELECT 1 FROM Friends WHERE (User_ID1 = p_user1 AND User_ID2 = p_user2) OR (User_ID1 = p_user2 AND User_ID2 = p_user1)) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Friendship already exists';
    END IF;
    
    -- Add friendship (ensure smaller ID is User_ID1)
    IF p_user1 < p_user2 THEN
        INSERT INTO Friends (User_ID1, User_ID2) VALUES (p_user1, p_user2);
    ELSE
        INSERT INTO Friends (User_ID1, User_ID2) VALUES (p_user2, p_user1);
    END IF;
    
    COMMIT;
END //

-- Procedure to add review
CREATE PROCEDURE sp_add_review(
    IN p_user_id INT,
    IN p_movie_id INT,
    IN p_show_id INT,
    IN p_score DECIMAL(3,1),
    IN p_title VARCHAR(200),
    IN p_content TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Validate user exists
    IF NOT EXISTS (SELECT 1 FROM User WHERE User_ID = p_user_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User does not exist';
    END IF;
    
    -- Validate content exists
    IF p_movie_id IS NULL AND p_show_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Must specify either movie or show';
    END IF;
    
    IF p_movie_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Movie WHERE Movie_ID = p_movie_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Movie does not exist';
    END IF;
    
    IF p_show_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM TV_Show WHERE Show_ID = p_show_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Show does not exist';
    END IF;
    
    -- Check if review already exists
    IF p_movie_id IS NOT NULL AND EXISTS (SELECT 1 FROM Reviews WHERE User_ID = p_user_id AND Movie_ID = p_movie_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Review for this movie already exists';
    END IF;
    
    IF p_show_id IS NOT NULL AND EXISTS (SELECT 1 FROM Reviews WHERE User_ID = p_user_id AND Show_ID = p_show_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Review for this show already exists';
    END IF;
    
    -- Insert review
    INSERT INTO Reviews (User_ID, Movie_ID, Show_ID, Score, Title, Content)
    VALUES (p_user_id, p_movie_id, p_show_id, p_score, p_title, p_content);
    
    COMMIT;
END //

-- Procedure to get movie recommendations
CREATE PROCEDURE sp_get_movie_recommendations(IN p_user_id INT)
BEGIN
    SELECT DISTINCT
        m.Movie_ID,
        m.Title,
        m.Description,
        m.Year,
        ROUND(AVG(r.Score), 2) as avg_rating,
        COUNT(r.Review_ID) as review_count,
        'Based on your preferences' as recommendation_reason
    FROM Movie m
    JOIN Movie_Genre mg ON m.Movie_ID = mg.Movie_ID
    JOIN User_Preferences up ON mg.Genre_ID = up.Genre_ID
    LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
    WHERE up.User_ID = p_user_id
        AND up.Preference_Score > 0
        AND NOT EXISTS (
            SELECT 1 FROM Reviews ur 
            WHERE ur.User_ID = p_user_id 
            AND ur.Movie_ID = m.Movie_ID
        )
    GROUP BY m.Movie_ID, m.Title, m.Description, m.Year
    HAVING avg_rating >= 7.0 OR avg_rating IS NULL
    ORDER BY avg_rating DESC, review_count DESC
    LIMIT 10;
END //

-- Procedure to get popular content
CREATE PROCEDURE sp_get_popular_content(IN p_limit INT)
BEGIN
    SELECT 
        'Movie' as content_type,
        m.Movie_ID as content_id,
        m.Title,
        m.Year,
        COUNT(r.Review_ID) as review_count,
        ROUND(AVG(r.Score), 2) as avg_rating
    FROM Movie m
    LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
    GROUP BY m.Movie_ID, m.Title, m.Year
    HAVING review_count > 0
    ORDER BY (COUNT(r.Review_ID) * AVG(r.Score)) DESC
    LIMIT p_limit;
END //

-- Procedure to get top rated content
CREATE PROCEDURE sp_get_top_rated_content(IN p_limit INT)
BEGIN
    SELECT 
        'Movie' as content_type,
        m.Movie_ID as content_id,
        m.Title,
        m.Year,
        COUNT(r.Review_ID) as review_count,
        ROUND(AVG(r.Score), 2) as avg_rating
    FROM Movie m
    LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
    GROUP BY m.Movie_ID, m.Title, m.Year
    HAVING review_count >= 3
    ORDER BY avg_rating DESC
    LIMIT p_limit;
END //

-- Procedure to get user statistics
CREATE PROCEDURE sp_get_user_stats(IN p_user_id INT)
BEGIN
    SELECT 
        u.Name,
        u.Email,
        u.Role,
        COUNT(DISTINCT r.Review_ID) as review_count,
        COUNT(DISTINCT f.Friendship_ID) as friend_count,
        ROUND(AVG(r.Score), 2) as avg_rating
    FROM User u
    LEFT JOIN Reviews r ON u.User_ID = r.User_ID
    LEFT JOIN Friends f ON u.User_ID = f.User_ID1 OR u.User_ID = f.User_ID2
    WHERE u.User_ID = p_user_id
    GROUP BY u.User_ID, u.Name, u.Email, u.Role;
END //

-- =============================================
-- ADMIN PROCEDURES
-- =============================================

-- Procedure: Add Genre
CREATE PROCEDURE sp_add_genre(
    IN p_name VARCHAR(100),
    IN p_description TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Check if genre already exists
    IF EXISTS (SELECT 1 FROM Genre WHERE Name = p_name) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Genre already exists';
    END IF;
    
    -- Insert new genre
    INSERT INTO Genre (Name, Description) 
    VALUES (p_name, p_description);
    
    -- Get the inserted genre ID
    SELECT Genre_ID, Name, Description 
    FROM Genre 
    WHERE Name = p_name;
    
    COMMIT;
END //

-- Procedure: Add Celebrity
CREATE PROCEDURE sp_add_celebrity(
    IN p_name VARCHAR(100),
    IN p_birth_year INT,
    IN p_nationality VARCHAR(50),
    IN p_bio TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Check if celebrity already exists (by name and birth year)
    IF EXISTS (SELECT 1 FROM Celebrity WHERE Name = p_name AND Birth_Year = p_birth_year) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Celebrity already exists with this name and birth year';
    END IF;
    
    -- Insert new celebrity
    INSERT INTO Celebrity (Name, Birth_Year, Nationality, Bio) 
    VALUES (p_name, p_birth_year, p_nationality, p_bio);
    
    -- Get the inserted celebrity ID
    SELECT Celebrity_ID, Name, Birth_Year, Nationality, Bio 
    FROM Celebrity 
    WHERE Name = p_name AND Birth_Year = p_birth_year;
    
    COMMIT;
END //

-- Procedure: Add Production Company
CREATE PROCEDURE sp_add_production_company(
    IN p_name VARCHAR(100),
    IN p_founded_year INT,
    IN p_country VARCHAR(50),
    IN p_description TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Check if production company already exists
    IF EXISTS (SELECT 1 FROM Production_Company WHERE Name = p_name) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Production company already exists';
    END IF;
    
    -- Insert new production company
    INSERT INTO Production_Company (Name, Founded_Year, Country, Description) 
    VALUES (p_name, p_founded_year, p_country, p_description);
    
    -- Get the inserted company ID
    SELECT Company_ID, Name, Founded_Year, Country, Description 
    FROM Production_Company 
    WHERE Name = p_name;
    
    COMMIT;
END //

-- Procedure: Update Movie with Celebrities and Production Companies
CREATE PROCEDURE sp_update_movie_with_details(
    IN p_movie_id INT,
    IN p_title VARCHAR(200),
    IN p_description TEXT,
    IN p_year INT,
    IN p_length INT,
    IN p_age_rating VARCHAR(10),
    IN p_genre_ids TEXT,
    IN p_celebrity_data TEXT,
    IN p_production_data TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Update movie basic info
    UPDATE Movie 
    SET Title = p_title, 
        Description = p_description, 
        Year = p_year, 
        Length = p_length, 
        Age_Rating = p_age_rating,
        Updated_At = CURRENT_TIMESTAMP
    WHERE Movie_ID = p_movie_id;
    
    -- Clear existing genres
    DELETE FROM Movie_Genre WHERE Movie_ID = p_movie_id;
    
    -- Add new genres (comma-separated IDs)
    IF p_genre_ids IS NOT NULL AND p_genre_ids != '' THEN
        SET @sql = CONCAT('INSERT INTO Movie_Genre (Movie_ID, Genre_ID) SELECT ', p_movie_id, ', Genre_ID FROM Genre WHERE Genre_ID IN (', p_genre_ids, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    -- Clear existing celebrities
    DELETE FROM Movie_Celebrity WHERE Movie_ID = p_movie_id;
    
    -- Add new celebrities (format: "celebrity_id:role,celebrity_id:role")
    IF p_celebrity_data IS NOT NULL AND p_celebrity_data != '' THEN
        SET @sql = CONCAT('INSERT INTO Movie_Celebrity (Movie_ID, Celebrity_ID, Role) VALUES ', p_celebrity_data);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    -- Clear existing production companies
    DELETE FROM Movie_Production WHERE Movie_ID = p_movie_id;
    
    -- Add new production companies (format: "company_id:role,company_id:role")
    IF p_production_data IS NOT NULL AND p_production_data != '' THEN
        SET @sql = CONCAT('INSERT INTO Movie_Production (Movie_ID, Company_ID, Role) VALUES ', p_production_data);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    COMMIT;
END //

-- Procedure: Create Movie with Celebrities and Production Companies
CREATE PROCEDURE sp_create_movie_with_details(
    IN p_title VARCHAR(200),
    IN p_description TEXT,
    IN p_year INT,
    IN p_length INT,
    IN p_age_rating VARCHAR(10),
    IN p_genre_ids TEXT,
    IN p_celebrity_data TEXT,
    IN p_production_data TEXT
)
BEGIN
    DECLARE v_movie_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Create movie
    INSERT INTO Movie (Title, Description, Year, Length, Age_Rating)
    VALUES (p_title, p_description, p_year, p_length, p_age_rating);
    
    SET v_movie_id = LAST_INSERT_ID();
    
    -- Add genres
    IF p_genre_ids IS NOT NULL AND p_genre_ids != '' THEN
        SET @sql = CONCAT('INSERT INTO Movie_Genre (Movie_ID, Genre_ID) SELECT ', v_movie_id, ', Genre_ID FROM Genre WHERE Genre_ID IN (', p_genre_ids, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    -- Add celebrities
    IF p_celebrity_data IS NOT NULL AND p_celebrity_data != '' THEN
        SET @sql = CONCAT('INSERT INTO Movie_Celebrity (Movie_ID, Celebrity_ID, Role) VALUES ', p_celebrity_data);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    -- Add production companies
    IF p_production_data IS NOT NULL AND p_production_data != '' THEN
        SET @sql = CONCAT('INSERT INTO Movie_Production (Movie_ID, Company_ID, Role) VALUES ', p_production_data);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
    
    SELECT v_movie_id as Movie_ID;
    COMMIT;
END //

-- Procedure: Populate User Preferences
CREATE PROCEDURE sp_populate_user_preferences()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_user_id INT;
    DECLARE v_movie_id INT;
    DECLARE v_show_id INT;
    DECLARE v_score DECIMAL(3,1);
    DECLARE v_genre_id INT;
    
    -- Cursor for movie reviews
    DECLARE movie_cursor CURSOR FOR
        SELECT r.User_ID, r.Movie_ID, r.Score, mg.Genre_ID
        FROM Reviews r
        JOIN Movie_Genre mg ON r.Movie_ID = mg.Movie_ID
        WHERE r.Movie_ID IS NOT NULL;
    
    -- Cursor for show reviews  
    DECLARE show_cursor CURSOR FOR
        SELECT r.User_ID, r.Show_ID, r.Score, sg.Genre_ID
        FROM Reviews r
        JOIN Show_Genre sg ON r.Show_ID = sg.Show_ID
        WHERE r.Show_ID IS NOT NULL;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Clear existing preferences
    DELETE FROM User_Preferences;
    
    -- Process movie reviews
    OPEN movie_cursor;
    movie_loop: LOOP
        FETCH movie_cursor INTO v_user_id, v_movie_id, v_score, v_genre_id;
        IF done THEN
            LEAVE movie_loop;
        END IF;
        
        -- Insert or update preference
        INSERT INTO User_Preferences (User_ID, Genre_ID, Preference_Score)
        VALUES (v_user_id, v_genre_id, v_score)
        ON DUPLICATE KEY UPDATE
        Preference_Score = (Preference_Score + v_score) / 2;
    END LOOP;
    CLOSE movie_cursor;
    
    -- Reset done flag for show cursor
    SET done = FALSE;
    
    -- Process show reviews
    OPEN show_cursor;
    show_loop: LOOP
        FETCH show_cursor INTO v_user_id, v_show_id, v_score, v_genre_id;
        IF done THEN
            LEAVE show_loop;
        END IF;
        
        -- Insert or update preference
        INSERT INTO User_Preferences (User_ID, Genre_ID, Preference_Score)
        VALUES (v_user_id, v_genre_id, v_score)
        ON DUPLICATE KEY UPDATE
        Preference_Score = (Preference_Score + v_score) / 2;
    END LOOP;
    CLOSE show_cursor;
    
    -- Show summary
    SELECT 
        COUNT(DISTINCT User_ID) as users_with_preferences,
        COUNT(*) as total_preference_entries,
        AVG(Preference_Score) as avg_preference_score
    FROM User_Preferences;
    
END //

-- Procedure: Get User Preferences Summary
CREATE PROCEDURE sp_get_user_preferences_summary(IN p_user_id INT)
BEGIN
    SELECT 
        g.Name as genre_name,
        up.Preference_Score,
        COUNT(r.Review_ID) as review_count,
        AVG(r.Score) as avg_rating
    FROM Genre g
    LEFT JOIN User_Preferences up ON g.Genre_ID = up.Genre_ID AND up.User_ID = p_user_id
    LEFT JOIN Reviews r ON r.User_ID = p_user_id 
        AND ((r.Movie_ID IS NOT NULL AND EXISTS (SELECT 1 FROM Movie_Genre mg WHERE mg.Movie_ID = r.Movie_ID AND mg.Genre_ID = g.Genre_ID))
             OR (r.Show_ID IS NOT NULL AND EXISTS (SELECT 1 FROM Show_Genre sg WHERE sg.Show_ID = r.Show_ID AND sg.Genre_ID = g.Genre_ID)))
    GROUP BY g.Genre_ID, g.Name, up.Preference_Score
    ORDER BY up.Preference_Score DESC, g.Name;
END //

DELIMITER ;

-- =============================================
-- FUNCTIONS
-- =============================================

DELIMITER //

-- Function to calculate average rating
CREATE FUNCTION fn_calculate_average_rating(p_content_id INT, p_content_type ENUM('movie', 'show'))
RETURNS DECIMAL(5,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE avg_rating DECIMAL(5,2) DEFAULT 0.0;
    
    IF p_content_type = 'movie' THEN
        SELECT AVG(Score) INTO avg_rating
        FROM Reviews
        WHERE Movie_ID = p_content_id;
    ELSE
        SELECT AVG(Score) INTO avg_rating
        FROM Reviews
        WHERE Show_ID = p_content_id;
    END IF;
    
    RETURN COALESCE(avg_rating, 0.0);
END //

-- Function to get user role
CREATE FUNCTION fn_get_user_role(p_user_id INT)
RETURNS VARCHAR(20)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE user_role VARCHAR(20) DEFAULT 'normal_user';
    
    SELECT Role INTO user_role
    FROM User
    WHERE User_ID = p_user_id;
    
    RETURN COALESCE(user_role, 'normal_user');
END //

-- Function to check if content is liked
CREATE FUNCTION fn_is_content_liked(p_user_id INT, p_content_id INT, p_content_type ENUM('movie', 'show'))
RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE is_liked BOOLEAN DEFAULT FALSE;
    DECLARE review_count INT DEFAULT 0;
    
    IF p_content_type = 'movie' THEN
        SELECT COUNT(*) INTO review_count
        FROM Reviews
        WHERE User_ID = p_user_id AND Movie_ID = p_content_id;
    ELSE
        SELECT COUNT(*) INTO review_count
        FROM Reviews
        WHERE User_ID = p_user_id AND Show_ID = p_content_id;
    END IF;
    
    SET is_liked = (review_count > 0);
    RETURN is_liked;
END //

-- Function to calculate user similarity
CREATE FUNCTION fn_calculate_user_similarity(p_user1 INT, p_user2 INT)
RETURNS DECIMAL(5,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE similarity DECIMAL(5,2) DEFAULT 0.0;
    DECLARE common_reviews INT DEFAULT 0;
    DECLARE total_reviews INT DEFAULT 0;
    
    -- Count common reviews
    SELECT COUNT(*) INTO common_reviews
    FROM Reviews r1
    JOIN Reviews r2 ON (r1.Movie_ID = r2.Movie_ID AND r1.Movie_ID IS NOT NULL) 
                   OR (r1.Show_ID = r2.Show_ID AND r1.Show_ID IS NOT NULL)
    WHERE r1.User_ID = p_user1 AND r2.User_ID = p_user2;
    
    -- Count total reviews for user1
    SELECT COUNT(*) INTO total_reviews
    FROM Reviews
    WHERE User_ID = p_user1;
    
    IF total_reviews > 0 THEN
        SET similarity = (common_reviews / total_reviews) * 100;
    END IF;
    
    RETURN similarity;
END //

-- Function to get movie popularity
CREATE FUNCTION fn_get_movie_popularity(p_movie_id INT)
RETURNS DECIMAL(8,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE popularity DECIMAL(8,2) DEFAULT 0.0;
    DECLARE avg_score DECIMAL(5,2) DEFAULT 0.0;
    DECLARE review_count INT DEFAULT 0;
    
    SELECT AVG(Score), COUNT(*) INTO avg_score, review_count
    FROM Reviews
    WHERE Movie_ID = p_movie_id;
    
    IF review_count > 0 THEN
        SET popularity = avg_score * LOG(review_count + 1);
    END IF;
    
    RETURN popularity;
END //

-- Function to get show popularity
CREATE FUNCTION fn_get_show_popularity(p_show_id INT)
RETURNS DECIMAL(8,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE popularity DECIMAL(8,2) DEFAULT 0.0;
    DECLARE avg_score DECIMAL(5,2) DEFAULT 0.0;
    DECLARE review_count INT DEFAULT 0;
    
    SELECT AVG(Score), COUNT(*) INTO avg_score, review_count
    FROM Reviews
    WHERE Show_ID = p_show_id;
    
    IF review_count > 0 THEN
        SET popularity = avg_score * LOG(review_count + 1);
    END IF;
    
    RETURN popularity;
END //

DELIMITER ;

-- =============================================
-- TRIGGERS
-- =============================================

DELIMITER //

-- Trigger to update average rating when review is added
CREATE TRIGGER tr_update_average_rating_after_insert
AFTER INSERT ON Reviews
FOR EACH ROW
BEGIN
    -- Update movie rating if applicable
    IF NEW.Movie_ID IS NOT NULL THEN
        UPDATE Movie m
        SET Updated_At = CURRENT_TIMESTAMP
        WHERE m.Movie_ID = NEW.Movie_ID;
    END IF;
    
    -- Update show rating if applicable
    IF NEW.Show_ID IS NOT NULL THEN
        UPDATE TV_Show s
        SET Updated_At = CURRENT_TIMESTAMP
        WHERE s.Show_ID = NEW.Show_ID;
    END IF;
END //

-- Trigger to validate review rating
CREATE TRIGGER tr_validate_review_rating
BEFORE INSERT ON Reviews
FOR EACH ROW
BEGIN
    IF NEW.Score < 1.0 OR NEW.Score > 10.0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rating must be between 1.0 and 10.0';
    END IF;
END //

-- Trigger to log user activity
CREATE TRIGGER tr_log_user_activity
AFTER INSERT ON Reviews
FOR EACH ROW
BEGIN
    -- This trigger can be extended to log user activities
    -- For now, it just updates the user's updated_at timestamp
    UPDATE User 
    SET Updated_At = CURRENT_TIMESTAMP 
    WHERE User_ID = NEW.User_ID;
END //

-- Trigger to update user preferences after review (SIMPLIFIED VERSION)
CREATE TRIGGER tr_update_user_preferences
AFTER INSERT ON Reviews
FOR EACH ROW
BEGIN
    -- Update preferences for movie genres
    IF NEW.Movie_ID IS NOT NULL THEN
        INSERT INTO User_Preferences (User_ID, Genre_ID, Preference_Score)
        SELECT NEW.User_ID, mg.Genre_ID, NEW.Score
        FROM Movie_Genre mg
        WHERE mg.Movie_ID = NEW.Movie_ID
        ON DUPLICATE KEY UPDATE
        Preference_Score = (Preference_Score + NEW.Score) / 2;
    END IF;
    
    -- Update preferences for show genres
    IF NEW.Show_ID IS NOT NULL THEN
        INSERT INTO User_Preferences (User_ID, Genre_ID, Preference_Score)
        SELECT NEW.User_ID, sg.Genre_ID, NEW.Score
        FROM Show_Genre sg
        WHERE sg.Show_ID = NEW.Show_ID
        ON DUPLICATE KEY UPDATE
        Preference_Score = (Preference_Score + NEW.Score) / 2;
    END IF;
END //

DELIMITER ;

-- =============================================
-- VIEWS
-- =============================================

-- View for popular movies with popularity score
CREATE VIEW vw_popular_movies AS
SELECT 
    m.Movie_ID,
    m.Title,
    m.Description,
    m.Year,
    m.Age_Rating,
    COUNT(r.Review_ID) as review_count,
    ROUND(AVG(r.Score), 2) as average_rating,
    fn_get_movie_popularity(m.Movie_ID) as popularity_score
FROM Movie m
LEFT JOIN Reviews r ON m.Movie_ID = r.Movie_ID
GROUP BY m.Movie_ID, m.Title, m.Description, m.Year, m.Age_Rating
ORDER BY popularity_score DESC;

-- View for top rated movies
CREATE VIEW vw_top_rated_movies AS
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
HAVING review_count >= 3
ORDER BY average_rating DESC;

-- View for top rated shows
CREATE VIEW vw_top_rated_shows AS
SELECT 
    s.Show_ID,
    s.Title,
    s.Description,
    s.Year,
    s.Age_Rating,
    COUNT(r.Review_ID) as review_count,
    ROUND(AVG(r.Score), 2) as average_rating
FROM TV_Show s
LEFT JOIN Reviews r ON s.Show_ID = r.Show_ID
GROUP BY s.Show_ID, s.Title, s.Description, s.Year, s.Age_Rating
HAVING review_count >= 3
ORDER BY average_rating DESC;

-- View for active users
CREATE VIEW vw_active_users AS
SELECT 
    u.User_ID,
    u.Name,
    u.Email,
    u.Role,
    COUNT(DISTINCT r.Review_ID) as review_count,
    COUNT(DISTINCT f.Friendship_ID) as friend_count,
    ROUND(AVG(r.Score), 2) as avg_rating,
    u.Created_At
FROM User u
LEFT JOIN Reviews r ON u.User_ID = r.User_ID
LEFT JOIN Friends f ON u.User_ID = f.User_ID1 OR u.User_ID = f.User_ID2
GROUP BY u.User_ID, u.Name, u.Email, u.Role, u.Created_At
ORDER BY review_count DESC, friend_count DESC;

-- View for friendship network
CREATE VIEW vw_friendship_network AS
SELECT 
    u1.Name as user_name,
    u2.Name as friend_name,
    fn_calculate_user_similarity(u1.User_ID, u2.User_ID) as similarity_score,
    f.Created_At as friendship_date
FROM Friends f
JOIN User u1 ON f.User_ID1 = u1.User_ID
JOIN User u2 ON f.User_ID2 = u2.User_ID
ORDER BY similarity_score DESC;

-- =============================================
-- SAMPLE DATA
-- =============================================

-- Insert genres
INSERT INTO Genre (Name, Description) VALUES
('Action', 'High-energy films with physical stunts and chases'),
('Comedy', 'Humorous films intended to entertain and amuse'),
('Drama', 'Serious, plot-driven presentations'),
('Horror', 'Films designed to frighten and unsettle'),
('Romance', 'Films focusing on love stories'),
('Sci-Fi', 'Science fiction films with futuristic concepts'),
('Thriller', 'Suspenseful films that keep audiences on edge'),
('Fantasy', 'Films with magical or supernatural elements'),
('Documentary', 'Non-fiction films documenting real events'),
('Animation', 'Films created using animation techniques');

-- Insert production companies
INSERT INTO Production_Company (Name, Founded_Year, Country, Description) VALUES
('Marvel Studios', 1993, 'USA', 'American film studio known for superhero films'),
('Warner Bros.', 1923, 'USA', 'Major American entertainment company'),
('Disney', 1923, 'USA', 'Multinational mass media and entertainment conglomerate'),
('Universal Pictures', 1912, 'USA', 'American film studio and distribution company'),
('Paramount Pictures', 1912, 'USA', 'American film and television production company');

-- Insert celebrities
INSERT INTO Celebrity (Name, Birth_Year, Nationality, Bio) VALUES
('Robert Downey Jr.', 1965, 'American', 'American actor known for Iron Man'),
('Christopher Nolan', 1970, 'British', 'British-American film director and producer'),
('Emma Stone', 1988, 'American', 'American actress and producer'),
('Ryan Reynolds', 1976, 'Canadian', 'Canadian actor, comedian, and producer'),
('Bryan Cranston', 1956, 'American', 'American actor, producer, and director');

-- Insert movies
INSERT INTO Movie (Title, Description, Year, Length, Age_Rating) VALUES
('Iron Man', 'A billionaire industrialist and genius inventor, Tony Stark, is conducting weapons tests overseas, but terrorists kidnap him to force him to build a devastating weapon.', 2008, 126, 'PG-13'),
('The Dark Knight', 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.', 2008, 152, 'PG-13'),
('Inception', 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.', 2010, 148, 'PG-13'),
('Deadpool', 'A wisecracking mercenary gets experimented on and becomes immortal but ugly, and sets out to track down the man who ruined his looks.', 2016, 108, 'R'),
('La La Land', 'While navigating their careers in Los Angeles, a pianist and an actress fall in love while attempting to reconcile their aspirations for the future.', 2016, 128, 'PG-13');

-- Insert TV shows
INSERT INTO TV_Show (Title, Description, Year, Seasons, Episodes, Age_Rating) VALUES
('Stranger Things', 'When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces, and one strange little girl.', 2016, 4, 34, 'TV-14'),
('The Office', 'A mockumentary on a group of typical office workers, where the workday consists of ego clashes, inappropriate behavior, and tedium.', 2005, 9, 201, 'TV-14'),
('Breaking Bad', 'A high school chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine in order to secure his family\'s future.', 2008, 5, 62, 'TV-MA');

-- Insert users
INSERT INTO User (Name, Age, Role, Email, PasswordHash, Gender) VALUES
('Admin User', 30, 'admin', 'admin@movieapp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'M'),
('John Doe', 25, 'normal_user', 'john@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'M'),
('Jane Smith', 28, 'verified_user', 'jane@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'F'),
('Mike Johnson', 32, 'normal_user', 'mike@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'M'),
('Sarah Wilson', 26, 'normal_user', 'sarah@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'F'),
('Tom Brown', 29, 'normal_user', 'tom@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'M'),
('Lisa Davis', 35, 'verified_user', 'lisa@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'F'),
('Chris Lee', 24, 'normal_user', 'chris@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4QqKqK2', 'M');

-- Insert movie genres
INSERT INTO Movie_Genre (Movie_ID, Genre_ID) VALUES
(1, 1), (1, 6), -- Iron Man: Action, Sci-Fi
(2, 1), (2, 3), -- The Dark Knight: Action, Drama
(3, 1), (3, 6), (3, 7), -- Inception: Action, Sci-Fi, Thriller
(4, 1), (4, 2), -- Deadpool: Action, Comedy
(5, 2), (5, 3), (5, 5); -- La La Land: Comedy, Drama, Romance

-- Insert show genres
INSERT INTO Show_Genre (Show_ID, Genre_ID) VALUES
(1, 6), (1, 7), (1, 3), -- Stranger Things: Sci-Fi, Thriller, Drama
(2, 2), (2, 3), -- The Office: Comedy, Drama
(3, 3), (3, 7); -- Breaking Bad: Drama, Thriller

-- Insert movie production companies
INSERT INTO Movie_Production (Movie_ID, Company_ID) VALUES
(1, 1), -- Iron Man: Marvel Studios
(2, 2), -- The Dark Knight: Warner Bros.
(3, 2), -- Inception: Warner Bros.
(4, 1), -- Deadpool: Marvel Studios
(5, 3); -- La La Land: Disney

-- Insert movie celebrities
INSERT INTO Movie_Celebrity (Movie_ID, Celebrity_ID, Role) VALUES
(1, 1, 'Actor'), -- Iron Man: Robert Downey Jr.
(2, 2, 'Director'), -- The Dark Knight: Christopher Nolan
(3, 2, 'Director'), -- Inception: Christopher Nolan
(4, 4, 'Actor'), -- Deadpool: Ryan Reynolds
(5, 3, 'Actor'); -- La La Land: Emma Stone

-- Insert friendships
INSERT INTO Friends (User_ID1, User_ID2) VALUES
(4, 5), -- John Doe and Jane Smith
(4, 6), -- John Doe and Mike Johnson
(5, 7), -- Jane Smith and Sarah Wilson
(6, 8); -- Mike Johnson and Tom Brown

-- Insert reviews
INSERT INTO Reviews (User_ID, Score, Title, Content, Movie_ID, Show_ID) VALUES
(4, 9.0, 'Amazing superhero film!', 'Robert Downey Jr. was perfect as Iron Man.', 1, NULL),
(5, 8.5, 'Great action movie', 'The effects were incredible.', 1, NULL),
(6, 9.5, 'Masterpiece', 'Christopher Nolan at his best.', 3, NULL),
(7, 8.0, 'Funny and action-packed', 'Ryan Reynolds was hilarious.', 4, NULL),
(8, 9.2, 'Beautiful musical', 'Emma Stone and Ryan Gosling were perfect.', 5, NULL),
(4, 8.8, 'Addictive series', 'Great characters and story.', NULL, 1),
(5, 9.0, 'Hilarious comedy', 'Steve Carell is brilliant.', NULL, 2),
(6, 9.5, 'Best TV show ever', 'Bryan Cranston is phenomenal.', NULL, 3);

-- =============================================
-- ADDITIONAL INDEXES
-- =============================================

CREATE INDEX idx_reviews_score ON Reviews(Score);
CREATE INDEX idx_reviews_created_at ON Reviews(Created_At);
CREATE INDEX idx_movie_year ON Movie(Year);
CREATE INDEX idx_show_year ON TV_Show(Year);
CREATE INDEX idx_user_preferences_score ON User_Preferences(Preference_Score);

-- =============================================
-- COMPLETE SETUP MESSAGE
-- =============================================

SELECT 'Movie Review Database Setup Complete!' as Status,
       'Database: movie_review_system' as Database_Name,
       (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'movie_review_system') as Table_Count,
       (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'movie_review_system' AND routine_type = 'PROCEDURE') as Procedure_Count,
       (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'movie_review_system' AND routine_type = 'FUNCTION') as Function_Count,
       (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'movie_review_system') as Trigger_Count,
       (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'movie_review_system') as View_Count;