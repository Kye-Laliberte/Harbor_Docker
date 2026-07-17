CREATE TABLE if NOT EXISTS Captain(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    experience_years INTEGER CHECK(experience_years >= 0) DEFAULT 0
);

CREATE TABLE if NOT EXISTS Ship(
    id SERIAL PRIMARY KEY,
    captain_id INTEGER  REFERENCES Captain(id),
    ship_status status DEFAULT 'docked' CHECK (ship_status IN ('docked', 'sailing', 'maintenance')),
    ship_name Text DEFAULT 'Unknown Ship',
    current_cargo INTEGER NOT NULL CHECK (current_cargo >= 0),
    registration_number TEXT UNIQUE NOT NULL,
    cargo_capacity INTEGER NOT NULL CHECK (cargo_capacity >= 0)
);

CREATE TABLE if NOT EXISTS Dock(
    id SERIAL PRIMARY KEY,
    dock_code INTEGER UNIQUE NOT NULL,
    dock_status status DEFAULT 'active' CHECK (dock_status IN ('active', 'inactive', 'maintenance')),
    harbor_id INTEGER REFERENCES Harbor(id),
    port_name TEXT NOT NULL,
    cargo_capacity INTEGER NOT NULL CHECK (cargo_capacity >= 0)
);

CREATE TABLE if NOT EXISTS Harbor(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    harbor_status status DEFAULT 'inactive' CHECK (harbor_status IN ('active', 'inactive'))
);

CREATE TABLE Docking(
    id SERIAL PRIMARY KEY,
    ship_id INTEGER REFERENCES Ship(id),
    dock_id INTEGER REFERENCES Dock(id),
    arrival_date TIMESTAMP NOT NULL,
    departure_date TIMESTAMP,
    purpose TEXT,
    ship_clearance_status status DEFAULT 'pending' CHECK (ship_clearance_status IN ('pending', 'approved', 'denied'))
    CHECK(
        departure_date IS NULL OR departure_date >= arrival_date)
);