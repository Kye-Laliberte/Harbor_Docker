--CREATE TABLE if NOT EXISTS captains(
--    id SERIAL PRIMARY KEY,
--    name TEXT NOT NULL,
--    experience_years INTEGER CHECK(experience_years >= 0) DEFAULT 0
--);

-- Enum type definitions
CREATE TYPE IF NOT EXISTS dock_status_enum AS ENUM ('active', 'inactive', 'maintenance');
-- vessel sizes are stored as integer ranks: 1=small, 2=medium, 3=large
CREATE TYPE IF NOT EXISTS ship_status_enum AS ENUM ('docked', 'sailing', 'maintenance');
CREATE TYPE IF NOT EXISTS ship_clearance_status_enum AS ENUM ('pending', 'approved', 'denied');
CREATE TYPE IF NOT EXISTS voyage_status AS ENUM ('scheduled', 'departed', 'arrived', 'cancelled');


CREATE TABLE if NOT EXISTS ships(
    id SERIAL PRIMARY KEY,
--    captain_id INTEGER  REFERENCES Captain(id),
    ship_status ship_status_enum, NOT NULL, DEFAULT ship_status_enum.docked,
    ship_name Text DEFAULT 'Unknown Ship',
    current_cargo INTEGER NOT NULL DEFAULT 0 CHECK (current_cargo >= 0),
    registration_number TEXT UNIQUE NOT NULL,
    cargo_capacity INTEGER NOT NULL CHECK (cargo_capacity >= 0),
    ship_size INTEGER NOT NULL CHECK (ship_size IN (1, 2, 3)),
    CHECK(current_cargo <= cargo_capacity)
    --current_harbor_id INTEGER REFERENCES (harbor.id) DEFAULT=NULL
);


CREATE TABLE if NOT EXISTS harbors(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    timezone TIMESTAMP WITH TIME ZONE NOT NULL 
   -- harbor_status dock_harbor DEFAULT 'inactive' CHECK (harbor_status IN ('active', 'inactive', 'maintenance'))
);

CREATE TABLE if NOT EXISTS voyage(
   id SERIAL PRIMARY KEY,
   ship_id INTEGER NOT NULL REFERENCES ships(id),
   departure_harbor_id INTEGER NOT NULL REFERENCES harbors(id),
   destination_harbor_id INTEGER REFERENCES harbors(id),
   departure_date TIMESTAMP WITH TIME ZONE,
   estimated_arrival TIMESTAMP WITH TIME ZONE,
   arrival_date TIMESTAMP WITH TIME ZONE,
   travel_status voyage_status NOT NULL
    --CHECK( destination_harbor_id <> departure_harbor_id)
);

CREATE TABLE if NOT EXISTS docks(
    id SERIAL PRIMARY KEY,
    dock_code INTEGER UNIQUE NOT NULL,
    dock_status dock_status_enum NOT NULL DEFAULT 'active',
    harbor_id INTEGER REFERENCES harbors(id),
    dock_name TEXT,
    cargo_capacity INTEGER NOT NULL DEFAULT 0 CHECK (cargo_capacity >= 0),
    dock_size INTEGER NOT NULL CHECK (dock_size IN (1, 2, 3))
);

CREATE TABLE if NOT EXISTS dockings(
    id SERIAL PRIMARY KEY,
    ship_id INTEGER REFERENCES ships(id),
    dock_id INTEGER REFERENCES docks(id),
    arrival_date TIMESTAMP WITH TIME ZONE NOT NULL,
    departure_date TIMESTAMP WITH TIME ZONE,
    purpose TEXT,
    ship_clearance_status ship_clearance_status_enum DEFAULT 'pending',
    CHECK(departure_date IS NULL OR departure_date > arrival_date)
);