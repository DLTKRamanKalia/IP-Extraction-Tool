import os
import csv
import configparser

class Config:
    def __init__(self):
        self.config_file = 'config.ini'
        self.csv_file = 'Key/deltekDev_aws_dba-cli-user.csv'
        self.config = configparser.ConfigParser()
        self._initialize_config()

    def _initialize_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        elif os.path.exists(self.csv_file):
            self._read_from_csv()
            self._save_config()
        else:
            raise FileNotFoundError(
                f"Neither config.ini nor {self.csv_file} found. "
                "Please ensure AWS credentials CSV file exists."
            )

    def _read_from_csv(self):
        try:
            with open(self.csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    access_key = row.get('Access key ID', '').strip()
                    secret_key = row.get('Secret access key', '').strip()
                    if access_key and secret_key:
                        if 'AWS' not in self.config:
                            self.config['AWS'] = {}
                        self.config['AWS']['access_key_id'] = access_key
                        self.config['AWS']['secret_access_key'] = secret_key
                        break
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")

    def _save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get_aws_credentials(self):
        if 'AWS' not in self.config:
            raise ValueError("AWS credentials not found in configuration")
        return {
            'access_key_id': self.config['AWS'].get('access_key_id'),
            'secret_access_key': self.config['AWS'].get('secret_access_key')
        }

config = Config()
