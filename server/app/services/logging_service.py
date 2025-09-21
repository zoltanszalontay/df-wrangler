import yaml

class LoggingService:
    def __init__(self, config_path="server/app/conf/config.yaml"):
        self.config_path = config_path
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def get_logging_level(self, service_name):
        if service_name == "all":
            return {service: self.config.get('logging', {}).get(service, {}).get('level', 'off') for service in self.config.get('services', [])}
        return self.config.get('logging', {}).get(service_name, {}).get('level', 'off')

    def get_log_file(self, service_name):
        return self.config.get('logging', {}).get(service_name, {}).get('log_file')

    def set_logging_status(self, service_name, level):
        if 'logging' not in self.config:
            self.config['logging'] = {}

        if service_name == "all":
            for service in self.config.get('services', []):
                if service not in self.config['logging']:
                    self.config['logging'][service] = {}
                self.config['logging'][service]['level'] = level
        else:
            if service_name not in self.config['logging']:
                self.config['logging'][service_name] = {}
            self.config['logging'][service_name]['level'] = level

        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f)

logging_service = LoggingService()
