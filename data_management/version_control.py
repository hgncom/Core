import subprocess
import os

class VersionControl:
    def __init__(self, dataset_dir='data'):
        """
        Initialize the VersionControl class with the dataset directory.
        """
        self.dataset_dir = dataset_dir
        # Ensure the dataset directory exists
        os.makedirs(self.dataset_dir, exist_ok=True)

    def _run_dvc_command(self, command):
        """
        Helper function to run a DVC command and return the output.
        """
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            raise Exception(f"DVC command failed: {result.stderr}")
        return result.stdout

    def save_version(self, dataset_path, version_message):
        """
        Save a new version of the dataset with a descriptive message.
        """
        add_command = f"dvc add {os.path.join(self.dataset_dir, dataset_path)}"
        self._run_dvc_command(add_command)

        # Git commands to commit the changes
        subprocess.run(f"git add {os.path.join(self.dataset_dir, dataset_path)}.dvc", shell=True)
        subprocess.run(f"git commit -m '{version_message}'", shell=True)

        print(f"Dataset version saved: {version_message}")

    def list_versions(self):
        """
        List all available versions of the dataset.
        """
        log_command = "git log --oneline"
        log_output = self._run_dvc_command(log_command)
        print("Available versions:")
        print(log_output)

    def get_version(self, version_id):
        """
        Retrieve a specific version of the dataset.
        """
        checkout_command = f"git checkout {version_id}"
        self._run_dvc_command(checkout_command)
        print(f"Checked out to version: {version_id}")