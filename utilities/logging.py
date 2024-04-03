import logging

def create_main_logger():
    """
    Creates a main logger for the application to log all processes and errors.
    Includes more detailed information in each log message.
    """
    logger = logging.getLogger('main_logger')
    logger.setLevel(logging.INFO)

    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler('main.log')

    # Enhance the formatter to include file name, line number, and the function name
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d - %(funcName)s()] - %(message)s')

    # Set the formatter for the file handler
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger
