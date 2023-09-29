from pathlib import Path
import os

TOOLSET_NAME = 'Momotarou'
NODE_EDITOR_APP_NAME = 'NodeEditor'
TOOLS_VIEWER_APP_NAME = 'ToolsViewer'
LOCALAPPDATA = Path(os.getenv('LOCALAPPDATA')) / TOOLSET_NAME
CACHE_DIR = LOCALAPPDATA / 'Cache'
INTERMEDIATE_DIR = LOCALAPPDATA / 'Intermediate'
LAST_SESSIONS_DIR = LOCALAPPDATA / 'LastSessions'
RECENT_PROJECTS_STORAGE_FILE_PATH = LOCALAPPDATA / 'recent_projects.json'
TEMP_DIR = Path(os.environ.get('temp'))

