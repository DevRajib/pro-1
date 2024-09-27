from django.core.management.base import BaseCommand
from transactions.views import check_user_status
import logging

# Set up logging for the command
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check user status and send notifications if necessary.'

    def handle(self, *args, **kwargs):
        try:
            # Call the function to check user status
            check_user_status()
            self.stdout.write(self.style.SUCCESS('Checked user status and sent notifications.'))
        except Exception as e:
            # Log any errors that occur during the execution of the command
            logger.error(f"Error checking user status: {e}")
            self.stdout.write(self.style.ERROR(f"Error checking user status: {e}"))
