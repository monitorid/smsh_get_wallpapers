# smsh_get_wallpapers
Script for downloading wallpapers from smashingmagazine.com for a certain Month of Year

### Requirements
Python 3.8.2
asyncio
aiohttp
BeautifulSoup
tqdm
python-dateutil

#### Options
```
usage: smsh_downloader.py [-h] [-c LIMIT] MMYYYY resolution

Script for downloading wallpapers from smashingmagazine.com for a certain Month of Year

positional arguments:
  MMYYYY      Month and Year in format 102022
  resolution  Resolution in format 1024x768

optional arguments:
  -h, --help  show this help message and exit
  -c LIMIT    The number of connection limit
  
  for example
  smsh_downloader.py 102021 1024x768 
```
<p align="center">
  <img src="https://raw.githubusercontent.com/monitorid/smsh_get_wallpapers/main/smsh_get_scr.png">
</p>
