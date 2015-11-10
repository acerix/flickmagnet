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
CREATE TABLE "person_history" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`person_id`	INTEGER NOT NULL,
	`entity_type_id`	INTEGER NOT NULL,
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
INSERT INTO `movie_tag` VALUES (1,16544,5),
 (2,16544,9),
 (3,16544,10);
CREATE TABLE "movie" (
	`id`	INTEGER NOT NULL UNIQUE,
	`name`	TEXT NOT NULL,
	`release_year`	INTEGER,
	`seconds_long`	INTEGER,
	`rating`	REAL,
	`synopsis`	TEXT,
	`status_id`	INTEGER NOT NULL DEFAULT 1,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
INSERT INTO `movie` VALUES (16544,'The Wizard of Oz',1925,4860,5.3,'Dorothy, heir to the Oz throne, must take it back from the wicked Prime Minister Kruel with the help of three farmhands.',51,'2015-10-26 23:52:07');
CREATE TABLE "magnet_file_status" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`name`	TEXT NOT NULL UNIQUE
);
INSERT INTO `magnet_file_status` VALUES (1,'new'),
 (11,'start watching'),
 (12,'stop watching'),
 (13,'delete'),
 (21,'ready'),
 (22,'watching'),
 (23,'downloading'),
 (31,'seeding');
CREATE TABLE "magnet_file" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`entity_type_id`	INTEGER NOT NULL,
	`entity_id`	INTEGER NOT NULL,
	`magnet_id`	INTEGER NOT NULL,
	`person_id`	INTEGER NOT NULL,
	`quality`	INTEGER NOT NULL,
	`filename`	TEXT NOT NULL,
	`status_id`	INTEGER NOT NULL DEFAULT 1,
	`stream_position`	INTEGER NOT NULL DEFAULT 0,
	`download_score`	INTEGER NOT NULL DEFAULT 0,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`streamed`	TEXT
);
INSERT INTO `magnet_file` VALUES (1,2,16544,1,0,720,'The.Wizard.of.Oz.1939.70th.Anniversary.Ultimate.Collector''s.Edition.720p.BluRay.x264.AAC-ETRG/The.Wizard.of.Oz.1939.720p.BluRay.x264.AAC-ETRG.mp4',1,0,0,'2015-11-01 00:00:00',NULL);
CREATE TABLE "magnet" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`btih`	TEXT NOT NULL UNIQUE,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO `magnet` VALUES (1,'2C5B66C74D89F4081FED14C5A75C5F062A514EBF','2015-11-01 00:00:00');
CREATE TABLE "episode" (
	`id`	INTEGER NOT NULL UNIQUE,
	`season_id`	INTEGER NOT NULL,
	`number`	INTEGER NOT NULL,
	`release_date`	TEXT,
	`seconds_long`	INTEGER,
	`rating`	REAL,
	`synopsis`	TEXT,
	`status_id`	INTEGER NOT NULL DEFAULT 1,
	`added`	TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(id)
);
CREATE TABLE `entity_type` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`name`	TEXT NOT NULL UNIQUE
);
INSERT INTO `entity_type` VALUES (1,'episode'),
 (2,'movie'),
 (3,'song');
CREATE TABLE "entity_status" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`name`	TEXT NOT NULL UNIQUE
);
INSERT INTO `entity_status` VALUES (1,'new'),
 (51,'magnetized'),
 (52,'unavailable');
COMMIT;
