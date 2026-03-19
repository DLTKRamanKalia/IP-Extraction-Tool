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
        # If neither file exists, config stays empty — credential getters will
        # raise specific errors when called, rather than failing at import time.

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

    def get_aws_credentials_for_account(self, account):
        account_csv_map = {
            'deltekdev': 'Key/deltekDev_aws_dba-cli-user.csv',
            'GOSS': 'Key/GOSS_Readonly_accessKeys.csv'
        }
        if account not in account_csv_map:
            raise ValueError(f"Unknown AWS account: '{account}'")
        csv_path = account_csv_map[account]
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Credentials file not found: {csv_path}")
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    access_key = row.get('Access key ID', '').strip()
                    secret_key = row.get('Secret access key', '').strip()
                    if access_key and secret_key:
                        return {
                            'access_key_id': access_key,
                            'secret_access_key': secret_key
                        }
        except Exception as e:
            raise Exception(f"Error reading credentials for account '{account}': {str(e)}")
        raise ValueError(f"No valid credentials found in {csv_path}")

    def get_azure_credentials(self):
        if 'AZURE' not in self.config:
            raise ValueError(
                "Azure credentials not found in configuration. "
                "Add an [AZURE] section to config.ini with: "
                "tenant_id, client_id, client_secret, subscription_id"
            )
        return {
            'tenant_id': self.config['AZURE'].get('tenant_id'),
            'client_id': self.config['AZURE'].get('client_id'),
            'client_secret': self.config['AZURE'].get('client_secret'),
            'subscription_id': self.config['AZURE'].get('subscription_id')
        }

    def get_oci_credentials(self):
        if 'OCI' not in self.config:
            raise ValueError(
                "OCI credentials not found in configuration. "
                "Add an [OCI] section to config.ini with: "
                "tenancy_ocid, user_ocid, fingerprint, key_file, region"
            )
        return {
            'tenancy_ocid': self.config['OCI'].get('tenancy_ocid'),
            'user_ocid': self.config['OCI'].get('user_ocid'),
            'fingerprint': self.config['OCI'].get('fingerprint'),
            'key_file': self.config['OCI'].get('key_file'),
            'region': self.config['OCI'].get('region')
        }

config = Config()
