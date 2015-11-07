BEGIN TRANSACTION;
CREATE TABLE `tag` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`name`	TEXT UNIQUE
);
INSERT INTO `tag` VALUES (1,'Action'),
 (2,'Adventure'),
 (3,'Animation'),
 (4,'Biography'),
 (5,'Comedy'),
 (6,'Crime'),
 (7,'Documentary'),
 (8,'Drama'),
 (9,'Family'),
 (10,'Fantasy'),
 (11,'Film-Noir'),
 (12,'History'),
 (13,'Horror'),
 (14,'Music'),
 (15,'Musical'),
 (16,'Mystery'),
 (17,'Romance'),
 (18,'Sci-Fi'),
 (19,'Sport'),
 (20,'Thriller'),
 (21,'War'),
 (22,'Western');
CREATE TABLE "series_tag" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`series_id`	INTEGER NOT NULL,
	`tag_id`	INTEGER NOT NULL
);
CREATE TABLE "series" (
	`id`	INTEGER NOT NULL UNIQUE,
	`name`	TEXT NOT NULL,
	`rating`	REAL,
	`synopsis`	TEXT,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
CREATE TABLE "season" (
	`id`	INTEGER NOT NULL UNIQUE,
	`series_id`	INTEGER,
	`number`	INTEGER,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
CREATE TABLE `person_history` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`person_id`	INTEGER NOT NULL,
	`entity_type`	TEXT NOT NULL,
	`entity_id`	INTEGER NOT NULL,
	`play_position`	INTEGER NOT NULL DEFAULT 0,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE `person` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`name`	TEXT NOT NULL,
	`password`	TEXT,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "movie_tag" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`movie_id`	INTEGER NOT NULL,
	`tag_id`	INTEGER NOT NULL
);
CREATE TABLE `movie_magnet` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`movie_id`	INTEGER NOT NULL,
	`magnet_id`	INTEGER NOT NULL,
	`quality`	INTEGER NOT NULL,
	`filename`	TEXT NOT NULL
);
CREATE TABLE "movie" (
	`id`	INTEGER NOT NULL UNIQUE,
	`name`	TEXT NOT NULL,
	`release_year`	INTEGER,
	`seconds_long`	INTEGER,
	`rating`	REAL,
	`synopsis`	TEXT,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
CREATE TABLE "magnet" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`btih`	TEXT NOT NULL UNIQUE,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE `episode_magnet` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`episode_id`	INTEGER NOT NULL,
	`magnet_id`	INTEGER NOT NULL,
	`quality`	INTEGER NOT NULL,
	`filename`	TEXT NOT NULL
);
CREATE TABLE "episode" (
	`id`	INTEGER NOT NULL UNIQUE,
	`season_id`	INTEGER NOT NULL,
	`number`	INTEGER NOT NULL,
	`release_date`	TEXT,
	`seconds_long`	INTEGER,
	`rating`	REAL,
	`synopsis`	TEXT,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
COMMIT;
