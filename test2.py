import holidays
from bdateutil import isbday

jp_holidays = holidays.Japan()

print(isbday("18-07-2022", holidays=jp_holidays))

print(jp_holidays.get("17-07-2022") != None)
