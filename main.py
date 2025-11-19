# main.py

import os
from app.plaguefire import Plaguefire

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    app = Plaguefire(project_root)
    app.run()
