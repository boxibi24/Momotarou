from pathlib import Path
import os

NODE_EDITOR_APP_NAME = 'NodeEditor'
TOOLS_VIEWER_APP_NAME = 'ToolsViewer'
CACHE_DIR = Path(os.getenv('LOCALAPPDATA')) / "RUT" / NODE_EDITOR_APP_NAME
TOOLS_PATH = CACHE_DIR / 'tools'
