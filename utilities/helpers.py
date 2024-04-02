# helpers.py

import logging
import os

# Configure a basic logger for the system
def configure_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        filename='system.log', filemode='a')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(console_handler)

def safe_create_directory(directory_path):
    """
    Safely create a directory if it does not already exist.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Directory created or already exists: {directory_path}")
    except Exception as e:
        logging.error(f"Failed to create directory {directory_path}: {e}")

def validate_data_schema(data, schema):
    """
    Validate a piece of data against a predefined schema.
    This is a placeholder function that should be implemented based on the specific validation needs.
    """
    # Placeholder for schema validation logic
    pass

# Example usage of utility functions
if __name__ == "__main__":
    configure_logging()
    logging.info("Utility functions example")

    directory_path = 'path/to/new/directory'
    safe_create_directory(directory_path)

    # Example data and schema
    data = {"name": "Example", "value": 100}
    schema = {"type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "number"}}}
    validate_data_schema(data, schema)
