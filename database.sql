DROP TABLE if exists urls;

---- Подключение к базе данных dev_db
--\c dev_db;

CREATE TABLE urls (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE url_checks (
    id SERIAL PRIMARY KEY,
    url_id INT,
    status_code INT,
    h1 TEXT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);