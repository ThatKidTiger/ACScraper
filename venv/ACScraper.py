# Methodology:
# Enter the search times, inserting the name of the villager into the url string
# depending on whether or not genuine cards only is selected, include the home-made filtering strings
# maybe check brand listing
# For each entry, click on the entry, and check the page for the same filtered keywords, if gco is selected.
# Add the relevant data to the arrays if none of the filtered keywords are found
# Also check if the date exceeds the time range that the user has selected

# Relevant Data:
# Price
# Shipping Price
# Listing Names
# Shipping Location, Check "Approximately US __" Tag if price is in non-US currency

# Configurations:
# Specific Country
# Owned vs. New Ticks
# Genuine Cards Only

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from numpy import mean, median, percentile
import numpy as np

import re

from dateutil.parser import *
from dateutil.utils import today
from dateutil.relativedelta import relativedelta
from datetime import *

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker

import os

def checkMultiple(text):
    multiple = False
    arr = text.split(" ")
    for j in range(0, len(arr) - 1):
        if cleanName(arr[j]) == name:
            if j == 0:
                if arr[1].lower() == "and":
                    multiple = True
            elif j == len(arr) - 1:
                if arr[len(arr) - 1] == "and":
                    multiple = True
            else:
                if arr[j - 1].lower() == "and" or arr[j + 1].lower() == "and":
                    multiple = True
    return multiple

def explicitLocate(xpath, driver):
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        return element
    except TimeoutException:
        raise NoSuchElementException


def explicitLocateTime(xpath, driver, time):
    try:
        element = WebDriverWait(driver, time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        return element
    except TimeoutException:
        raise NoSuchElementException


def cleanPrice(text):
    new_text = text
    new_text = re.sub("[^.0-9]", '', new_text)
    return new_text


def cleanDate(text):
    new_text = text
    new_text = re.sub("Sold ", '', new_text)
    return new_text


def cleanName(text):
    new_text = text.lower()
    new_text = re.sub("[^a-z]", '', new_text)
    return new_text


chrome = webdriver.Chrome("C:/Users/nytig/seleniumchrome/chromedriver.exe")

# Genuine Cards Only variable, which controls what is or is not filtered out
gco = True

# The excluded terms are only inserted into the url if gco is enabled
if gco:
    excludes = open("exclude", "r")
    excluded = excludes.readlines()
    for i in range(0, len(excluded)):
        excluded[i] = excluded[i].replace("\n", "")

    exclude = "-" + "+-".join(excluded)
else:
    exclude = ""

# placeholder string for eventual user entry of time interval in days
timeinterval = ""
today = today().date()

if timeinterval == "":
    earliestdate = today + relativedelta(months=-1)
else:
    earliestdate = today + relativedelta(days=-int(timeinterval))

page = 1
# placeholder string for eventual user entry of the target amiibo
name = "chief"
url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=\"%s\"+animal+crossing+card+%s&_sacat=0&LH_TitleDesc=0&LH_PrefLoc=1&_fsrp=1&_sop=13&LH_Complete=1&LH_Sold=1&_ipg=200&_pgn=%d" % (
    name, exclude, page)

# generate the directory for the boxplot and rolling average
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
outputdir = os.path.join(ROOT_DIR, "listings/%s" % name)
if not os.path.exists(outputdir):
    os.makedirs(outputdir)

chrome.get(url)

titles = []
dates = []
prices = []

while True:
    for i in range(1, 201):
        titlePath = "/html//ul[@class='srp-results srp-list clearfix']/li[%d]/div/div[2]/a/h3" % i
        pricePath = "/html//ul[@class='srp-results srp-list clearfix']/li[%d]//div[@class='s-item__details clearfix']//span[@class='s-item__price']/span" % i
        shippingPath = "/html//ul[@class='srp-results srp-list clearfix']/li[%d]//div[@class='s-item__details clearfix']//span[@class='s-item__shipping s-item__logisticsCost']" % i
        datePath = "/html//ul[@class='srp-results srp-list clearfix']/li[%d]/div/div[2]/div[2]/div//span[@class='POSITIVE']" % i

        try:
            title = explicitLocate(titlePath, chrome)
            if gco:
                genuine = True
                titleText = title.text
                if checkMultiple(titleText):
                    continue

                title.click()

                try:
                    brand = explicitLocateTime("/html/body/div[3]/div[5]/div[1]//div[@class='itemAttr']//h2[@itemprop='brand']/span", chrome, 5)
                    brandText = brand.text
                    if brandText.lower() != "nintendo":
                        genuine = False
                except NoSuchElementException:
                    pass

                chrome.switch_to.frame("desc_ifr")
                descriptionBody = chrome.find_element_by_xpath("/html/body/table/tbody/tr/td/div").text.lower()

                for word in excluded:
                    if word in descriptionBody:
                        genuine = False
                        break

                chrome.back()
                if not genuine:
                    continue

            title = chrome.find_element_by_xpath(titlePath).text
            price = chrome.find_element_by_xpath(pricePath).text
            shipping = chrome.find_element_by_xpath(shippingPath).text
            date = parse(cleanDate(chrome.find_element_by_xpath(datePath).text)).date()

            if date >= earliestdate:
                if "Free" in shipping:
                    shipping = 0
                else:
                    shipping = float(cleanPrice(shipping))

                price = float(cleanPrice(price))

                prices.append(price + shipping)
                titles.append(title)
                dates.append(date)
            else:
                print("End of time interval reached: " + str(i) + " items processed.")
                break

        except NoSuchElementException:
            print("Search terminated. " + name.upper() + " page " + str(page) + " had only " + str(i) + " results.")
            break

    try:
        nextButton = chrome.find_element_by_xpath(
            "/html/body/div[4]/div[5]/div[2]/div[1]/div[2]/ul/div[3]/div[@class='s-pagination']//a[@class='pagination__next']")
        nextButton.click()
    except NoSuchElementException:
        print("Search terminated. " + name.upper() + " page " + str(page) + " had only " + str(i) + " results.")
        break

listings = {"titles": titles, "prices": prices, "dates": dates}
listingsFrame = pd.DataFrame(listings)

print(name.upper() + ":")
print("$" + str(round(mean(prices), 2)) + " Mean")
print("$" + str(round(median(prices), 2)) + " Median")
print("$" + str(round(percentile(prices, 25), 2)) + " 25th Percentile")
print("$" + str(round(percentile(prices, 75), 2)) + " 75th Percentile")
print(listingsFrame[['prices', 'dates']])

# boxplot pyplot code
bp = pd.DataFrame(listingsFrame['prices']).plot.box()
plt.figure(1)
plt.title(name.upper() + ' Price Distribution')
bp.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(10))
bp.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))
bp.grid(b=True, which='both', axis='y')
bp.figure.savefig(os.path.join(outputdir, name + " boxplot"))

# rolling average
f2 = plt.figure(figsize=(19.2, 10.8))
plt.title(name.upper() + ' 3 Day Rolling Average')
pc = listingsFrame[['dates', 'prices']]
mm = pc.prices.rolling(window=3).mean()

# pc = plt.plot(pc.dates, pc.prices, label = 'Average Price', color = 'blue')
mm = plt.plot(listingsFrame['dates'], mm, label='3 Day Rolling Average', color='blue')
f2.savefig(os.path.join(outputdir, name + " lineplot"))

chrome.close()
plt.close('all')
