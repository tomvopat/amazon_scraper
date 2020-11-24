import requests
from bs4 import BeautifulSoup
import numpy as np
import time
import re
from itertools import cycle
import os
import copy
import pandas as pd
##########################################################
##########################################################

# validates the response from the http request
def check_response(r):
    if r.status_code != 200:
        return False

    return True

# removes empty lines from a string
def strip_empty_lines(s):
    if s is None:
        return ""

    result = ""

    lines = s.splitlines()
    for l in lines:
        if l.strip() != "":
            result += l

    return result

# validates the result of the parsing
def check_parsing_result(data):
    if data is None:
        return False
    if not bool(data):
        return False

    return True

def is_captcha(html):
    soup = BeautifulSoup(html, "lxml")
    captcha = soup.find(id="captchacharacters")
    if captcha:
        return True

    return False

# parse data from scraped url
def parse_data(html):
    soup = BeautifulSoup(html, "lxml")
    result = {}

    try:
        title = soup.head.title.string
        title = strip_empty_lines(title).strip()
        result["title"] = title
    except:
        pass

    try:
        price = soup.find(id="price").span.string
        price = strip_empty_lines(price).strip()
        result["price"] = price
    except:
        pass

    return result

# download the list of proxy servers
def download_proxies():
    url = "https://free-proxy-list.net/"
    r = requests.get(url)
    if not check_response(r):
        return []

    soup = BeautifulSoup(r.text, "lxml")
    ips = soup.find(id="raw").textarea.string

    pattern = r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}:[0-9]{1,5}"
    result = []
    for ip in ips.splitlines():
        if re.match(pattern, ip) is not None:
            result.append(ip)

    return result

# tries which proxies are working and returns the working ones
def validate_proxies(proxy_list, headers):
    print("validate proxies (size: {})".format(len(proxy_list)))

    scores = {}
    url = "https://www.google.com/"
    for p in proxy_list:
        scores[p] = 0

    for i in range(6):
        print("\trun: {}".format(i))
        for proxy in proxy_list:
            print("-", end="", flush="true")
            try:
                r = requests.get(url, headers=headers, proxies={"http": proxy}, timeout=1)
            except requests.RequestException:
                scores[proxy] += 1
        print("")

    result = [proxy for proxy, score in scores.items() if score < 3]
    return result

# reads proxies from file or downloads them if the file is not available
def get_proxies():
    file_name = "proxies.txt"
    proxies = []

    if os.path.isfile(file_name):
        f = open(file_name, "r")
        for l in f.readlines():
            proxies.append(l)
        f.close()
    else:
        proxies = download_proxies()
        proxies = validate_proxies(proxies, headers)
        print(proxies)
        f = open(file_name, "w")
        for p in proxies:
            f.write(p + "\n")
        f.close()

    return proxies

# prints statistics from scraping
def print_counters(counters):
    print("\nCounters:")
    for name, val in counters.items():
        if name == "time":
            print("\t{0}: {1:.0f} minutes".format(name, (time.time() - val)/60))
        else:
            print("\t{0}: {1}".format(name, val))

# initialize counters for statistics
def initialize_counters():
    counters = {}

    counters["time"] = time.time()
    counters["total"] = 0
    counters["response_error"] = 0
    counters["parsing_error"] = 0
    counters["request_error"] = 0
    counters["success"] = 0
    counters["captcha"] = 0
    counters["skipped"] = 0

    return counters

def scraper(urls, headers, proxies, counters):
    use_proxy = True if len(proxies) > 0 else False
    if use_proxy:
        print("using proxy")
    all_results = []

    # scrape all items
    for url in urls:
        print("trying: {0} ...".format(url[:50]))

        data = None
        i = 0
        while data is None and i < 100:
            counters["total"] += 1
            i += 1

            response = None
            # use proxy server
            if use_proxy:
                try:
                    proxy = np.random.choice(proxies)
                    response = requests.get(url, headers=headers, proxies={"http": proxy}, timeout=5)
                except requests.RequestException:
                    counters["request_error"] += 1
                    continue

            # don't use proxy server
            else:
                # wait - prevents from request blocking
                delay = np.random.random() * 7 + 1
                time.sleep(delay)

                try:
                    response = requests.get(url, headers=headers, timeout=5)
                except requests.RequestException:
                    counters["request_error"] += 1
                    continue

            # process the response
            if not check_response(response):
                counters["response_error"] += 1
                continue

            # check downloaded data
            if is_captcha(response.text):
                counters["captcha"] += 1
                continue

            data = parse_data(response.text)
            if not check_parsing_result(data):
                counters["parsing_error"] += 1
                continue

        if data is None:
            # scraping failed
            counters["skipped"] += 1
            continue
        else:
            # scraping succeeded
            counters["success"] += 1
            all_results.append(data)

    # return all results
    return all_results

#######################################################################
#######################################################################
# url address for scraping
urls = [
        "https://www.amazon.nl/Nintendo-Switch-Lite-Console-Grijs/dp/B07V5JJHK4/",
        "https://www.amazon.de/-/en/L4S3RE/dp/B085FXHR38/",
        "https://www.amazon.de/-/en/1072057-Gold-Standard-Gain-1624-G/dp/B01M2WZ41N/",
        "https://www.amazon.de/-/en/Mobile-Holder-Playstation-Gamepad-Controller-White/dp/B07WCFBNQM/",
        "https://www.amazon.de/-/en/Lizefang-Gamepad-Holder-Controller-Retractable/dp/B0832CDVFY",
        "https://www.amazon.de/dp/B01FPHG31M",
        "https://www.amazon.de/Her-Embroidered-Design-Rainbow-apply/dp/B071S13DDK/",
        "https://www.amazon.de/Rainbow-Flag-Pride-Iron-Patch/dp/B0764FNCG2/",
        "https://www.amazon.de/European-Embroidered-Emblem-Europe-International/dp/B0721SXJ4F/",
        "https://www.amazon.de/EmbTao-Czech-Republic-National-Embroidered/dp/B085T8LG56/",
        "https://www.amazon.de/Kindle-built-light-Special-Offers/dp/B07FQ4DJ7X/",
        "https://www.amazon.de/Sonos-Arc-Soundbar-Elegant-Immersive/dp/B0883K61BG/",
        "https://www.amazon.de/Sonos-Arc-Soundbar-Elegant-Immersive/dp/B0883M3PJB/",
        "https://www.amazon.de/AmazonBasics-Fade-Proof-100-Cotton-Towel/dp/B00Q4TK2W2",
        "https://www.amazon.de/AmazonBasics-Premium-Knife-Block-9-piece/dp/B00R3Z46JQ/",
        "https://www.amazon.de/Samsung-GP-U999SJVLGSB-SmartThings-Hub-V3/dp/B07XZ7NG4W/",
        "https://www.amazon.de/Nutrition-Standard-Supplement-Electrolytes-Strawberry/dp/B01EIS3790/",
        "https://www.amazon.de/9399506/dp/B08H99BPJN/",
        "https://www.amazon.de/dp/B08H93ZRK9/",
        "https://www.amazon.de/dp/B08MF7RQBL/",
        "https://www.amazon.com/AmazonBasics-Performance-Alkaline-Batteries-Count/dp/B00LH3DMUO/",
        "https://www.amazon.com/AmazonBasics-Lightning-USB-Cable-Collection/dp/B082T5WH22/",
        "https://www.amazon.com/AmazonBasics-Performance-Alkaline-Batteries-Count/dp/B00MNV8E0C/",
        "https://www.amazon.com/AmazonBasics-Silicone-Baking-Mat-Sheet/dp/B0725GYNG6/",
        "https://www.amazon.com/AmazonBasics-Premium-Single-Monitor-Stand/dp/B00MIBN16O/"
        "https://www.amazon.com/Acer-Display-Graphics-Keyboard-A515-43-R19L/dp/B07RF1XD36",
        "https://www.amazon.com/Lenovo-IdeaPad-Processor-Graphics-81W0003QUS/dp/B0862269YP/",
        "https://www.amazon.com/Acer-i5-9300H-GeForce-Keyboard-AN515-54-5812/dp/B086KJBKDW/",
        "https://www.amazon.com/Apple-MacBook-13-inch-256GB-Storage/dp/B08636NKF8/",
        "https://www.amazon.com/ASUS-Display-Processor-Microsoft-L406MA-WH02/dp/B0892WCGZM/"
        ]

urls2 = ["https://www.amazon.nl/Nintendo-Switch-Lite-Console-Grijs/dp/B07V5JJHK4/"]

# headers for http requests
headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'referrer': 'https://google.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Pragma': 'no-cache'
        }

# proxy servers
proxies = get_proxies()
counters = initialize_counters()

results = scraper(urls, headers, proxies, counters)
df = pd.DataFrame(results)
df.to_csv("result.csv")

# print statistics
print_counters(counters)
