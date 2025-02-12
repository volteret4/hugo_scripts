-- Tabla principal de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL
);

-- Tabla principal de artistas
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    mbid TEXT,
    UNIQUE(name, mbid)
);

-- Tabla principal de álbumes
CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    artist_id INTEGER,
    mbid TEXT,
    image_url TEXT,
    FOREIGN KEY (artist_id) REFERENCES artists(id),
    UNIQUE(name, artist_id)
);

-- Tabla principal de canciones
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    artist_id INTEGER,
    album_id INTEGER,
    mbid TEXT,
    duration INTEGER,
    url TEXT,
    FOREIGN KEY (artist_id) REFERENCES artists(id),
    FOREIGN KEY (album_id) REFERENCES albums(id),
    UNIQUE(name, artist_id, album_id)
);

-- Tabla de fuentes de géneros
CREATE TABLE IF NOT EXISTS genre_sources (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Tabla de géneros
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    source_id INTEGER,
    FOREIGN KEY (source_id) REFERENCES genre_sources(id),
    UNIQUE(name, source_id)
);

-- Tabla de reproducción de usuarios (historial detallado)
CREATE TABLE IF NOT EXISTS user_plays (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    track_id INTEGER,
    timestamp INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- Tabla de relación entre canciones y géneros
CREATE TABLE IF NOT EXISTS track_genres (
    track_id INTEGER,
    genre_id INTEGER,
    confidence FLOAT,
    PRIMARY KEY (track_id, genre_id),
    FOREIGN KEY (track_id) REFERENCES tracks(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- Tabla de estadísticas de escucha por usuario y artista
CREATE TABLE IF NOT EXISTS user_artist_stats (
    user_id INTEGER,
    artist_id INTEGER,
    play_count INTEGER DEFAULT 0,
    first_played INTEGER,
    last_played INTEGER,
    PRIMARY KEY (user_id, artist_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (artist_id) REFERENCES artists(id)
);

-- Tabla de estadísticas de escucha por usuario y álbum
CREATE TABLE IF NOT EXISTS user_album_stats (
    user_id INTEGER,
    album_id INTEGER,
    play_count INTEGER DEFAULT 0,
    first_played INTEGER,
    last_played INTEGER,
    PRIMARY KEY (user_id, album_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (album_id) REFERENCES albums(id)
);

-- Tabla de estadísticas de escucha por usuario y canción
CREATE TABLE IF NOT EXISTS user_track_stats (
    user_id INTEGER,
    track_id INTEGER,
    play_count INTEGER DEFAULT 0,
    first_played INTEGER,
    last_played INTEGER,
    PRIMARY KEY (user_id, track_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- Tabla de estadísticas de escucha por usuario y género
CREATE TABLE IF NOT EXISTS user_genre_stats (
    user_id INTEGER,
    genre_id INTEGER,
    play_count INTEGER DEFAULT 0,
    first_played INTEGER,
    last_played INTEGER,
    PRIMARY KEY (user_id, genre_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- Vistas útiles para análisis

-- Vista de coincidencias de artistas entre usuarios
CREATE VIEW IF NOT EXISTS artist_user_overlap AS
SELECT 
    u1.username as user1,
    u2.username as user2,
    a.name as artist_name,
    uas1.play_count as user1_plays,
    uas2.play_count as user2_plays
FROM user_artist_stats uas1
JOIN user_artist_stats uas2 ON uas1.artist_id = uas2.artist_id
JOIN users u1 ON uas1.user_id = u1.id
JOIN users u2 ON uas2.user_id = u2.id
JOIN artists a ON uas1.artist_id = a.id
WHERE uas1.user_id < uas2.user_id;

-- Vista de coincidencias de géneros entre usuarios
CREATE VIEW IF NOT EXISTS genre_user_overlap AS
SELECT 
    u1.username as user1,
    u2.username as user2,
    g.name as genre_name,
    ugs1.play_count as user1_plays,
    ugs2.play_count as user2_plays
FROM user_genre_stats ugs1
JOIN user_genre_stats ugs2 ON ugs1.genre_id = ugs2.genre_id
JOIN users u1 ON ugs1.user_id = u1.id
JOIN users u2 ON ugs2.user_id = u2.id
JOIN genres g ON ugs1.genre_id = g.id
WHERE ugs1.user_id < ugs2.user_id;

-- Vista de top géneros por usuario
CREATE VIEW IF NOT EXISTS user_top_genres AS
SELECT 
    u.username,
    g.name as genre_name,
    ugs.play_count,
    gs.name as source
FROM user_genre_stats ugs
JOIN users u ON ugs.user_id = u.id
JOIN genres g ON ugs.genre_id = g.id
JOIN genre_sources gs ON g.source_id = gs.id;

-- Insertar fuentes de géneros
INSERT OR IGNORE INTO genre_sources (name) VALUES 
    ('lastfm'),
    ('spotify'),
    ('musicbrainz'),
    ('discogs_genre'),
    ('discogs_style');

-- Índices para optimizar consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_user_plays_user ON user_plays(user_id);
CREATE INDEX IF NOT EXISTS idx_user_plays_track ON user_plays(track_id);
CREATE INDEX IF NOT EXISTS idx_user_plays_timestamp ON user_plays(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_plays_year ON user_plays(year);
CREATE INDEX IF NOT EXISTS idx_track_genres_track ON track_genres(track_id);
CREATE INDEX IF NOT EXISTS idx_track_genres_genre ON track_genres(genre_id);
