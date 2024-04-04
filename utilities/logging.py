import logging

def create_main_logger():
    """
    Creates a main logger for the application to log all processes and errors.
    Includes more detailed information in each log message.
    """
    print("Creating main logger...")  # Add this line for debugging
    logger = logging.getLogger('main_logger')
    logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG to include all log messages

    # Check if the logger already has handlers to prevent adding multiple file handlers
    if not logger.handlers:
        # Create a file handler to write logs to a file
        file_handler = logging.FileHandler('main.log')

        # Enhance the formatter to include file name, line number, and the function name
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d - %(funcName)s()] - %(message)s')

        # Set the formatter for the file handler
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)

    return logger
