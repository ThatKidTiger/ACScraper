from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from numpy import mean, median, percentile
import re
from dateutil.parser import *
from dateutil.utils import today
from dateutil.relativedelta import relativedelta
from datetime import *

def clean_prices(text):
    new_text = text
    new_text = re.sub("[^.0-9]", '', new_text)
    return new_text

def clean_dates(text):
    new_text = text
    new_text = re.sub("Sold ", '', new_text)
    return new_text

driver = webdriver.Chrome("C:/Users/nytig/seleniumchrome/chromedriver.exe")

excludes = open("exclude", "r")
excluded = excludes.readlines()
for i in range(0, len(excluded)):
    excluded[i] = excluded[i].replace("\n", "")

exclude = "-" + "+-".join(excluded)

timeinterval = ""
today = today().date()

if timeinterval == "":
    earliestdate = today + relativedelta(months=-1)
else:
    earliestdate = today + relativedelta(days=-int(timeinterval))

page = 1
name = "erik"
url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=\"%s\"+animal+crossing+card+%s&_sacat=0&LH_TitleDesc=0&LH_PrefLoc=1&_fsrp=1&_sop=13&LH_Complete=1&LH_Sold=1&_ipg=200&_pgn=%d" % (name, exclude, page)

driver.get(url)

titles = []
prices = []

for i in range(1, 201):
    titlepath = "/html/body/div[4]/div[4]/div[2]/div[1]/div[2]/ul/li[%d]/div/div[2]/a/h3" % i
    pricepath = "/html/body/div[4]/div[4]/div[2]/div[1]/div[2]/ul/li[%d]/div/div[2]//span[@class='POSITIVE']" % i
    shippingpath = "/html/body/div[4]/div[4]/div[2]/div[1]/div[2]/ul/li[%d]/div/div[2]//span[@class='s-item__shipping s-item__logisticsCost']" % i
    datepath = "/html/body/div[4]/div[4]/div[2]/div[1]/div[2]/ul/li[%d]/div/div[2]//span[@role='text']" % i

    try:
        title = driver.find_element_by_xpath(titlepath).text
        price = driver.find_element_by_xpath(pricepath).text
        shipping = driver.find_element_by_xpath(shippingpath).text
        date = parse(clean_dates(driver.find_element_by_xpath(datepath).text)).date()
    except NoSuchElementException:
        print("Search terminated. " + name.upper() + " page " + page + " had only " + i + " results.")
        break;

    if "Free" in shipping:
        shipping = 0
    else:
        shipping = float(clean_prices(shipping))

    price = float(clean_prices(price))

    prices.append(price + shipping)
    titles.append(title)

print(name.upper() + ":")
print("$" + str(round(mean(prices), 2)) + " Mean")
print("$" + str(round(median(prices), 2)) + " Median")
print("$" + str(round(percentile(prices, 25), 2)) + " 25th Percentile")
print("$" + str(round(percentile(prices, 75), 2)) + " 75th Percentile")
print(prices)
driver.close()

#TO-DO
#filter by date by scraping the sale time, optional time range field, default one month
#Front end for name entry and time entry
#front end statistics reporting with pandas
#If you want to be extra, retrieve the image and put it next to the graph
#Remind aaliya to pay nick back his $35!!!!!

