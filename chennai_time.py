# chennai_time.py

from datetime import datetime
from zoneinfo import ZoneInfo

chennai_time = datetime.now(ZoneInfo("Asia/Kolkata"))
# denver_time = datetime.now(ZoneInfo("America/Denver"))

print("Chennai time:")
print(chennai_time.strftime("%Y-%m-%d %H:%M:%S"))