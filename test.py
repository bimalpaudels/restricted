from restricted.core import Restrictor

r = Restrictor(action="restrict")

code = """
import sys
import requests
"""

print(r.restrict(code))

