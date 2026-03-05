"""
ML Service AppConfig.
Auto-loads the trained model when the Django server starts.
"""
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MlServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ml_service'
    verbose_name = 'ML Service'

    def ready(self):
        """Load the trained ML model on server startup."""
        try:
            from .ml_model import grade_predictor
            grade_predictor._load_from_disk()
            if grade_predictor.is_ready():
                logger.info('✅ ML model loaded successfully on startup.')
            else:
                logger.info('ℹ️  ML model not trained yet. Run: python manage.py train_ml_model')
        except Exception as e:
            logger.warning(f'Could not load ML model on startup: {e}')
