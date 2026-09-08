-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Roles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Locations
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL
);

-- Rainfall Observations
CREATE TABLE IF NOT EXISTS rainfall_observations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    source VARCHAR(50) NOT NULL,
    data_state VARCHAR(20) NOT NULL
);

-- Flood Assessments
CREATE TABLE IF NOT EXISTS flood_assessments (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    factors JSONB,
    model_version VARCHAR(50),
    data_state VARCHAR(20) NOT NULL
);
