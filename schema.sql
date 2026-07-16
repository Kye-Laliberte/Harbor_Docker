CREATE TABLE if NOT EXISTS Captain(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT DEFAULT 'Unknown'
);

CREATE TABLE if NOT EXISTS Ship(
    id SERIAL PRIMARY KEY,
    captain_id INTEGER NOT NULL REFERENCES Captain(id),
    ship_name Text DEFAULT 'ghost ship',
    cargo_size INTEGER NOT NULL CHECK (cargo_size > 0),
    registration_number TEXT UNIQUE NOT NULL
);

CREATE TABLE if NOT EXISTS Dock(
    id SERIAL PRIMARY KEY,
    dock_code INTEGER UNIQUE NOT NULL,
    port_name TEXT NOT NULL
);

CREATE TABLE if NOT EXISTS Harbor(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    dock_count INTEGER CHECK(dock_count > 0) DEFAULT 1,
    harbor_status status, DEFAULT('open')
);

CREATE TABLE Docking(
    id SERIAL PRIMARY KEY,
    ship_id INTEGER REFERENCES Ship(id),
    dock_id INTEGER REFERENCES Dock(id),
    arrival_date TIMESTAMP NOT NULL,
    departure_date TIMESTAMP,
    CHECK(
        departure_date IS NULL OR departure_date >= arrival_date)
);