"""
Stub file for flask_migrate to resolve IDE import issues
"""

from typing import Any, Optional, Callable
from flask import Flask

class Migrate:
    def __init__(
        self, 
        app: Optional[Flask] = None, 
        db: Any = None, 
        directory: str = 'migrations',
        **kwargs: Any
    ) -> None: ...
    
    def init_app(
        self, 
        app: Flask, 
        db: Any, 
        directory: str = 'migrations',
        **kwargs: Any
    ) -> None: ...

def init_app(app: Flask, db: Any, directory: str = 'migrations', **kwargs: Any) -> None: ...

