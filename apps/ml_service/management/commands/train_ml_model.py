"""
Management command to train the ML model.
Usage: python manage.py train_ml_model [--retrain]
"""
from django.core.management.base import BaseCommand
from apps.ml_service.ml_model import grade_predictor


class Command(BaseCommand):
    help = 'Train the grade prediction ML model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retrain',
            action='store_true',
            help='Force retrain even if model already exists',
        )

    def handle(self, *args, **options):
        retrain = options['retrain']
        self.stdout.write(self.style.HTTP_INFO('🤖 Training ML model...'))

        try:
            metrics = grade_predictor.train(retrain=retrain)
            self.stdout.write(self.style.SUCCESS(
                f'✅ Model trained successfully!\n'
                f'   R² Score:  {metrics.get("r2", "N/A")}\n'
                f'   RMSE:      {metrics.get("rmse", "N/A")}\n'
                f'   MAE:       {metrics.get("mae", "N/A")}\n'
                f'   Samples:   {metrics.get("training_samples", "N/A")} train / '
                f'{metrics.get("test_samples", "N/A")} test\n'
                f'   Saved to:  ml_models/grade_predictor.pkl'
            ))
            if 'coefficients' in metrics:
                coef = metrics['coefficients']
                self.stdout.write(f'   Coefficients:')
                self.stdout.write(f'     attendance:   {coef["attendance"]}')
                self.stdout.write(f'     midterm:      {coef["midterm"]}')
                self.stdout.write(f'     previous_gpa: {coef["previous_gpa"]}')
                self.stdout.write(f'     intercept:    {coef["intercept"]}')
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'❌ Training failed: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {e}'))
            raise
