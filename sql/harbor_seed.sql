

--harbors
INSERT INTO harbors (id, name, timezone) VALUES
    (1, 'Portside Harbor', '2026-07-23 00:00:00+00'),
    (2, 'East Reach Harbor', '2026-07-23 00:00:00+00');

-- Ships
INSERT INTO ships (id, ship_name, registration_number, ship_status, current_cargo, cargo_capacity, ship_size) VALUES
    (1, 'Aurora', 'SHIP-001', 'docked', 150, 200, 'large'),
    (3, 'Maco', 'SHIP-001', 'docked', 150, 200, 'small'),
    (2, 'Sea Wind', 'SHIP-002', 'sailing', 50, 150, 'medium');

-- Docks
INSERT INTO docks (id, dock_code, dock_name, harbor_id, dock_status, cargo_capacity, dock_size) VALUES
    (1, 1001, 'Alpha Dock', 1, 'active', 500, 'large'),
    (2, 1002, 'Bay Dock', 2, 'maintenance', 300, 'small');
    (2, 1002, 'Bay Dock', 2, 'maintenance', 300, 'medium');
    (2, 1002, 'Bay Dock', 1, 'maintenance', 300, 'medium');

-- Voyage records
INSERT INTO voyage (id, ship_id, departure_date, estimated_arrival, arrival_date, travel_status, departure_harbor_id, destination_harbor_id) VALUES
    (1, 2, '2026-07-24 08:00:00+00', '2026-07-25 18:00:00+00', NULL, 'scheduled', 1, 2),
    (2, 1, '2026-07-20 09:00:00+00', '2026-07-21 20:00:00+00', '2026-07-21 19:30:00+00', 'arrived', 2, 1);

-- Dockings
INSERT INTO dockings (id, ship_id, dock_id, arrival_date, departure_date, purpose, ship_clearance_status) VALUES
    (1, 1, 1, '2026-07-23 08:00:00+00', NULL, 'Loading cargo', 'approved'),
    (2, 2, 2, '2026-07-22 12:00:00+00', '2026-07-22 18:00:00+00', 'Routine maintenance', 'approved');

-- Advance serial sequences if using PostgreSQL SERIAL/sequence columns
SELECT setval(pg_get_serial_sequence('harbors', 'id'), (SELECT MAX(id) FROM harbors));
SELECT setval(pg_get_serial_sequence('ships', 'id'), (SELECT MAX(id) FROM ships));
SELECT setval(pg_get_serial_sequence('docks', 'id'), (SELECT MAX(id) FROM docks));
SELECT setval(pg_get_serial_sequence('voyage', 'id'), (SELECT MAX(id) FROM voyage));
SELECT setval(pg_get_serial_sequence('dockings', 'id'), (SELECT MAX(id) FROM dockings));
