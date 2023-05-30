CREATE DATABASE dev_db; -- База данных для разработки
CREATE DATABASE prod_db; -- База данных для продакшена

-- Подключение к базе данных dev_db
\c dev_db;

CREATE TABLE urls (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Подключение к базе данных prod_db
\c prod_db;

CREATE TABLE urls (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
