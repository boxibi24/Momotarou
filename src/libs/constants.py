from pathlib import Path
import os

TOOLSET_NAME = 'Momotarou'
NODE_EDITOR_APP_NAME = 'NodeEditor'
TOOLS_VIEWER_APP_NAME = 'ToolsViewer'
LOCALAPPDATA = Path(os.getenv('LOCALAPPDATA'))
CACHE_DIR = LOCALAPPDATA / TOOLSET_NAME / 'Cache'
INTERMEDIATE_DIR = LOCALAPPDATA / TOOLSET_NAME / 'Intermediate'

