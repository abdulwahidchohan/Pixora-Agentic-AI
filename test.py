from pydantic.v1 import BaseSettings
from typing import Optional

class Test(BaseSettings):
    x: Optional[int] = None

print("BaseSettings success")
