import os
import logging

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, node, plugin_dir):
        self.node = node
        self.plugin_dir = plugin_dir
        self.plugins = {}

    def load_plugins(self):
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    module = __import__(f'plugins.{module_name}', fromlist=[''])
                    plugin_class = getattr(module, f'{module_name.capitalize()}Plugin')
                    plugin = plugin_class(self.node)
                    self.plugins[module_name] = plugin
                    plugin.initialize()
                except Exception as e:
                    logger.error(f"Failed to load plugin {module_name}: {e}")

    def shutdown_plugins(self):
        for plugin in self.plugins.values():
            plugin.shutdown()

    def get_plugin(self, name):
        return self.plugins.get(name)