from pathlib import Path
import os

TOOLSET_NAME = 'Momotarou'
NODE_EDITOR_APP_NAME = 'NodeEditor'
TOOLS_VIEWER_APP_NAME = 'ToolsViewer'
CACHE_DIR = Path(os.getenv('LOCALAPPDATA')) / TOOLSET_NAME / NODE_EDITOR_APP_NAME
TOOLS_PATH = CACHE_DIR / 'tools'
