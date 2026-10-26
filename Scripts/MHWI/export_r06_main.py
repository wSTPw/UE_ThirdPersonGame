"""Author the constructor-proven native insertion main 112, without tests."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_r06_staging
export_r06_staging.main('R06MainShared-20261025', [112])
