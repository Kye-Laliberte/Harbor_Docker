--CREATE TABLE if NOT EXISTS captains(
--    id SERIAL PRIMARY KEY,
--    name TEXT NOT NULL,
--    experience_years INTEGER CHECK(experience_years >= 0) DEFAULT 0
--);



CREATE TABLE if NOT EXISTS ships(
    id SERIAL PRIMARY KEY,
--    captain_id INTEGER  REFERENCES Captain(id),
    ship_status STATUS  CHECK (ship_status IN ('docked', 'sailing', 'maintenance')),
    ship_name Text DEFAULT 'Unknown Ship',
    current_cargo INTEGER NOT NULL CHECK (current_cargo >= 0),
    registration_number TEXT UNIQUE NOT NULL,
    cargo_capacity INTEGER NOT NULL CHECK (cargo_capacity >= 0),
    ship_size TEXT NOT NULL CHECK (ship_size IN ('small','medium','large'))--,
    --current_harbor_id INTEGER REFERENCES (harbor.id) DEFAULT=NULL
    CHECK(curent_cargo <= cargo_capacity)
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
   departure_time TIMESTAMP WITH TIME ZONE,
   estimated_arrival TIMESTAMP WITH TIME ZONE,
   actual_arrival TIMESTAMP WITH TIME ZONE,
   travel_status STATUS NOT NULL CHECK (travel_status IN ('scheduled','departed','arrived','cancelled'))
    --CHECK( destination_harbor_id <> departure_harbor_id)
);

CREATE TABLE if NOT EXISTS docks(
    id SERIAL PRIMARY KEY,
    dock_code INTEGER UNIQUE NOT NULL,
    dock_status STATUS NOT NULL DEFAULT 'active' CHECK (dock_status IN ('active', 'inactive', 'maintenance')),
    harbor_id INTEGER REFERENCES harbors(id),
    dock_name TEXT NOT NULL,
    cargo_capacity INTEGER NOT NULL CHECK (cargo_capacity >= 0),
    dock_size INTEGER NOT NULL CHECK (dock_size IN ('small','medium','large'))
);

CREATE TABLE if NOT EXISTS dockings(
    id SERIAL PRIMARY KEY,
    ship_id INTEGER REFERENCES ships(id),
    dock_id INTEGER REFERENCES docks(id),
    arrival_date TIMESTAMP NOT NULL,
    departure_date TIMESTAMP,
    purpose TEXT,
    ship_clearance_status status DEFAULT 'pending' CHECK (ship_clearance_status IN ('pending', 'approved', 'denied')),
    CHECK(departure_date IS NULL OR departure_date >= arrival_date)
);