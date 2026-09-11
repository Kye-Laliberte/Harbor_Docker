from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt

from sqlalchemy.orm import Session, aliased

from app.models import Harbor, Ship, Voyage

DEFAULT_SPEED_KMH = 20.0
MIN_SPEED_KMH = 1.0
MAX_SPEED_KMH = 100.0


def haversine_distance_km(origin: Harbor, destination: Harbor) -> float:
    """Return the great-circle distance between two harbors."""
    if None in (origin.latitude, origin.longitude, destination.latitude, destination.longitude):
        raise ValueError("Both harbors need latitude and longitude")

    latitude_delta = radians(destination.latitude - origin.latitude)
    longitude_delta = radians(destination.longitude - origin.longitude)
    origin_latitude = radians(origin.latitude)
    destination_latitude = radians(destination.latitude)
    value = sin(latitude_delta / 2) ** 2 + cos(origin_latitude) * cos(destination_latitude) * sin(longitude_delta / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(value))

def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

def _training_rows(db: Session) -> list[tuple[int, float, int, float]]:
    origin = aliased(Harbor)
    destination = aliased(Harbor)
    rows = (
        db.query(Voyage, Ship, origin, destination)
        .join(Ship, Voyage.ship_id == Ship.id)
        .join(origin, Voyage.departure_harbor_id == origin.id)
        .join(destination, Voyage.destination_harbor_id == destination.id)
        .filter(
            Voyage.departure_date.isnot(None),
            Voyage.arrival_date.isnot(None),
            origin.latitude.isnot(None),
            origin.longitude.isnot(None),
            destination.latitude.isnot(None),
            destination.longitude.isnot(None),).all())

    training_rows = []
    for voyage, ship, origin_harbor, destination_harbor in rows:
        duration_hours = (_as_utc(voyage.arrival_date) - _as_utc(voyage.departure_date)).total_seconds() / 3600
        distance_km = haversine_distance_km(origin_harbor, destination_harbor)
        if duration_hours > 0 and distance_km > 0:
            training_rows.append((ship.id, distance_km, int(ship.ship_size), distance_km / duration_hours))
    return training_rows


def training_sample_count(db: Session) -> int:
    """Return the number of completed voyages available as labeled data."""
    return len(_training_rows(db))


class ShipSpeedRegression:
    """Ridge linear regression trained with batch gradient descent.

    Features are an intercept, route distance, vessel size, and one indicator
    for each ship observed in the training set. Unknown ships use the shared
    distance and vessel-size coefficients without a ship indicator.
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        epochs: int = 5000,
        regularization: float = 1e-3,
        tolerance: float = 1e-9,
    ):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.regularization = regularization
        self.tolerance = tolerance
        self.ship_feature_index: dict[int, int] = {}
        self.ship_sample_counts: dict[int, int] = {}
        self.coefficients: list[float] = []
        self.sample_count = 0
        self.epochs_run = 0
        self.training_loss: float | None = None

    @property
    def is_fitted(self) -> bool:
        return bool(self.coefficients)

    def _features(self, distance_km: float, ship_size: int, ship_id: int | None = None) -> list[float]:
        features = [0.0] * (3 + len(self.ship_feature_index))
        features[0] = 1.0
        features[1] = distance_km / 1000.0
        features[2] = float(ship_size) / 3.0
        if ship_id in self.ship_feature_index:
            features[self.ship_feature_index[ship_id]] = 1.0
        return features

    def fit(self, training_rows: list[tuple[int, float, int, float]]) -> "ShipSpeedRegression":
        self.sample_count = len(training_rows)
        self.ship_sample_counts = {}
        if not training_rows:
            return self

        for ship_id, _, _, _ in training_rows:
            self.ship_sample_counts[ship_id] = self.ship_sample_counts.get(ship_id, 0) + 1

        ship_ids = sorted({row[0] for row in training_rows})
        self.ship_feature_index = {
            ship_id: index + 3 for index, ship_id in enumerate(ship_ids)
        }
        feature_count = 3 + len(ship_ids)
        feature_rows = [
            self._features(distance_km, ship_size, ship_id)
            for ship_id, distance_km, ship_size, _ in training_rows
        ]
        targets = [observed_speed for _, _, _, observed_speed in training_rows]
        self.coefficients = [0.0] * feature_count
        previous_loss = float("inf")

        for epoch in range(1, self.epochs + 1):
            errors = [
                sum(coefficient * feature for coefficient, feature in zip(self.coefficients, features)) - target
                for features, target in zip(feature_rows, targets)
            ]
            gradients = [0.0] * feature_count
            for features, error in zip(feature_rows, errors):
                for index, feature in enumerate(features):
                    gradients[index] += error * feature

            sample_count = len(feature_rows)
            for index in range(feature_count):
                gradients[index] = 2 * gradients[index] / sample_count
                if index != 0:
                    gradients[index] += 2 * self.regularization * self.coefficients[index]
                self.coefficients[index] -= self.learning_rate * gradients[index]

            squared_error = sum(error * error for error in errors) / sample_count
            penalty = self.regularization * sum(coefficient * coefficient for coefficient in self.coefficients[1:])
            current_loss = squared_error + penalty
            self.epochs_run = epoch
            self.training_loss = current_loss
            if abs(previous_loss - current_loss) < self.tolerance:
                break
            previous_loss = current_loss
        return self

    def predict(self, distance_km: float, ship_size: int, ship_id: int) -> float:
        if not self.is_fitted:
            return DEFAULT_SPEED_KMH
        features = self._features(distance_km, ship_size, ship_id)
        predicted_speed = sum(
            coefficient * feature
            for coefficient, feature in zip(self.coefficients, features)
        )
        return max(MIN_SPEED_KMH, min(MAX_SPEED_KMH, predicted_speed))

    def ship_sample_count(self, ship_id: int) -> int:
        return self.ship_sample_counts.get(ship_id, 0)


def _fit_speed_regression(db: Session) -> ShipSpeedRegression:
    return ShipSpeedRegression().fit(_training_rows(db))


def estimate_arrival(db: Session, ship: Ship, origin: Harbor, destination: Harbor, departure: datetime) -> tuple[datetime, float, float]:
    """Estimate arrival from learned completed-voyage speeds and route distance."""
    distance_km = haversine_distance_km(origin, destination)
    model = _fit_speed_regression(db)
    speed = model.predict(distance_km, int(ship.ship_size), ship.id)
    return _as_utc(departure) + timedelta(hours=distance_km / speed), speed, distance_km


def predict_voyage_metrics(db: Session, ship: Ship, origin: Harbor, destination: Harbor) -> dict[str, float | int | bool]:
    """Predict the ship's speed and average duration for a harbor pair."""
    distance_km = haversine_distance_km(origin, destination)
    rows = _training_rows(db)
    model = ShipSpeedRegression().fit(rows)
    speed = model.predict(distance_km, int(ship.ship_size), ship.id)
    return {
        "ship_id": ship.id,
        "departure_harbor_id": origin.id,
        "destination_harbor_id": destination.id,
        "distance_km": round(distance_km, 2),
        "predicted_speed_kmh": round(speed, 2),
        "average_voyage_time_hours": round(distance_km / speed, 2),
        "training_samples": len(rows),
        "ship_training_samples": model.ship_sample_count(ship.id),
        "model_trained": model.is_fitted,
        "regression_model": "ridge_linear_regression",
        "optimizer": "batch_gradient_descent",
        "training_loss": model.training_loss,
        "epochs_run": model.epochs_run,
    }