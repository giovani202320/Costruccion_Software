import sys
from pathlib import Path

# Agregar carpeta src al sys.path para facilitar las importaciones en las pruebas
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
