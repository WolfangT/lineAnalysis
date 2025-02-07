"""QuickOSM plugin init."""

__copyright__ = 'Copyright 2025, Wolfang Torres'
__license__ = 'GPL version 3'
__email__ = 'wolfang.torres@gmail.com'

def classFactory(iface):
    """Launch of the plugin"""
    from .mainPlugin import lineAnalisisPlugin
    return lineAnalisisPlugin(iface)
