"""
Use this to import kaos in the unit tests in this directory.

```
from .context import kaos
```
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    '../kaos')))

import kaos

