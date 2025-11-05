# SQL invocation examples: procedures, functions, and triggers

Use these examples to quickly call your stored procedures, SQL functions, and to exercise triggers in the `movie_review_system` database.

Note: Run this first in your SQL session:

```sql
USE movie_review_system;
```

## Stored procedures

### Create data

Add a user (expects a pre-hashed password):

```sql
CALL sp_add_user(
  'Alice Example',
  27,
  'normal_user',
  'alice@example.com',
  '$2b$12$exampleHashValueForDemoOnlyabcdefghijklmno',
  'F',
  NULL,
  NULL
);
```

Add a friendship (IDs must exist):

```sql
CALL sp_add_friendship(4, 5);
```

Add a review for a movie (fires triggers):

```sql
CALL sp_add_review(
  4,          -- p_user_id
  1,          -- p_movie_id
  NULL,       -- p_show_id
  8.7,        -- p_score (1.0..10.0)
  'Solid',    -- p_title
  'Enjoyed it'
);
```

Add a review for a TV show (fires triggers):

```sql
CALL sp_add_review(5, NULL, 1, 9.1, 'Great binge', 'Loved the cast');
```

Add reference data:

```sql
CALL sp_add_genre('Mystery', 'Whodunit and intrigue');
CALL sp_add_celebrity('Sample Star', 1990, 'American', 'Bio goes here');
CALL sp_add_production_company('Sample Studios', 2000, 'USA', 'Indie house');
```

Populate user preferences from existing reviews:

```sql
CALL sp_populate_user_preferences();
```

User preferences summary for a user:

```sql
CALL sp_get_user_preferences_summary(4);
```

Recommendations and analytics snapshots:

```sql
CALL sp_get_movie_recommendations(4);
CALL sp_get_popular_content(10);
CALL sp_get_top_rated_content(10);
```

Update/create movie with related data (minimal examples using only genres; celebrities/production can be left NULL):

```sql
-- Update existing movie (id 1) with genres 1,2
CALL sp_update_movie_with_details(
  1,
  'Updated Title',
  'Updated description',
  2010,
  120,
  'PG-13',
  '1,2',          -- p_genre_ids
  NULL,           -- p_celebrity_data (see notes)
  NULL            -- p_production_data (see notes)
);

-- Create a new movie with genres 1,3
CALL sp_create_movie_with_details(
  'New Movie',
  'Description here',
  2023,
  110,
  'PG-13',
  '1,3',
  NULL,
  NULL
);
```

Notes on celebrities/production parameters: The procedures expect dynamic SQL value lists for `(Movie_ID, Celebrity_ID, Role)` and `(Movie_ID, Company_ID, Role)` respectively when provided. If not needed, pass `NULL`.

## SQL functions

Average rating for content:

```sql
SELECT fn_calculate_average_rating(1, 'movie') AS avg_movie_rating;
SELECT fn_calculate_average_rating(1, 'show')  AS avg_show_rating;
```

User role lookup:

```sql
SELECT fn_get_user_role(4) AS user_role;
```

Did a user review specific content:

```sql
SELECT fn_is_content_liked(4, 1, 'movie') AS liked_movie;
SELECT fn_is_content_liked(4, 1, 'show')  AS liked_show;
```

User similarity score:

```sql
SELECT fn_calculate_user_similarity(4, 5) AS similarity_pct;
```

Popularity scores:

```sql
SELECT fn_get_movie_popularity(1) AS movie_popularity;
SELECT fn_get_show_popularity(1)  AS show_popularity;
```

## Triggers (how to exercise and verify)

These triggers run automatically on insert into `Reviews`:

- `tr_validate_review_rating` (BEFORE INSERT): ensures `Score` is between 1.0 and 10.0.
- `tr_update_average_rating_after_insert` (AFTER INSERT): bumps `Updated_At` on Movie/TV_Show.
- `tr_log_user_activity` (AFTER INSERT): updates `User.Updated_At`.
- `tr_update_user_preferences` (AFTER INSERT): upserts into `User_Preferences` for relevant genres.

Attempt an invalid review (should error):

```sql
INSERT INTO Reviews (User_ID, Movie_ID, Score, Title, Content)
VALUES (4, 1, 0.5, 'Too low', 'This should fail');
-- Expect: ERROR: Rating must be between 1.0 and 10.0
```

Insert a valid review to trigger updates:

```sql
INSERT INTO Reviews (User_ID, Movie_ID, Score, Title, Content)
VALUES (4, 1, 9.0, 'Great', 'Enjoyed it a lot');
```

Verify timestamps updated on movie and user:

```sql
SELECT Movie_ID, Title, Updated_At FROM Movie WHERE Movie_ID = 1;
SELECT User_ID, Name, Updated_At FROM User WHERE User_ID = 4;
```

Verify user preferences updated for the movie’s genres:

```sql
SELECT *
FROM User_Preferences
WHERE User_ID = 4
ORDER BY Preference_Score DESC, Genre_ID;
```

Tip: To test show-related triggers, use `Show_ID` instead of `Movie_ID` in the review insert.
