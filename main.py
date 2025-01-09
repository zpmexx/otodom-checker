import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from get_chrome_driver import GetChromeDriver
import json
import re
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from datetime import datetime
import sqlite3
import sys
from pathlib import Path
import csv
import re
try:
    file_name = Path(__file__).stem
except:
    file_name = None


#get date
now = formatDateTime = formatted_date = formatDbDateTime = None
try:
    now = datetime.now()
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    formatDbDateTime = now.strftime("%Y/%m/%d %H:%M")
    formatted_date = now.strftime("%Y-%m-%d")
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem with date - {str(e)}\n""")
        
        
try:
    load_dotenv()
    login = os.getenv('login')
    password = os.getenv('password')
    # from_address = os.getenv('from_address')
    # to_address = os.getenv('to_address')
    # email_password = os.getenv('email_password')
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem with loading .env variables - {str(e)}\n""")        

try:
    get_driver = GetChromeDriver()
    get_driver.install()
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem with getting a ChromeDriver - {str(e)}\n""")

options = webdriver.ChromeOptions()
options.add_argument("disable-infobars")
options.add_argument("start-maximized")
options.add_argument("disable-dev-shm-usage")
options.add_argument("no-sandbox")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_argument("disable-blink-features=AutomationControlled")

service = Service()
try:
    driver = webdriver.Chrome(options=options, service=service)
except:
    driver = webdriver.Chrome(service=service)
login_data = {
    'username': {login}, 
    'password': {password} 
}

#login url
login_url = 'https://login.otodom.pl/?redirect_uri=https%3A%2F%2Fwww.otodom.pl%2Fapi%2Finternal%2Fhciam%2Fcallback&state=eyJyZWZlcnJlciI6IlwvcGxcL29mZXJ0YVwvcHJ6eS1sZXNpZS02OS05MW0tYmFsa29uLTktODhtLW0tcGFya2luZ293ZS1JRDRwb202In0%3D&response_type=code&approval_prompt=auto&code_challenge=yo0YqxJeXlgEcfgvKhPfX_8GbT2oeKpnovrWCcgDAN8&code_challenge_method=S256&client_id=7qfnltd713ntok0m0ohv2bn29j'
try:
    driver.get(login_url)
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem with  loading a login page - {str(e)}\n""")

time.sleep(3)

try:
    cookie_consent_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")  
    cookie_consent_button.click()
    
    login_field = driver.find_element(By.XPATH,'//*[@id="username"]')

    login_field.send_keys(login_data['username'])
                                                  #/html/body/div[1]/div/div/div/div/div[1]/div[2]/div[3]/div[2]/form/div[2]/div/div/div/input
    password_field = driver.find_element(By.XPATH,'//*[@id="password"]')

    password_field.send_keys(login_data['password'])
    
    driver.find_element(By.XPATH,'/html/body/div[1]/div/div/div/div/div[1]/div[2]/div[2]/div[2]/form/button[2]/span/span').click()
    
    
    time.sleep(3)

except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem with login - {str(e)}\n""")
        
counter = 1
cars_dict = {}
list_items = []
csv_file_path = "real_estate_listings.csv"
with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Write the header row
    writer.writerow(["Link","Title", "City","Region",'Street', "Price", "Rooms", "Size", "Rent",'Ifrent','Price+Rent'])
    while True:
        try:
            observed_link = f'https://www.otodom.pl/pl/zapisane/ogloszenia?page={counter}'
            driver.get(observed_link)
            
            print(driver.current_url)
            try:
                page_number = re.search(r'\d+', driver.current_url).group()
                print(page_number)
                
                if int(page_number) != counter:
                    print("KAROL")
                    break
            except Exception as e:
                print(e)
            

            # Wait for the page to load

            # Locate all parent containers of the elements
            elements = driver.find_elements(By.CSS_SELECTOR, 'li[data-cy="single-saved-ad"]')  # Adjust the selector to match the container
    

            # Loop through each container to extract data
            for element in elements:
                try:
                    title = element.find_element(By.CSS_SELECTOR, '.css-ikdvvr').text.strip()
                    address = element.find_element(By.CSS_SELECTOR, '.css-1vifsg9').text.strip()
                    price = element.find_elements(By.CSS_SELECTOR, '.css-1cyxwvy')[0].text.strip()
                    rooms = element.find_elements(By.CSS_SELECTOR, '.css-1cyxwvy')[1].text.strip()
                    size = element.find_elements(By.CSS_SELECTOR, '.css-1cyxwvy')[2].text.strip()
                    rent = element.find_element(By.CSS_SELECTOR, '.css-5qfobm').text.strip()
                    link = element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                    
                    # remove zł from price
                    price = price[:-3]

                    # find rent value if exists
                    rentprice =  re.search(r'\d+', rent)
                    if rentprice:
                        rent = rentprice.group()
                        ifRent = True
                    else:
                        rent = 0
                        ifRent = False
                        
                    # Split address
                    try:
                        parts = address.split(',')
                        city,region,street = parts[0],parts[1],parts[2]
                    except:
                        city = parts[0] if len(parts) > 0 else None
                        region = parts[1] if len(parts) > 1 else None
                        street = parts[2] if len(parts) > 2 else None
                    
                    price_rent = float(price) + float(rent)
                        
                    # Write the data to the CSV file
                    writer.writerow([link,title, city,region,street, price, rooms, size, rent,ifRent,price_rent])

                    # Print extracted variables (optional for debugging)
                    print(f"Link: {link}")
                    print(f"Title: {title}")
                    print(f"Address: {address}")
                    print(f"Price: {price}")
                    print(f"Rooms: {rooms}")
                    print(f"Size: {size}")
                    print(f"Rent: {rent}")
                    print("-" * 50)  # Separator for better readability
                except Exception as e:
                    print(f"Error extracting data from an element: {e}")

            # Close the browser  
        except NoSuchElementException:
                #print(f"No more pages after {counter}.")
                break

        except Exception as e:
            with open ('logfile.log', 'a') as file:
                file.write(f"""{formatDateTime} Problem with favorites page - {str(e)}\n""")
        counter +=1
driver.quit()