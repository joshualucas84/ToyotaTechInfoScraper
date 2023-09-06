#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import base64
import globals
from urllib.parse import urlparse


from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

settings = globals.getSettings()
globals.setRootUrl(settings["root_url"])
globals.setRootDir(fr'{settings["root_dir"]}')
globals.setDirectory(settings["toyota_remote_dir"])  ## TODO: Replace with the URL for the directory you want to scrape (see README.md)
globals.setUsername(settings["username"])
globals.setPassword(settings["password"])
globals.setDefaultDownloadDir(settings["default_download_dir"])


def main():


    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    prefs = {
             "download.default_directory": globals.getDefaultDownloadDir() ,
             "download.prompt_for_download": False,
             "download.extensions_to_open": "applications/pdf",
             "plugins.plugins_disabled": "Chrome PDF Viewer",
             "plugins.always_open_pdf_externally": True}
    options.add_experimental_option("prefs", prefs)

    #options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    # Login URL
    login_url = f"{globals.getRootUrl()}/techInfoPortal/appmanager/t3/ti?_nfpb=true&_pageLabel=ti_home_page&goto=https%3A%2F%2Ftechinfo.toyota.com%3A443%2Fagent%2Fcustom-login-response%3Fstate%3DDXn0JOw9_lSKhNw8Dqzw8CKB1pU&original_request_url=https%3A%2F%2Ftechinfo.toyota.com%3A443%2F"

    # Navigate to the login page
    driver.get(login_url)

    # You might need to inspect the page to find the correct ids or name attributes
    username_field = driver.find_element(by=By.NAME, value="username")
    password_field = driver.find_element(by=By.NAME, value="password")
    login_button = driver.find_element(by=By.ID, value="externalloginsubmit")

    # Enter your credentials
    username_field.send_keys(globals.getUsername()) # TODO: Replace with your username
    password_field.send_keys(globals.getPassword()) # TODO: Replace with your password

    # Submit the form
    login_button.click()  # This works if the form is a traditional HTML form

    # It might be needed to use explicit wait here
    time.sleep(10)

    # URL to scrape after login

    directory_url = f'{globals.getRootUrl()}/t3Portal/resources/jsp/siviewer/index.jsp?{globals.getDirectory()}'
    driver.get(directory_url)
    time.sleep(5)
    section_titles = getSectionTitles(driver)
    for title in section_titles:
        driver.get(directory_url)
        time.sleep(5)
        process_section(driver, title)
    driver.quit()


def getSectionTitles(driver):
    section_titles = driver.execute_script(""" return window[1].eval("TREE_ITEMS")[0] """)
    new_section_titles = []


    for section in section_titles:
        if isinstance(section, list):
            new_section_titles.append(section[0])
        else:
            if (len(globals.getTitleForDir()) == 0):
                globals.setTitleForDir(cleanupText(section))
    return new_section_titles


def process_section(driver, section_title):
    # Toggles all nodes in the tree
    frame = driver.find_element_by_xpath("//frame[@name='navigation_frame']")
    driver.switch_to.frame(frame)
    time.sleep(1)
    driver.find_element_by_xpath(f"//a[@title='{section_title}']").click()
    driver.execute_script("""
            let allIds = [];
            let openedIds = [];
         function dfs(node) {
                // Add all ids to the allIds array
                allIds.push(node.n_id);

                // Check if the b_opened is true, then add the id to openedIds
                if(node.b_opened === true) {
                    openedIds.push(node.n_id);
                }

                // If there are children, then traverse them
                if(node.a_children && node.a_children.length > 0) {
                    for(let i = 0; i < node.a_children.length; i++) {
                        dfs(node.a_children[i]);
                    }
                }
            }

            // Call the function with the root node
            dfs(trees[0]);

            // Goes through all ids and opens the ones not already opened
            allIds.forEach(id => {
                // If the id is not in openedIds, then toggle it
                if (!openedIds.includes(id)) {
                    trees[0].toggle(id);
                }
            });
            """)
    time.sleep(1)

    # Get the page source after JavaScript has been executed
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # Extract all href links
    links = [a['href'] for a in soup.find_all('a', href=True) if '/t3Portal/' in a['href']]
    titles = [a['title'] for a in soup.find_all('a', href=True) if '/t3Portal/' in a['href']]
      # Loop through each link and save the page as a PDF
    driver.switch_to.default_content()
    for index in range(len(links)):
        link = links[index]
        # Some links might be relative, so we need to ensure they're absolute
        if not link.startswith('http'):
            link = globals.getRootUrl() + link
        # We'll use the link as the file name, replacing any characters that could cause problems
        filename = link.replace('https://', '').replace('http://', '').replace('/', '_') + '.pdf'
        driver.get(link)
        title = driver.title
        if title == "" or title == " ":
            title = titles[index]

        # Sanitize the title so it's safe to use as a filename
        directory, safe_title = create_filepath(title, section_title)
        if ".pdf" in driver.current_url:
            if not os.path.exists(directory):
                os.makedirs(directory)
            file = urlparse(driver.current_url)
            filename = os.path.basename(file.path)
            if os.path.isfile(f'{directory}/{safe_title}'):
                os.remove(f'{directory}/{safe_title}')
            os.rename(rf'{globals.getDefaultDownloadDir()}{filename}', f'{directory}/{safe_title}')
        else:
            pdf_data = driver.execute_cdp_cmd('Page.printToPDF', {"printBackground": True})
            # Check if the directory exists, and if not, create it
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.path.isfile(filename):
                with open(f'{directory}/{safe_title}', "wb") as f:
                    f.write(base64.b64decode(pdf_data['data']))


def cleanupText(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a underscore
    s = re.sub(r"\s+", '_', s)
    return s


def create_filepath(title, section_title):
    title = ''.join(title.split(';')[0])
    parts = title.split(":")
    section_title = cleanupText(section_title)

    # List to hold the cleaned parts
    cleaned_parts = []

    for part in parts:
        # Remove non-alphabetic characters and extra whitespace
        cleaned = re.sub('[^a-zA-Z ]', '', part).strip()

        # Title case the cleaned part and add it to the cleaned_parts list
        cleaned_parts.append(cleanupText(cleaned.title()))

    # Join the cleaned and title-cased parts with '/' and print the result
    cleaned_path = '/'.join([globals.getFullRootDirectory(), section_title] + cleaned_parts)

    # Separate the directory and filename
    directory, filename = os.path.split(cleaned_path)

    # Add '.pdf' to the filename
    filename += '.pdf'
    return directory, filename

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
