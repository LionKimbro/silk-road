APP_NAME = "silk-road"
PROJECT_DIR = ".silkroad"

SHERPA_DOCUMENT_SCOUT = "document-scout"
SHERPA_WAYSTATION_SCOUT = "waystation-scout"
SHERPA_DOCUMENT_INDEXER = SHERPA_DOCUMENT_SCOUT

STATUS_DISABLED = "disabled"
STATUS_RESTING = "resting"
STATUS_HIKING = "hiking"
STATUS_PAUSED = "paused"
STATUS_TROUBLE = "trouble"
STATUS_FINISHING = "finishing"

STATUS_TEXT = {
    STATUS_DISABLED: "Disabled",
    STATUS_RESTING: "Resting",
    STATUS_HIKING: "Hiking the mountains...",
    STATUS_PAUSED: "Paused on the trail",
    STATUS_TROUBLE: "Trouble",
    STATUS_FINISHING: "Returning to camp...",
}

PACE_PRESETS = {
    "cautious": 5,
    "walking": 15,
    "brisk": 30,
    "expedition": 75,
}

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    "site-packages",
}
