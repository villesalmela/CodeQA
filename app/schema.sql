CREATE TABLE IF NOT EXISTS users (
    user_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL CHECK (LENGTH(username) BETWEEN 14 AND 100),
    password TEXT NOT NULL CHECK (LENGTH(password) = 162),
    verification_code TEXT NOT NULL CHECK (LENGTH(verification_code) = 162),
    admin BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    disabled BOOLEAN DEFAULT FALSE,
    created INT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    locked INT
);

CREATE TABLE IF NOT EXISTS auth_events (
    event_id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    event_time INT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    event_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    remote_ip TEXT NOT NULL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS account_events (
    event_id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    event_time INT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    event_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    remote_ip TEXT NOT NULL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS functions (
    function_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name TEXT UNIQUE NOT NULL,
    code TEXT NOT NULL,
    tests TEXT NOT NULL,
    usecase TEXT NOT NULL,
    keywords TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created INT DEFAULT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
    data BYTEA CHECK (LENGTH(data) < 100000)
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id SERIAL,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    function_id INT NOT NULL REFERENCES functions(function_id) ON DELETE CASCADE,
    value INT NOT NULL CHECK (value BETWEEN 1 AND 5),
    PRIMARY KEY (user_id, function_id)
);