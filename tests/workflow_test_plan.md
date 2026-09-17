# Harbor voyage/docking workflow test plan

This file is intentionally a test plan rather than a fake test suite. The project currently has no pytest fixtures or isolated test database, so these cases can be implemented once the test harness is added.

## Happy path

Start with:
- Ship 1 is `DOCKED`.
- Ship 1 has one active docking (`departure_date IS NULL`) at Harbor 1.
- Dock 1 is `INACTIVE` and belongs to Harbor 1.
- Harbor 2 has an `ACTIVE` dock compatible with Ship 1.
- Both harbors have coordinates.

### 1. Create voyage
`POST /voyages/create`

Expected:
- HTTP 201.
- `travel_status == scheduled`.
- `arrival_date is None`.
- `estimated_arrival > departure_date`.
- Ship remains `DOCKED`.
- Departure docking remains open.
- Departure dock remains `INACTIVE`.

### 2. Approve voyage
`POST /voyages/{id}/approve`

Expected:
- HTTP 200.
- `travel_status == approved`.
- Ship and dock state do not change.

### 3. Leave dock
`POST /voyages/{id}/leave_dock`

Expected:
- HTTP 200.
- `travel_status == departed`.
- Ship becomes `SAILING`.
- Previous docking gets `departure_date`.
- Previous dock becomes `ACTIVE`.

### 4. Record arrival
`POST /voyages/{id}/arrive`

Expected:
- HTTP 200.
- `travel_status == arrived`.
- `arrival_date` is recorded.
- Ship remains `SAILING` until destination docking is physically entered.
- The completed voyage is now eligible for the travel-time training set.

### 5. Create destination docking
`POST /dockings/from-voyage/{id}` with the destination `dock_id`.

Expected:
- HTTP 201.
- New docking has `PENDING` clearance.
- `arrival_date` equals the voyage's actual `arrival_date`.
- Ship remains `SAILING`.
- Destination dock remains `ACTIVE`.

### 6. Approve docking
`POST /dockings/{docking_id}/approve`

Expected:
- HTTP 200.
- Docking clearance becomes `APPROVED`.
- Ship remains `SAILING`.
- Dock remains `ACTIVE`.

### 7. Enter destination dock
`PUT /dockings/{docking_id}/arrive/`

Expected:
- HTTP 202.
- Ship becomes `DOCKED`.
- Destination dock becomes `INACTIVE`.
- Docking remains open (`departure_date IS NULL`).

## Negative workflow cases

1. Create a voyage for a `SAILING` ship -> 400.
2. Create a voyage with a departure harbor different from the ship's current dock harbor -> 400.
3. Approve an already approved/departed/arrived voyage -> 400.
4. Leave an unapproved voyage -> 400.
5. Leave a voyage while the ship is not `DOCKED` -> 400.
6. Leave with a future departure date -> 400.
7. Record arrival before departure -> 400.
8. Record arrival in the future -> 400.
9. Record arrival twice -> 400.
10. Create destination docking before the voyage arrives -> 400.
11. Create destination docking using a dock from another harbor -> 400.
12. Create destination docking when the ship already has an active docking -> 400.
13. Create destination docking on an inactive/maintenance dock -> 400.
14. Create destination docking with an incompatible ship/dock size -> 400.
15. Approve a non-pending docking -> 400.
16. Enter an unapproved docking -> 400.
17. Enter a docking before its arrival time -> 400.
18. Enter a docking after it has already been released -> 400.
19. Enter a docking while the ship is not `SAILING` -> 400.
20. Enter a docking whose dock is no longer active -> 400.

## ML/training checks

- A completed voyage with positive duration and positive route distance appears in the training set.
- A voyage with zero/negative duration is ignored by training.
- A voyage with missing harbor coordinates is ignored by training.
- After recording arrival, `/voyages/predict` reports one additional valid training sample when the voyage has positive distance and duration.
- A ship with no historical samples still receives the shared regression prediction/cold-start baseline.

## Timezone checks

- Send departure/arrival datetimes with `Z` (UTC).
- Send equivalent datetimes with an explicit offset such as `-05:00`.
- Confirm they represent the same instant after normalization.
- Confirm naive datetimes are treated as UTC by the current application policy.
- Confirm a local harbor timezone is metadata for display/conversion, not a replacement for UTC storage.

## Data integrity checks

- Creating a voyage must not close its current docking.
- Leaving a voyage must close exactly the ship's current docking.
- Arriving a voyage must not create a docking automatically.
- Creating a destination docking must not occupy the dock before approval/entry.
- Approving a docking must not change ship/dock physical state.
- Entering an approved docking must update both ship and dock in the same transaction.
