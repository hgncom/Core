# handlers.py

import logging
import sys

# Configure logging
logging.basicConfig(filename='error.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def log_error(error):
    """
    Log an error to the system log file.
    """
    logging.error(error)

def handle_data_error(error):
    """
    Handle errors related to data processing.
    """
    log_error(error)
    # Implement data-specific error handling logic, e.g., retrying data fetching or cleaning.
    print("Handling data error:", error)

def handle_network_error(error):
    """
    Handle errors related to network issues.
    """
    log_error(error)
    # Implement network-specific error handling logic, e.g., retrying the request after a delay.
    print("Handling network error:", error)

def handle_system_error(error):
    """
    Handle unrecoverable system errors.
    """
    log_error(error)
    # Implement logic for severe errors, e.g., sending alerts or safely shutting down.
    print("Handling system error:", error)
    sys.exit(1)

def handle_error(error, error_type):
    """
    Main function to handle errors based on their type.
    """
    if error_type == 'data':
        handle_data_error(error)
    elif error_type == 'network':
        handle_network_error(error)
    elif error_type == 'system':
        handle_system_error(error)
    else:
        log_error("Unknown error type: " + error_type)
