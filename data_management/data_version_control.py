import subprocess
import os

class DataVersionControl:
    def __init__(self, repo_path=None):
        if repo_path is None:
            # If no repo path is provided, assume the current working directory
            self.repo_path = os.getcwd()
        else:
            self.repo_path = repo_path
        self._verify_repo()

    def _run_command(self, command, cwd=None):
        """
        Utility method to run shell commands.
        """
        if cwd is None:
            cwd = self.repo_path
        result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")
        return result.stdout

    def _verify_repo(self):
        """
        Verify that the specified path is a DVC and Git repository.
        """
        try:
            self._run_command("git status")
            self._run_command("dvc status")
        except Exception:
            raise Exception("The specified path is not a valid DVC and Git repository.")

    def checkpoint_data(self, dataset_path, metadata):
        """
        Create a version checkpoint for the dataset, including metadata.
        """
        # Add dataset to DVC
        self._run_command(f"dvc add {dataset_path}")

        # Save metadata, assuming a simple JSON format for this example
        metadata_path = f"{dataset_path}.meta.json"
        with open(os.path.join(self.repo_path, metadata_path), 'w') as meta_file:
            import json
            json.dump(metadata, meta_file)

        # Add changes to Git, including the metadata file
        self._run_command(f"git add {dataset_path}.dvc {metadata_path}")
        commit_message = f"Checkpoint for {dataset_path} with metadata."
        self._run_command(f"git commit -m \"{commit_message}\"")

    def track_experiment(self, experiment_details):
        """
        Record details of a model training experiment, including dataset version, parameters, and metrics.
        This function assumes the use of a simple file-based logging for demonstration.
        """
        experiment_log_path = os.path.join(self.repo_path, "experiments.log")
        with open(experiment_log_path, 'a') as log_file:
            from datetime import datetime
            log_entry = f"{datetime.now()}: {experiment_details}\n"
            log_file.write(log_entry)

        # Add the log entry to Git to track changes over time
        self._run_command(f"git add {experiment_log_path}")
        self._run_command('git commit -m "Log experiment details"')


    def version_pipeline(self, pipeline_stages):
        """
        Define and version a data processing pipeline using DVC.
        This function assumes a predefined structure for pipeline stages passed as a parameter.
        """
        dvc_file_path = os.path.join(self.repo_path, "dvc.yaml")
        with open(dvc_file_path, 'w') as dvc_file:
            import yaml
            yaml.dump({"stages": pipeline_stages}, dvc_file)

        # Add the DVC pipeline file to DVC and Git
        self._run_command("dvc add dvc.yaml")
        self._run_command("git add dvc.yaml.dvc")
        self._run_command('git commit -m "Version pipeline configuration"')


# Example usage
if __name__ == "__main__":
    dvc_control = DataVersionControl()
    dataset_path = "data/my_dataset.csv"
    metadata = {"source": "source_name", "date": "2023-04-01", "description": "Initial dataset version."}
    dvc_control.checkpoint_data(dataset_path, metadata)
