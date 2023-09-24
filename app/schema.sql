CREATE TABLE IF NOT EXISTS users (
    uid UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL CHECK (LENGTH(username) BETWEEN 14 AND 100),
    password TEXT NOT NULL CHECK (LENGTH(password) = 102),
    verification_code TEXT NOT NULL CHECK (LENGTH(verification_code) = 102),
    admin BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    disabled BOOLEAN DEFAULT FALSE,
    created INT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    locked INT
);

CREATE TABLE IF NOT EXISTS auth_events (
    event_id SERIAL PRIMARY KEY,
    uid UUID REFERENCES users(uid),
    event_time INT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    event_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    remote_ip TEXT NOT NULL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS account_events (
    event_id SERIAL PRIMARY KEY,
    uid UUID REFERENCES users(uid),
    event_time INT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    event_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    remote_ip TEXT NOT NULL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS functions (
    function_id SERIAL PRIMARY KEY,
    uid UUID REFERENCES users(uid) NOT NULL,
    name TEXT UNIQUE NOT NULL,
    code TEXT NOT NULL,
    tests TEXT NOT NULL,
    usecase TEXT NOT NULL,
    keywords TEXT NOT NULL
);