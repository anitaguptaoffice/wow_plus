import yaml

class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path='config.yaml'):
        if not hasattr(self, 'initialized'):
            self.config_path = config_path
            self.config = self._load_config()
            self.initialized = True

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"错误: 配置文件 {self.config_path} 未找到。")
            return {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get_config(self):
        return self.config
