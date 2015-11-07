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
INSERT INTO `series_tag` VALUES (1,96697,3),
 (2,96697,5);
CREATE TABLE "series" (
	`id`	INTEGER NOT NULL UNIQUE,
	`name`	TEXT NOT NULL,
	`rating`	REAL,
	`synopsis`	TEXT,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
INSERT INTO `series` VALUES (96697,'The Simpsons',8.9,'The satiric adventures of a working-class family in the misfit city of Springfield.','2015-10-15 02:06:14');
CREATE TABLE "season" (
	`id`	INTEGER NOT NULL UNIQUE,
	`series_id`	INTEGER,
	`number`	INTEGER,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
INSERT INTO `season` VALUES (1,96697,1,'');
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
INSERT INTO `movie_tag` VALUES (1,111161,6),
 (2,111161,8);
CREATE TABLE `movie_magnet` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`movie_id`	INTEGER NOT NULL,
	`magnet_id`	INTEGER NOT NULL,
	`quality`	INTEGER NOT NULL,
	`filename`	TEXT NOT NULL
);
INSERT INTO `movie_magnet` VALUES (1,111161,2,720,'www.TamilRockers.com - The Shawshank Redemption (1994) 720p BDRip [Tamil + Eng + Hindi]/www.TamilRockers.com - The Shawshank Redemption (1994) 720p BDRip [Tamil + Eng + Hindi].mkv'),
 (2,111161,3,1080,'The Shawshank Redemption (1994) 1080p/The.Shawshank.Redemption.1994.1080p.mp4');
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
INSERT INTO `movie` VALUES (111161,'The Shawshank Redemption',1994,8520,9.3,'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.','');
CREATE TABLE "magnet" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`btih`	TEXT NOT NULL UNIQUE,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO `magnet` VALUES (1,'B3D81EE368807FEAFCFD9FA1E1E7D5AD6291F2D1',''),
 (2,'AE763414E6BD81497814894EA1545E1AA120A795',''),
 (3,'C0DCDBF9C7EDA92E783DE835600F7AD6A2328DAA','');
CREATE TABLE `episode_magnet` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`episode_id`	INTEGER NOT NULL,
	`magnet_id`	INTEGER NOT NULL,
	`quality`	INTEGER NOT NULL,
	`filename`	TEXT NOT NULL
);
INSERT INTO `episode_magnet` VALUES (1,348034,1,480,'The Simpsons Season 1 Complete 480p HDTV x265 - BrB/The Simpsons S01E01 480p HDTV x265 - BrB.mkv');
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
INSERT INTO `episode` VALUES (348034,1,1,'1990-11-18',1800,7.7,'Christmas seems doomed for the Simpson family when Homer receives no holiday bonus. Hoping to make extra money, he becomes a mall Santa Claus in an attempt to bring the family a happy holiday.','');
COMMIT;
