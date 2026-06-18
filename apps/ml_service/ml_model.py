"""
Machine Learning Service for EduAnalytics.

Model: Linear Regression
Features: attendance, midterm, previous_gpa (derived)
Target: final exam score

Includes:
- Model training
- Pickle save/load
- Risk detection (predicted final < 50 → 'At Risk')
- Auto-load on server start via AppConfig.ready()
"""
import os
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# Model persistence path
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / 'ml_models' / 'grade_predictor.pkl'
SCALER_PATH = Path(__file__).resolve().parent.parent.parent / 'ml_models' / 'scaler.pkl'
METADATA_PATH = Path(__file__).resolve().parent.parent.parent / 'ml_models' / 'metadata.pkl'


class GradePredictor:
    """
    Linear Regression model that predicts final exam score.

    Features:
        - attendance (0–100): percentage of classes attended
        - midterm (0–100): midterm exam score
        - previous_gpa (0–4.0): student's cumulative GPA before this semester

    Target:
        - final (0–100): predicted final exam score

    Risk Detection:
        - Predicted final < 50 → 'At Risk'
        - Predicted final 50–69 → 'Borderline'
        - Predicted final >= 70 → 'Safe'
    """

    RISK_THRESHOLD = 50.0
    BORDERLINE_THRESHOLD = 70.0

    def __init__(self):
        self.model = None
        self.scaler = None
        self.metadata: Dict[str, Any] = {}
        self._is_loaded = False

    # ──────────────────────────────────────────────────────────────────────────
    #  Model Training
    # ──────────────────────────────────────────────────────────────────────────

    def train(self, retrain: bool = False) -> Dict[str, float]:
        """
        Train the Linear Regression model using data from the database.
        Saves model and scaler to disk as pickle files.

        Args:
            retrain: If True, force retrain even if model exists.

        Returns:
            Dict with training metrics (r2, mse, rmse, mae).
        """
        if not retrain and MODEL_PATH.exists():
            logger.info('ML model already exists; skipping training. Use retrain=True to force.')
            self._load_from_disk()
            return self.metadata.get('metrics', {})

        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

        # Load training data
        X, y = self._load_training_data()

        if len(X) < 10:
            raise ValueError(
                'Not enough training data. Need at least 10 grade records. '
                'Run the data generator first: python scripts/generate_fake_data.py'
            )

        logger.info(f'Training ML model with {len(X)} samples...')

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train/test split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        # Train Linear Regression
        self.model = LinearRegression()
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred = np.clip(y_pred, 0, 100)

        metrics = {
            'r2': round(float(r2_score(y_test, y_pred)), 4),
            'mse': round(float(mean_squared_error(y_test, y_pred)), 4),
            'rmse': round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
            'mae': round(float(mean_absolute_error(y_test, y_pred)), 4),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'coefficients': {
                'attendance': round(float(self.model.coef_[0]), 4),
                'midterm': round(float(self.model.coef_[1]), 4),
                'previous_gpa': round(float(self.model.coef_[2]), 4),
                'intercept': round(float(self.model.intercept_), 4),
            }
        }

        logger.info(f'Model trained — R²={metrics["r2"]}, RMSE={metrics["rmse"]}')

        self.metadata = {
            'metrics': metrics,
            'feature_names': ['attendance', 'midterm', 'previous_gpa'],
            'target': 'final',
            'algorithm': 'LinearRegression',
            'version': '1.0',
        }

        # Save to disk
        self._save_to_disk()
        self._is_loaded = True

        return metrics

    def _load_training_data(self):
        """Extract features and target from the database."""
        from apps.academics.models import Grade

        grades = Grade.objects.select_related('student').values(
            'attendance', 'midterm', 'final', 'student_id'
        )

        records = list(grades)
        if not records:
            return np.array([]), np.array([])

        df = pd.DataFrame(records)

        # Compute previous GPA per student (avg total_score of all other grades)
        from apps.academics.models import Grade as G
        gpa_map = {}
        from django.db.models import Avg
        for row in G.objects.values('student_id').annotate(avg=Avg('total_score')):
            gpa_map[row['student_id']] = min(row['avg'] / 25.0, 4.0)

        df['previous_gpa'] = df['student_id'].map(gpa_map).fillna(2.5)

        X = df[['attendance', 'midterm', 'previous_gpa']].values
        y = df['final'].values
        return X, y

    # ──────────────────────────────────────────────────────────────────────────
    #  Prediction
    # ──────────────────────────────────────────────────────────────────────────

    def predict(self, attendance: float, midterm: float, previous_gpa: float) -> Dict[str, Any]:
        """
        Predict final exam score and determine risk level.

        Args:
            attendance: Attendance percentage (0–100)
            midterm: Midterm score (0–100)
            previous_gpa: Previous GPA (0–4.0)

        Returns:
            Dict with predicted_final, risk_level, confidence_note
        """
        if not self._is_loaded:
            self._load_from_disk()

        if self.model is None:
            raise RuntimeError('ML model not trained. Call train() first.')

        # Validate inputs
        attendance = float(np.clip(attendance, 0, 100))
        midterm = float(np.clip(midterm, 0, 100))
        previous_gpa = float(np.clip(previous_gpa, 0, 4.0))

        features = np.array([[attendance, midterm, previous_gpa]])
        features_scaled = self.scaler.transform(features)
        prediction = float(np.clip(self.model.predict(features_scaled)[0], 0, 100))

        risk_level = self._determine_risk(prediction)
        total_score = round(midterm * 0.3 + prediction * 0.5 + attendance * 0.2, 2)

        return {
            'predicted_final': round(prediction, 2),
            'predicted_total_score': total_score,
            'risk_level': risk_level,
            'risk_label': self._risk_label(risk_level),
            'input': {
                'attendance': attendance,
                'midterm': midterm,
                'previous_gpa': previous_gpa,
            }
        }

    def predict_batch(self, records: List[Dict]) -> List[Dict]:
        """Predict for a list of student records."""
        return [
            self.predict(
                r.get('attendance', 0),
                r.get('midterm', 0),
                r.get('previous_gpa', 2.5),
            )
            for r in records
        ]

    def _determine_risk(self, predicted_final: float) -> str:
        """Classify risk based on predicted final score."""
        if predicted_final < self.RISK_THRESHOLD:
            return 'at_risk'
        elif predicted_final < self.BORDERLINE_THRESHOLD:
            return 'borderline'
        return 'safe'

    def _risk_label(self, risk_level: str) -> str:
        labels = {
            'at_risk': '⚠️ At Risk',
            'borderline': '⚡ Borderline',
            'safe': '✅ Safe',
        }
        return labels.get(risk_level, 'Unknown')

    # ──────────────────────────────────────────────────────────────────────────
    #  Persistence
    # ──────────────────────────────────────────────────────────────────────────

    def _save_to_disk(self):
        """Serialize model, scaler, and metadata to pickle files."""
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)

        with open(SCALER_PATH, 'wb') as f:
            pickle.dump(self.scaler, f)

        with open(METADATA_PATH, 'wb') as f:
            pickle.dump(self.metadata, f)

        logger.info(f'ML model saved to {MODEL_PATH}')

    def _load_from_disk(self):
        """Load model, scaler, and metadata from pickle files."""
        if not MODEL_PATH.exists():
            logger.warning('No trained ML model found. Train the model first.')
            return

        try:
            with open(MODEL_PATH, 'rb') as f:
                self.model = pickle.load(f)
            with open(SCALER_PATH, 'rb') as f:
                self.scaler = pickle.load(f)
            with open(METADATA_PATH, 'rb') as f:
                self.metadata = pickle.load(f)
            self._is_loaded = True
            logger.info('ML model loaded from disk successfully.')
        except Exception as e:
            logger.error(f'Failed to load ML model: {e}')
            self._is_loaded = False

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata and training metrics."""
        if not self._is_loaded:
            self._load_from_disk()
        return {
            'is_trained': self._is_loaded and self.model is not None,
            'model_path': str(MODEL_PATH),
            **self.metadata,
        }

    def is_ready(self) -> bool:
        """Check if model is loaded and ready for predictions."""
        return self._is_loaded and self.model is not None and self.scaler is not None


# ─── Singleton instance (loaded on server start) ──────────────────────────────
grade_predictor = GradePredictor()
