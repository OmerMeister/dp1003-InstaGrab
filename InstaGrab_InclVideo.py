from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver, common
from colorama import Fore, Back, Style, init
from datetime import datetime
from time import sleep
import requests
import getpass
import os

init(convert=True)

# GLOBAL VARIABLES
USER = "some_instagram_account"
OLDEST_POST_NUMBER = 1
POSTS_SUCCESS = 0
POSTS_FAIL = 0
FILES_SUCCESS = 0
FILES_FAIL = 0
profile_tab_handle = ""


def messages(text, msg_code):
    # info+cls = ic
    # info = i
    # error + cls = ec
    # error = e
    # clear screen support for both windows and linux
    if (msg_code == "ic"):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.GREEN, Back.BLACK + text + Style.RESET_ALL)
    elif (msg_code == "ec"):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.RED, Back.WHITE + text + Style.RESET_ALL)
    elif (msg_code == "i"):
        print(Fore.GREEN, Back.BLACK + text + Style.RESET_ALL)
    elif (msg_code == "e"):
        print(Fore.RED, Back.WHITE + text + Style.RESET_ALL)
    elif (msg_code == "cy"):
        print(Fore.CYAN, Back.BLACK + text + Style.RESET_ALL)


def prerequisites(driver):
    # checks if there is a h2 in the page, says that the acoount is private. if does, return true.
    # exception eccours if the profile is public, so return false.

    # looking for private indicator
    element = driver.find_elements(By.XPATH, '/ html / body / div[1] / div / div[3] / div / div / div / h2')
    if (len(element) > 0):
        element = element[0].text
        if ("Private" in element or "private" in element):
            messages("The account is private, cannot procceed", "ec")
            return True
    # looking for no posts error
    if ("Page not found" in driver.title):
        messages("The account has no posts", "ec")
        return True
    # looging for profile doesn't exist error
    if ("Profile doesn't exist" in driver.title):
        messages("The profile doesn't exist", "ec")
        return True
    else:
        return False


def scrollDown(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(0.5)


def newFolderHandler(profile_name):
    # duplicate folder name check
    folder_name = profile_name
    # path to user desktop (windows)
    desktop_path = f"C:/Users/{getpass.getuser()}/Desktop"
    # Combine the desktop path and folder name
    folder_path = desktop_path + "/" + folder_name
    # Check if the folder exists
    if os.path.exists(folder_path):
        messages(f"Folder name '{profile_name}' already exist", "e")
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = "IG_" + datetime_string
        folder_path = desktop_path + "/" + folder_name
        messages(f"Exporting to folder '{folder_name}' on Desktop", "e")
    else:
        messages(f"Exporting to folder '{folder_name}' on Desktop", "i")

    # Create the new folder
    os.mkdir(folder_path)
    return folder_path


def downloader(url, destination):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(destination + url[-4:], 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
        else:
            messages(f"Download function failed. Error: {response} file url: {url}", "e")
            return 0
    except Exception as e:
        messages(f"Download function failed. file url: {url} ,Error: {e}", "e")
        return 0


def url_ToMediaItems(driver, post_page_url, folder_path):
    # gets the driver to make a search inside a given page, the given page, and the primary suffix for the filename
    # a secondary suffix will be added if the post contain multiple items
    global POSTS_SUCCESS
    global POSTS_FAIL
    global FILES_SUCCESS
    global FILES_FAIL
    # Open a new tab and switch to the given url
    driver.switch_to.new_window('tab')
    tab_handle = driver.current_window_handle
    driver.get(post_page_url)
    # check if the post has single item
    if (len(driver.find_elements(By.XPATH, '//*[@class="swiper-wrapper carousel"]')) == 0):
        parent_div = driver.find_elements(By.XPATH, '//*[@class="main__image-container"]')[0]
        # check if the item is a image (jpg)
        try:
            media_element_url = parent_div.find_element(By.TAG_NAME, "img").get_attribute('src')
            # applying the downloader with the desire destanation and name
            downloader(media_element_url, folder_path)
            POSTS_SUCCESS += 1
            FILES_SUCCESS += 1
        except common.NoSuchElementException:
            # check if the item is a video (mp4)
            try:
                media_element_url = parent_div.find_element(By.TAG_NAME, "video").get_attribute('src')
                downloader(media_element_url, folder_path)
                POSTS_SUCCESS += 1
                FILES_SUCCESS += 1
            # the item is neither image tag or a video tag
            except common.NoSuchElementException:
                messages(f"Couldn't manage to get the post (single item). page url: {post_page_url}", "e")
                # because it's a one item post. the whole post fails
                POSTS_FAIL += 1
        finally:
            # switching to the post tab, close it and going back to the profile tab
            driver.switch_to.window(tab_handle)
            driver.close()
            driver.switch_to.window(profile_tab_handle)
    # check if the post has multiple items
    elif (len(driver.find_elements(By.XPATH, '//*[@class="swiper-wrapper carousel"]')) == 1):
        media_item_suffix = 1  # secondary suffix for the item of a post
        # trying to load the multi item element and split it to a list
        try:
            parent_div = driver.find_element(By.XPATH, '//*[@class="swiper-wrapper carousel"]')
            media_items_list = parent_div.find_elements(By.CLASS_NAME, "swiper-slide")
            # iterating on all of the media items in the list
            for media_item in media_items_list:
                messages(f"Working on media item: {media_item_suffix}", "cy")
                # checking if it is a picture
                try:
                    url = media_item.find_element(By.TAG_NAME, "img").get_attribute('src')
                    down_rslt = downloader(url, folder_path + "_item" + str(media_item_suffix))
                    if (down_rslt == 0):
                        FILES_FAIL += 1
                        media_item_suffix += 1
                        continue
                    media_item_suffix += 1
                    FILES_SUCCESS += 1
                except common.NoSuchElementException:
                    # check if the item is a video (mp4)
                    try:
                        url = media_item.find_element(By.TAG_NAME, "video").get_attribute('src')
                        down_rslt = downloader(url, folder_path + "_item" + str(media_item_suffix))
                        if (down_rslt == 0):
                            FILES_FAIL += 1
                            media_item_suffix += 1
                            continue
                        media_item_suffix += 1
                        FILES_SUCCESS += 1
                    # the item is neither image tag or a video tag
                    except common.NoSuchElementException:
                        messages(f"Couldn't manage to get the post media item. page url: {post_page_url}", "e")
            # after the for loop
            if (FILES_FAIL == len(media_items_list)):
                POSTS_FAIL += 1
            else:
                POSTS_SUCCESS += 1
        except:
            # in case the program could not load the multi items parent element
            POSTS_FAIL += 1
            messages(f"Couldn't manage to get the post (multiple items). page url: {post_page_url}", "e")


# detached chrome session
def InstaGrab():
    global profile_tab_handle
    MAX_POSTS = 3  ##########################################temp local variable

    # set the web driver and page to load
    print(Fore.GREEN, Back.BLACK + "Loading profile page. Please wait" + Style.RESET_ALL)
    service = Service(r"C:\Users\Omer\PycharmProjects\chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    driver.get(f'https://greatfon.com/v/{USER}')
    profile_tab_handle = driver.current_window_handle
    # check if the profile is private. it does, end the program.
    if prerequisites(driver):
        return 0
    # creating a list with all of the post elements (identify by classes)
    posts_list = driver.find_elements(By.XPATH, '//*[@class="content__item grid-item card"]')
    # get total post by the profile
    total_posts = \
        driver.find_elements(By.XPATH, '/ html / body / div[1] / div / div[3] / div / div / div[1] / div / a[1]')[
            0].text
    total_posts = int(total_posts[:-6])
    # if the wanted num of posts is more than all of the profile posts, it will change to total posts
    if (MAX_POSTS > total_posts):
        MAX_POSTS = total_posts
    # keep scrolling down and refreshing the posts list until it reach the desired length
    while (len(posts_list) < MAX_POSTS):
        scrollDown(driver)
        posts_list = driver.find_elements(By.XPATH, '//*[@class="content__item grid-item card"]')
        print("length is: ", len(posts_list))
    # if list length is beyond MAX_POSTS, then trim the list to reach desired length
    if (len(posts_list) > MAX_POSTS):
        del posts_list[MAX_POSTS:len(posts_list)]

    # get the href from the post element and put it back in the list instead of the element
    for index, value in enumerate(posts_list):
        posts_list[index] = value.find_element(By.TAG_NAME, "a").get_attribute('href')
    # creating a desktop folder for the exported media
    folder_path = newFolderHandler(USER)
    # iterating on all of the posts from oldest to newest and applying the media save function on them
    post_num = 1  # decide from with number to start. from the oldest post to newest
    current_post_number = OLDEST_POST_NUMBER
    for url in reversed(posts_list):
        try:
            messages(f"Working on post number: {post_num}, url is: {url}", "i")
            url_ToMediaItems(driver, url, folder_path + "/" + str(current_post_number))
        except Exception as e:
            print(f"exception on parsing the url: {url}", e)
            continue
        finally:
            post_num += 1
            current_post_number += 1
    # Finish message,statistics, and close driver
    messages("#-#-# Done! #-#-#", "b")
    messages(
        f"Succeded posts: {POSTS_SUCCESS}, Failed posts: {POSTS_FAIL}, Succeeded files: {FILES_SUCCESS}, Failed fails: {FILES_FAIL}",
        "cy")
    driver.quit()
    sleep(100)


# Main
InstaGrab()
