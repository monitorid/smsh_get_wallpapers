import asyncio
import aiohttp
from bs4 import BeautifulSoup as BS
import argparse
import logging
from datetime import datetime,timedelta
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import re

#prevent the issue for asyncio bug on Windows 10
#https://github.com/aio-libs/aiohttp/issues/6635
import platform
if platform.system()=='Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] - %(message)s",
)
LOG = logging.getLogger(__name__)

#Validate date argument
def moyear(arg):
    try:
        MINYEAR=1999
        MASK='%m%Y'
        
        ndate=datetime.strptime(arg, '%m%Y')
        if ndate.year<MINYEAR:
            raise argparse.ArgumentTypeError(f'Minimal Year is {MINYEAR}')
        return ndate   
    except ValueError:
        raise argparse.ArgumentTypeError('Date must be in MMYYYY format')
        
#Validate resolution argument format
def resolution(arg):
    if not re.match('^\d{3,5}(x|X)\d{3,4}$',arg):
        raise argparse.ArgumentTypeError(f'Resolution must be in 1024x768 format')  
    #TODO: cyrillic x/X warning
    return arg
    

async def download_img(session, url, pbar):
    async with session.get(url) as resp:
        file_name = url.split('/')[-1]
        file_size = int(resp.headers.get('content-length', 0))
        
        try:
            with tqdm.wrapattr(open(file_name, mode='wb'), 'write',
                       desc=file_name,  unit='B', unit_scale=True, total=file_size, leave=False, nrows=6) as file:
                async for chunk in resp.content.iter_chunked(4096):
                    file.write(chunk)
                    
            #Version 2 :: Write to file after downloading (less I/O for SSD?)
            #file.write(await resp.read())
        except OSError as e:
            logging.warning(f'Error for writing image file: {file_name}')
            logging.warning(e)
            return Null
        except aiohttp.ClientConnectorError as e:
            logging.warning(f'Error for download image file: {e}')
            return Null
        except asyncio.TimeoutError:
            logging.warning(f'Timeout error for download image file: {file_name}')   
            return Null
        except Exception as e:
            logging.error(f'Error for image file {file_name} : {e}')
            return Null
            
        pbar.update(1)
        return file_name

def parse_page(content, resolution) -> list:
    soup = BS(content,"html.parser")
    img_urls=[]
    for el in soup.findAll(text=["with calendar: ","without calendar: "]):
        #finding resolution text in description of link
        el_res = el.parent.find(text=resolution) 
        if el_res:  
            img_urls.append (el_res.parent['href'])

    #Verion 2 :: With BeautifulSoup and regexp
    #print(soup.findAll('a', attrs={'href': re.compile(rf"smashingmagazine.com/files/wallpapers\/.*\/(nocal|cal)\/.*{resolution}", re.I)}))
   
    #Verion 3 :: With regexp without BeautifulSoup
    #print(re.findall( rf'href=[\'\"]?(https://smashingmagazine.com/files/wallpapers/[^/]+/[^/]+/(nocal|cal)/[^/]+-{resolution}[^\"\']+)[\'\"]', content))
    
    if not len(img_urls):
        logging.error(f'Images ({resolution}) were not found on the page with wallpapers. Please check the resolution')
    
    return img_urls

async def main(url, resolution, c_limit=10):
    conn = aiohttp.TCPConnector(limit=c_limit)
    timeout = aiohttp.ClientTimeout(total=120)
    with logging_redirect_tqdm():
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            try:
                async with session.get(url) as resp:
                    #TODO: User defined error
                    if resp.status == 404:
                        logging.error(f'The page with wallpapers does not exist\n{url}\nPlease check the Month and Date')
                        quit()
                    elif resp.status != 200: 
                        logging.error(f'Cannot download page with wallpapers\n{url}\nPlease check the Month and Date: {resp.status}')
                        #TODO: More elegant quitting
                        quit()
                        
                    image_urls = parse_page(await resp.text(),resolution)
                    #Main progress bar
                    pbar = tqdm(total=len(image_urls), leave=True)
                    tasks = [download_img(session, url, pbar) for url in image_urls]
                    return await asyncio.gather(*tasks)
                    
                    #
                    
            except (asyncio.TimeoutError, aiohttp.ClientOSError,
                aiohttp.ClientResponseError, aiohttp.ServerDisconnectedError) as e:
                    logging.error(f'{e}')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Script for downloading wallpapers from smashingmagazine.com for a certain Month of Year')
    parser.add_argument('month_year', metavar='MMYYYY', help='Month and Year in format 102022', type=moyear)
    parser.add_argument('resolution', help='Resolution in format 1024x768', type=resolution)
    parser.add_argument("-c", dest="limit", default=10, type=int, help="The number of connection limit")
    
    args = parser.parse_args()

    
    pre_month_date=args.month_year-timedelta(1)
    smsh_url=f'https://www.smashingmagazine.com/{pre_month_date.year}/{pre_month_date.month:02d}/desktop-wallpaper-calendars-{args.month_year.strftime("%B").lower()}-{args.month_year.year}/'
    resolution = args.resolution.lower()
    
    asyncio.run(main(smsh_url,resolution,c_limit=int(args.limit))) #.run instead get_event_loop() 
    
    #except KeyboardInterrupt:
    
