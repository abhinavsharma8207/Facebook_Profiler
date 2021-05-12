import os
import sys
import json
import time
from selenium import webdriver
# importing the requests library
import requests
from requests_futures.sessions import FuturesSession
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import random
import re
import base64
from pyvirtualdisplay import Display
from bs4 import BeautifulSoup as bs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, ElementNotInteractableException, JavascriptException
from selenium.webdriver.common.keys import Keys
import re
import dateparser,datetime
import urllib.parse as urlparse
from urllib.parse import parse_qs
import sqlite3
from sqlite3 import Error

from .ElementSelectors import *


regex_query_remove_url = r'https?:\/\/[^\s]*[\r\n]*'
regex_patt_hashtag = r'\s(#[^\s]+)'
regex_patt_mention = r'(@[^\s]+)'

NAMED_ENTITY_RELATION_EXTRACTION_API = None

if 'NAMED_ENTITY_RELATION_EXTRACTION_API' in os.environ:
    NAMED_ENTITY_RELATION_EXTRACTION_API = os.environ['NAMED_ENTITY_RELATION_EXTRACTION_API']
else:
    NAMED_ENTITY_RELATION_EXTRACTION_API = "http://dmi-dev.tora-named-entity-recognition.dmi.devdef.g42.ae/api/named-entity-extraction"

DB_PATH = '/app/database/'


class FacebookProfileScraper:
    random_user_no = 0

    def __init__(self):
        self.date_format = '%Y-%m-%d %H:%M:%S'
        display = Display(visible=0, size=(1420, 1080))
        display.start()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1420,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument('--lang=en-ca')
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        # chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-web-resources')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-default-apps')
        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}


        try:
            self.browser = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)
            self.browser.maximize_window()

        except Exception as e:
            try:
                print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
                print("ERROR: " + str(e))
                print("reconnecting to chrome driver")
                time.sleep(60)
                self.browser = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)

            except:
                sys.exit("Chrome crashed exiting application")


    def get_db_path(self):
        return DB_PATH + 'fblogin.db'


    def init_sql_connection(self):
        try:
            con = sqlite3.connect(self.get_db_path())
            return con
        except Error:
            print(Error)

    def sql_fb_logins_fetch(self):
        con = self.init_sql_connection()
        cursor_obj = con.cursor()

        cursor_obj.execute('SELECT * FROM fblogin')
        rows = cursor_obj.fetchall()
        return rows


    def get_auth_object_from_db(self):
        fb_logins = self.sql_fb_logins_fetch()
        fb_auth_obj = None
        if len(fb_logins) > 1:
            self.random_user_no = random.randrange(0, len(fb_logins))
            fb_auth_obj = fb_logins[self.random_user_no]
        if len(fb_logins) == 1:
            fb_auth_obj = fb_logins[0]
        return fb_auth_obj

    def get_auth_object(self):
        auth_object = dict()
        auth_object["username"] = ""
        auth_object["password"] = ""
        auth_obj_db = self.get_auth_object_from_db()
        auth_object["username"] = auth_obj_db[1]
        auth_object["password"] = auth_obj_db[2]
        return auth_object


    def login(self):

        try:
            auth_object = self.get_auth_object()

            print("before", self.browser.title)
            self.browser.get("https://en-gb.facebook.com/login.php")

            # filling the forms
            WebDriverWait(self.browser, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="email"]')))
            # elem = self.browser.find_element_by_id("email")

            self.browser.find_element_by_xpath("//input[@id='email']").send_keys(r'%s' % auth_object["username"])
            # elem.send_keys(email)
            time.sleep(3)
            # elem = self.browser.find_element_by_id("pass")
            self.browser.find_element_by_xpath("//input[@id='pass']").send_keys(r'%s' % auth_object["password"])
            # elem.send_keys(password)

            print("check1", self.browser.find_element_by_xpath("//input[@id='email']").get_attribute("value"))
            print("check2", self.browser.find_element_by_xpath("//input[@id='pass']").get_attribute("value"))
            time.sleep(3)
            # self.browser.find_element_by_id("pass").send_keys(Keys.ENTER)
            self.browser.find_element_by_xpath("//input[@id='pass']").send_keys(Keys.ENTER)
            # elem.send_keys(Keys.RETURN)
            time.sleep(3)

            # more stuff
            print("title after click login", self.browser.title)

        except Exception as e:
            print("There was some error while logging in.")
            print(sys.exc_info())
            exit()

    def click_esc_key(self):
        return webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()

    def get_profile_posts(self, profile, sleep_times=8):

        self.login()

        searchurl = "https://m.facebook.com/profile.php?id=" + profile.get("userid")

        print("searchurl: ", searchurl)
        self.browser.get(searchurl)
        print("total_posts: ", profile.get("total_posts"))


        self._scroll_profile_post(profile.get("total_posts"), sleep_times)
        # WebDriverWait(self.browser, 50).until(EC.presence_of_element_located((By.XPATH, '//h1[contains(text(),"Search results")]')))
        # time.sleep(5)

        post_dict_list, intro_dict = self._extract_profile_html(profile)


        self.browser.close()
        return post_dict_list, intro_dict

    def check_height(self, old_height):
        new_height = self.browser.execute_script("return document.body.scrollHeight")
        return new_height != old_height


    def _extract_profile_html(self, profile):
        #Getting Intro
        intro_dict = dict()

        # Skip to the post index directly
        articles = self.browser.find_elements_by_xpath(articles_selector)
        posts = self.browser.find_elements_by_css_selector(post_no_selector)
        # print("bs_data.find_all", articles)
        post_dict_list = list()

        ''' Skip to desire post number.Only use when large amount of posts are crawled '''
        # posts = posts[current_post_index:] ## Can use desire number.
        for item in articles:
            post_dict = dict()
            post_text = self._extract_profile_post_text(item)
            post_time = self._extract_profile_post_time(item)
            conversation_id, link = self._extract_profile_link(item)

            if not not post_time and not not conversation_id:
                author_name = self._extract_profile_owner(item)
                # mentions, locations = self._extract_checkin_mentions(item)
                post_dict['id_str'] = str(conversation_id)
                post_dict['id'] = conversation_id
                post_dict['conversation_id'] = str(conversation_id)
                post_dict['user_id'] = int(profile.get("userid"))
                post_dict['user_id_str'] = profile.get("userid")
                post_dict['link'] = link
                post_dict['username'] = profile.get("username")
                post_dict['name'] = author_name
                # TODO
                post_dict['location'] = []
                post_dict['place'] = []
                # TODO: mentions in tag-friends or in post text
                post_dict['mentions'] = list([])
                post_dict['datestamp'] = post_time
                # TODO: urls in post text
                post_dict['urls'] = self._extract_url_from_post(post_text)
                post_dict['photos'] = self._extract_profiles_image(item)
                post_dict['profile_image_url'] = ''
                post_dict['facebook_post'] = post_text
                post_dict['hashtags'] = self._extract_hashtags(post_text)
                post_dict['reaction'] = self._extract_profile_reaction(item)
                # post_dict['image_paths'] = self._extract_profiles_image(item)
                post_dict['image_paths'] = None
                post_dict['video_url'] = ''
                post_dict['location_country'] = None
                post_dict['location_address'] = None
                post_dict['place_country'] = None
                post_dict['place_address'] = None
                post_dict['post_no_urls'] = self.remove_urls(post_text)
                post_dict['post_no_urls_mentions'] = self.remove_urls_mentions(post_text)

                #Add to check
                post_dict_list.append(post_dict)

        print("=======================TOTAL ITEMS:==========================", len(articles))
        return post_dict_list, intro_dict


    def remove_urls(self, text):
        text_cleaned = text
        if not not text:
            if len(text_cleaned.strip()) > 2:
                text_cleaned = re.sub(regex_query_remove_url, '', text_cleaned)
        return text_cleaned

    def _extract_url_from_post(self, text):
        urls = []
        if not not text:
            urls = re.findall(regex_query_remove_url, text)

        return urls

    def remove_urls_mentions(self, text):
        text_cleaned = text
        if not not text:
            if len(text_cleaned.strip()) > 2:
                text_cleaned = re.sub(regex_query_remove_url, '', text_cleaned)
                text_cleaned = re.sub(regex_patt_mention, '', text_cleaned)
        return text_cleaned


    def _extract_hashtags(self, text):
        response = []
        if not text:
            return response

        # extracting the hashtags
        hashtag_list = re.findall(regex_patt_hashtag, text)
        # printing the hashtag_list
        print("The hashtags in \"" + text + "\" are :")
        for hashtag in hashtag_list:
            response.append(hashtag)

        return response


    def _extract_profile_post_time(self, item):
        try:
            # post_time = item.find_element_by_xpath(".//span[@class='j1lvzwm4 stjgntxs ni8dbmo4 q9uorilb gpro0wi8']")
            date_content = item.find_element_by_css_selector(date_content_selector).get_attribute("aria-label")
            print("post_time: ", date_content)

            return self.get_publish_at(date_content)
        except (NoSuchElementException, StaleElementReferenceException) as error:
            try:
                date_content = item.find_element_by_css_selector(date_content_2_selector).text
                print("post_time-type-2: ", date_content)

                return self.get_publish_at(date_content)
            except (NoSuchElementException, StaleElementReferenceException) as error:
                return None

    def _extract_profile_owner(self, item):
        author_name = ''
        try:
            author_name = item.find_element_by_css_selector(profile_author_name_selector).get_property("textContent")
            if re.search("shared",author_name):
                author_name = re.sub(" shared a post.","",author_name)

            print(f"Author name --------> {author_name}")
        except (NoSuchElementException, StaleElementReferenceException) as error:
            author_name = item.find_element_by_css_selector(profile_author_name_only_selector).get_property("textContent")
            if re.search("shared",author_name):
                author_name = re.sub(" shared a post.","",author_name)
            print(f"Author name --------> {author_name}")
            print("Error retrieving author name : ",str(error))
        return author_name


    def _extract_checkin_mentions(self, item):
        persons = []
        locations = []
        try:
            print("--------HEADER TEXT >>>>-----h2--jsc-----", item.find_element_by_css_selector(post_header_selector).get_property("textContent"))
            full_header_text = item.find_element_by_css_selector(post_header_selector).get_property("textContent")

            if re.search('others', full_header_text, re.IGNORECASE):

                # others_link = item.find_element_by_xpath(u"//div[contains(., 'others') and @role='button']")
                other_link = item.find_element_by_xpath(profile_click_others_selector)
                print("=============others_linkothers_link==========", other_link.get_attribute('innerHTML'))
                time.sleep(0.3)
                webdriver.ActionChains(self.browser).move_to_element(other_link).perform()
                time.sleep(0.5)

                tooltips = self.browser.find_element_by_css_selector("span[role='tooltip']")
                # moving mouse to other place -> reload tooltip
                webdriver.ActionChains(self.browser).move_by_offset(10, 20).perform()

                persons.extend(tooltips.text.splitlines())

            # else:
            #     if " with " in full_header_text or " in " in full_header_text:
            #         # persons, locations = self.detect_object_entity(full_header_text)
            #         print("persons, locations ---------->>>>>>>>>>>>", persons, locations)
            #         # if not not persons:
            #         #     try:
            #         #         persons.remove(author_name)
            #         #     except ValueError:
            #         #         pass

            return persons, locations

        except (NoSuchElementException, StaleElementReferenceException) as error:
            print("Error retrieving mentions, checkin places: ",str(error))

        self.click_esc_key()
        return persons, locations


    # def detect_object_entity(self, text):
    #     # sending get request and saving the response as response object
    #     persons = []
    #     locations = []
    #     response = requests.post(url = NAMED_ENTITY_RELATION_EXTRACTION_API, json = text)
    #     # extracting data in json format
    #     if response.status_code == 200:
    #         data = response.json()
    #         if not not data:
    #             locations = data.get("locations")
    #             persons = data.get("persons")
    #
    #     return persons, locations


    def _extract_profile_owner_id_link(self, item):
        owner_link = item.find_element_by_xpath(profile_user_id_link_selector).get_attribute("href")
        owner_link_sanitize = owner_link.split("?")[0]
        owner_id = os.path.basename(os.path.normpath(owner_link_sanitize))
        # print("user_id: ", owner_id)
        # print("user_url: ", owner_link_sanitize)
        return owner_link_sanitize,owner_id


    def _extract_profile_post_text(self, item):

        # print("=================================================================================================================")
        # print("=============_extract_profile_post_text==========", item.get_attribute('innerHTML'))
        # print("=================================================================================================================")

        try:
            post_content = item.find_element_by_css_selector(profile_post_content_selector)
            print("post_content: ", post_content.text)
            return  self.get_see_more_content(item, post_content)

        except (NoSuchElementException, StaleElementReferenceException) as error:
            print("Exception post_content default ", error)
            try:
                post_content = item.find_element_by_xpath(profile_post_content_with_background_selector)
                print("post_content having background: ", post_content.text)
                return  self.get_see_more_content(item, post_content)
            except (NoSuchElementException, StaleElementReferenceException) as error:
                print("Exception post_content having background ", error)
                try:
                    post_content = item.find_element_by_xpath(profile_post_content_with_link_selector)
                    print("post_content having link: ", post_content.text)
                    return  self.get_see_more_content(item, post_content)
                except (NoSuchElementException, StaleElementReferenceException) as error:
                    print("Exception post_content having link ", error)
                    try:
                        post_content = item.find_element_by_css_selector(profile_post_content_with_blockquote_selector)
                        print("post_content with blockquote: ", post_content.text)
                        return  self.get_see_more_content(item, post_content)
                    except (NoSuchElementException, StaleElementReferenceException) as error:
                        print("Exception post_content with blockquote", error)
                        try:
                            post_content = item.find_element_by_xpath(profile_post_content_with_bold_font_selector)
                            print("post_content with bold font: ", post_content.text)
                            return  self.get_see_more_content(item, post_content)
                        except (NoSuchElementException, StaleElementReferenceException) as error:
                            print("Exception post_content with bold font", error)
                            try:
                                post_content = item.find_element_by_xpath(profile_post_content_bio_selector)
                                print("post_content ----> bio : ", post_content.text)
                                return  self.get_see_more_content(item, post_content)
                            except (NoSuchElementException, StaleElementReferenceException) as error:
                                print("Exception post_content bio", error)
                                try:
                                    post_content = item.find_element_by_xpath(profile_post_content_jobs_location_selector)
                                    print("post_content ----> birth, jobs, relocate : ", post_content.text)
                                    return  self.get_see_more_content(item, post_content)
                                except (NoSuchElementException, StaleElementReferenceException) as error:
                                    print("Exception post_content birth, jobs, relocate", error)
                                    try:
                                        check_post_content = item.find_element_by_xpath(profile_post_content_avatar_selector).get_attribute("src")
                                        if not not check_post_content:
                                            post_content = item.find_element_by_xpath(".//div[contains(@id,'jsc_c')]/div/div/div/div[2]/a/div/img").get_property("src")
                                            image_content = item.find_element_by_xpath(".//div[contains(@id,'jsc_c')]/div/div/div/div[2]/a/div/img").get_attribute("alt")
                                            return f"upload profile picture: {post_content} , image content: {image_content}"
                                    except (NoSuchElementException, StaleElementReferenceException) as error:
                                        print("Exception post_content ----> birth, jobs, relocate: ", error)
                                        return None


    def get_see_more_content(self, item, post_content):
        # bs_data = bs(item, 'html.parser')
        # print("================get_see_more_content==========html==", item.get_attribute('innerHTML'))
        if re.search('More', post_content.text, re.IGNORECASE):
            self.click_see_more_button(post_content)
            try:
                post_content = item.find_element_by_css_selector(profile_post_content_selector)
                print("after click see more - post_content: ", post_content.text)
                return  post_content.text
            except (NoSuchElementException, StaleElementReferenceException) as error:
                try:
                    post_content = item.find_element_by_xpath(profile_post_content_with_background_selector)
                    print("after click see more - post_content having background: ", post_content.text)
                    return  post_content.text
                except (NoSuchElementException, StaleElementReferenceException) as error:
                    try:
                        post_content = item.find_element_by_xpath(profile_post_content_with_link_selector)
                        print("after click see more - post_content having link: ", post_content.text)
                        return  post_content.text
                    except (NoSuchElementException, StaleElementReferenceException) as error:
                        try:
                            post_content = item.find_element_by_css_selector(profile_post_content_with_blockquote_selector)
                            print("after click see more - post_content having blockquote: ", post_content.text)
                            return  post_content.text
                        except (NoSuchElementException, StaleElementReferenceException) as error:
                            try:
                                post_content = item.find_element_by_xpath(profile_post_content_with_bold_font_selector)
                                print("after click see more - post_content with bold font: ", post_content.text)
                                return  post_content.text
                            except (NoSuchElementException, StaleElementReferenceException) as error:
                                try:
                                    post_content = item.find_element_by_xpath(profile_post_content_bio_selector)
                                    print("after click see more - post_content ----> bio : ", post_content.text)
                                    return  post_content.text
                                except (NoSuchElementException, StaleElementReferenceException) as error:
                                    try:
                                        post_content = item.find_element_by_xpath(profile_post_content_jobs_location_selector)
                                        print("after click see more - post_content ----> birth, jobs, relocate : ", post_content.text)
                                        return  post_content.text
                                    except (NoSuchElementException, StaleElementReferenceException) as error:
                                        return None
        return post_content.text


    def _extract_profile_link(self, item):
        try:
            int_conversation_id = 0
            element = item.find_element_by_xpath(".//a[@class='oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8 b1v8xokw']")
            time.sleep(0.2)
            if not element:
                return None, None
            webdriver.ActionChains(self.browser).move_to_element(element).perform()
            time.sleep(0.2)
            url = item.find_element_by_xpath(".//a[@class='oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8 b1v8xokw']").get_attribute("href")
            replaced_url = url.replace("amp;","")
            print("This replaced_url - post link -------->", replaced_url)
            parsed = urlparse.urlparse(replaced_url)

            try:
                user_id = parse_qs(parsed.query)['id'][0]
                conversation_id = parse_qs(parsed.query)['story_fbid'][0]
                link = f"https://www.facebook.com/permalink.php?story_fbid={conversation_id}&id={user_id}"

                print("conversation_id: ", conversation_id)
                print("link: ", link)
                return int(conversation_id), link
            except KeyError as error:
                path_str = urlparse.urlparse(replaced_url).path
                print("This profileId has username, crawling other way -------->", path_str)
                path_array = path_str.split("/posts/")
                if len(path_array) > 1:
                    conversation_id = path_str.split("/posts/")[1]
                    scheme = urlparse.urlparse(replaced_url).scheme
                    netloc = urlparse.urlparse(replaced_url).netloc
                    print("conversation_id: ", conversation_id)
                    print("link: ", scheme + "://" + netloc + path_str)

                    sanitize_conversation_id = conversation_id.replace("/", "")
                    try:
                        int_conversation_id = int(sanitize_conversation_id)
                    except ValueError as e:
                        print("This link is not normal post, conversation_id = ", sanitize_conversation_id)
                        if sanitize_conversation_id.index(':'):
                            int_conversation_id = sanitize_conversation_id.split(":")[0]
                        else:
                            int_conversation_id = 0

                    return int_conversation_id, scheme + "://" +  netloc + path_str
                return None, None

        except (NoSuchElementException, JavascriptException, StaleElementReferenceException) as error:
            return None, None


    def _extract_profiles_image(self, item):
        images = []
        try:
            # Try clicking on the images

            image_holder = item.find_element_by_css_selector(image_holder_selector)
            if not image_holder:
                return images
            # image_holder.click()
            self.browser.execute_script("arguments[0].click();", image_holder)
            # webdriver.ActionChains(browser).move_to_element(image_holder).click(image_holder).perform()
            self.browser.set_page_load_timeout(1000)
            count = 0
            max_count = 1
            try:
                album_existing = item.find_element_by_css_selector("div.ni8dbmo4.stjgntxs.pmk7jnqg")
                if not not album_existing:
                    max_count = 31
            except Exception as e:
                pass
            while(count < max_count):
                try:
                    # WebDriverWait(browser, 300).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.ji94ytn4")))
                    WebDriverWait(self.browser,300).until(
                        lambda x: x.find_element(By.CSS_SELECTOR,page_video_btn_selector + ',' + page_image_selector)
                    )

                    try:
                        video_btn = self.browser.find_element_by_css_selector(page_video_btn_selector)
                        print("\n----------Video Detected---------")
                        # webdriver.ActionChains(browser).send_keys(Keys.ARROW_RIGHT).perform()
                        next_btn = self.browser.find_element_by_css_selector(page_next_btn_selector)
                        next_btn.click()
                        count += 1
                        continue
                    except:
                        pass
                    time.sleep(0.4)
                    next_btn = self.browser.find_element_by_css_selector(page_next_btn_selector)
                    webdriver.ActionChains(self.browser).move_to_element(next_btn).perform()
                    spotlight = self.browser.find_element_by_css_selector(page_image_selector)
                    webdriver.ActionChains(self.browser).move_to_element(spotlight).perform()

                    # print('---------------------------------')
                    image_url = spotlight.get_attribute("src")
                    i = 0
                    if len(images) > 0:
                        while image_url == images[-1] and i < 15:
                            time.sleep(0.4)
                            i+=1
                            image_url = spotlight.get_attribute("src")
                            print(f'the loop count of the image is {i}')

                    print(f'Successfully retrieve image ${image_url}')
                    if image_url in images:
                        print('This image is already retrieved')
                        count = 40
                        # hasMore = False
                    else:
                        print('Appending image into the image list')
                        images.append(image_url)

                    ## Clicking next image
                    # webdriver.ActionChains(browser).send_keys(Keys.ARROW_RIGHT).perform()
                    next_btn.click()
                    # webdriver.ActionChains(browser).send_keys(Keys.ARROW_RIGHT).perform()
                    # time.sleep(1.2)
                    count += 1
                except Exception as ex:
                    print("Issue from ImageExtractor : ",ex)

                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    print("error type : ",exc_type)
                    print(f"Error message ---------> {exc_value} & data type --------> {type(exc_value)} ")
                    if exc_type == ElementNotInteractableException:
                        count = 40
                    elif exc_type == NoSuchElementException:
                        # WebDriverWait(browser,60).until(EC.presence_of_element_located((By.CSS_SELECTOR, page_image_selector)))
                        try:
                            WebDriverWait(self.browser, 10).until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, image_paginator_selector))
                            )
                            # Selector image paginator and retrieve all images at once.
                            images_pager = self.browser.find_element_by_css_selector(image_paginator_selector)
                            print("Image selector found")
                            image_elements = images_pager.find_elements_by_css_selector('img')
                            for image in image_elements:
                                images.append(image.get_attribute("src"))

                            return images
                        except Exception as exc:
                            pass

                    count += 1
                    time.sleep(0.5)
            print("******* done crawling images for post*************")
            time.sleep(0.5)
            self.click_esc_key()

        except Exception as e:
            # No image holder or images here
            print('Issue from ImageHolder : ' + str(e))
            self.click_esc_key()

        time.sleep(1)
        return images


    def _extract_shares(self, item):

        return 0


    def _extract_profile_reaction(self, item):
        like_count = 0
        try:
            likes = item.find_element_by_css_selector(like_count_selector).get_attribute("innerText")
            print("raw like string *******  ", likes)
            reg = r"\d+|\d+\.\d+"
            if re.search(r"k|K",likes):
                like = re.search(reg,likes).group()
                like_count = int(float(like) * 1000)
            elif re.search(r"m|M",likes):
                like = re.search(reg,likes).group()
                like_count = int(float(like) * 1000000)
            else:
                like_count = re.search(reg,likes).group()
        except Exception as e:
            print("_extract_profile_reaction: An error occur while trying to get like_count ",str(e))
            try:
                likes_btn = item.find_element_by_xpath("//div[@class='bp9cbjyn j83agx80 buofh1pr ni8dbmo4 stjgntxs']/span/span/span/span/span/div")
                time.sleep(0.3)
                webdriver.ActionChains(self.browser).move_to_element(likes_btn).perform()
                time.sleep(0.3)
                self.browser.execute_script("arguments[0].click();", likes_btn)
                time.sleep(1)
                likes = item.find_element_by_xpath("//div[@class='ni8dbmo4 stjgntxs kr9hpln1']/div/span/span").get_attribute("innerText")
                print("_extract_profile_reaction: after click popup reaction ----value---> ", likes.get_attribute("innerText"))
            except Exception:
                like_count = 0
        # like_count = re.search(reg,likes).group()
        # if likes == None:
        #     like_count =0
        time.sleep(0.5)
        self.click_esc_key()
        time.sleep(0.3)
        print("like counts ------------> ",like_count)
        return int(like_count)


    def _extract_profile_comments(self, item):

        try:
            comments = item.find_element_by_css_selector(cmt_count_selector).get_property("textContent")
            if "shares" in comments or 'share' in comments:
                comment_count = 0
                print("comment count ----------> ",comment_count)
                return comment_count
            # print("raw comments ----------------> ",comments)
            reg = r"\d+|\d+\.\d+"
            if re.search(r"k|K",comments):
                comment = re.search(reg,comments).group()
                comment_count = int(float(comment) * 1000)
            elif re.search(r"m|M",comments):
                comment = re.search(reg,comments).group()
                comment_count = int(float(comment) * 1000000)
            else:
                comment_count = re.search(reg,comments).group()
        except Exception as e:
            print("An error occur while trying to get comment_count ",str(e))
            comment_count = 0
            time.sleep(0.5)
        print("comment counts --------------> ",comment_count)
        return int(comment_count)


    def _scroll_profile_post(self, total_posts, sleep_times):
        # # last_count = 0
        match = False
        height = 1000
        count = 0
        old_length = 0
        # To prevent session crash issue
        self.browser.set_page_load_timeout(1000)

        while not match:
            # for scroll in range(total_posts):
            # last_count += 1

            self.click_esc_key()
            # wait for the browser to load, this time can be changed slightly ~3 seconds with no difference, but 5 seems
            # to be stable enough
            time.sleep(1)

            self.browser.execute_script(
                f"window.scrollTo(0, {height})")

            time.sleep(sleep_times)
            articles = self.browser.find_elements_by_xpath("//div[@class = 'lzcic4wl']")

            print(f"========================SCROLLING======height=={height}================", len(articles))
            height += 1000

            if (old_length == len(articles)):
                count += 1
            else:
                old_length = len(articles)
                count = 0

            if len(articles) - 2 >= total_posts or count >= 4:
                match = True


        time.sleep(0.5)
        self.browser.execute_script(
            "window.scrollTo(document.body.scrollHeight,0)")
        # self.browser.execute_script("window.scrollBy(0,document.body.scrollHeight)")
        time.sleep(1)


    def get_publish_at(self, content):
        year_reg = r"[1][9][9][0-9]|[2][0][0-9][0-9]"
        month_reg = r"\d*\s*January\s*\d*|\d*\s*February\s*\d*|\d*\s*March\s*\d*|\d*\s*April\s*\d*|\d*\s*May\s*\d*|\d*\s*June\s*\d*|\d*\s*July\s*\d*|\d*\s*August\s*\d*|\d*\s*September\s*\d*|\d*\s*October\s*\d*|\d*\s*November\s*\d*|\d*\s*December\s*\d*"
        published_date = ''
        if re.search(month_reg,content):
            try:
                day = re.search(r"\d+",re.search(month_reg,content).group()).group()
                month_name = re.sub(r"\d+","",re.search(month_reg,content).group())
                month_name = month_name.strip()
                date_obj = datetime.datetime.strptime(month_name,"%B")
                month = date_obj.month

                if re.search(r"\d+:\d+\s*A*M*|\d+:\d+\s*P*M*|\d+:\d+\s*[Aa]*[Mm]*|\d+:\d+\s*[Pp]*[Mm]*",content):
                    hr = re.search(r"\d+|\d+",re.search(r"\d+:\d+\s*A*M*|\d+:\d+\s*P*M*|\d+:\d+\s*[Aa]*[Mm]*|\d+:\d+\s*[Pp]*[Mm]*",content).group()).group()
                    mins = re.search(r":\d+",content).group()
                    mins = re.sub(r":","",mins)
                    if re.search(r"[Aa][Mm]|[Pp][Mm]",content):
                        print("time found")
                        am_pm = re.search(r"[Aa][Mm]|[Pp][Mm]",content).group()
                        print(am_pm)
                        am_pm = am_pm.upper()
                        if am_pm == "PM":
                            hr = int(hr) + 12
                else:
                    hr , mins , secs = "00","00","00"
                if re.search(year_reg,content):
                    year = re.search(year_reg,content).group()
                else:
                    year = datetime.datetime.now().strftime("%Y")
                published_date = f"{year}-{month}-{day} {hr}:{mins}:00"
                print("published_date ---------------------> ",published_date)
                return published_date
            except Exception as e:
                print(f"An error occur while trying to get timestamp at month format : {e}")
                with open("error_time_formats.txt",'a') as obj:
                    obj.write(content)
                    obj.write("\n")
                # print(published_date)
                return published_date
        elif re.search(r"yesterday|Yesterday",content):
            try:
                dateobj = datetime.datetime.strftime(datetime.datetime.now()- datetime.timedelta(1),r"%Y-%m-%d")
                year , month , day = dateobj.split("-")
                hr = re.search(r"\d+",content).group()
                mins = re.search(r":\d+",content).group()
                mins = re.sub(r":","",mins)
                published_date = f"{year}-{month}-{day} {hr}:{mins}:00"
                print("published_date ---------------------> ",published_date)
                return published_date
            except Exception as e:
                print(f"An error occur while trying to get timestamp at yesterday format: {e}")
                # print(published_date)
                with open("error_time_formats.txt",'a') as obj:
                    obj.write(content)
                    obj.write("\n")
                return published_date
        elif re.search(r"today|Today",content):
            try:
                dateobj = datetime.datetime.strftime(datetime.datetime.now(),r"%Y-%m-%d")
                year , month , day = dateobj.split("-")
                hr = "00"
                mins = "00"
                published_date = f"{year}-{month}-{day} {hr}:{mins}:00"
                print("published_date ---------------------> ",published_date)
                return published_date
            except Exception as e:
                print(f"An error occur while trying to get timestamp at today format: {e}")
                # print(published_date)
                with open("error_time_formats.txt",'a') as obj:
                    obj.write(content)
                    obj.write("\n")
                return published_date
        elif re.search(r"\d{4}", content):
            return content
        else:
            # splited_value = content.split('')
            try:
                # time_type = splited_value[1]
                time_reg = r"\d+\s*h|\d+\s*hr|\d+\s*hrs|\d+\s*m|\d+\s*min|\d+\s*mins|\d+\s*d|\d+\s*day|\d+\s*days"
                time_type = re.search(time_reg,content).group()
                if(re.search(r"h|hr|hrs",time_type)):
                    # total_hours = int(splited_value[0])
                    total_hours = int(re.search(r"\d+",time_type).group())
                    published_date = datetime.datetime.now() - datetime.timedelta(hours=total_hours)
                    formatted_published_at = published_date.strftime("%Y-%m-%d %H:00:00")
                    print(formatted_published_at)
                    return formatted_published_at
                elif(re.search(r"m|min|mins",time_type)):
                    # total_minutes = int(splited_value[0])
                    total_minutes = int(re.search(r"\d+",time_type).group())
                    published_date = datetime.datetime.now() - datetime.timedelta(minutes=total_minutes)
                    formatted_published_at = published_date.strftime("%Y-%m-%d %H:%M:%S")
                    print("Published_date ---------------------->",formatted_published_at)
                    return formatted_published_at
                elif(re.search(r"d|day|days",time_type)):
                    # total_days = int(splited_value[0])
                    total_days = int(re.search(r"\d+",time_type).group())
                    published_date = datetime.datetime.now() - datetime.timedelta(days=total_days)
                    formatted_published_at = published_date.strftime(r"%Y-%m-%d 00:00:00")
                    print("published date ---------------------->",formatted_published_at)
                    return formatted_published_at
            except Exception as e:
                print(f"An error occur while trying to get timestamp at hr/min/day format: {e}")
                # print(published_date)
                with open("error_time_formats.txt",'a') as obj:
                    obj.write(content)
                    obj.write("\n")
                return published_date


    def click_see_more_button(self, post):
        try:
            see_more = post.find_element_by_xpath(profile_click_see_more_selector)
            webdriver.ActionChains(self.browser).move_to_element(see_more).perform()
            time.sleep(0.5)
            self.browser.execute_script("arguments[0].click();", see_more)
            time.sleep(0.7)
        except Exception as e:
            print("An error occur while trying to click see_more button : ",str(e))
            try:
                see_more = post.find_element_by_css_selector(profile_click_see_more_default_selector)
                webdriver.ActionChains(self.browser).move_to_element(see_more).perform()
                time.sleep(0.5)
                self.browser.execute_script("arguments[0].click();", see_more)
                time.sleep(0.5)
            except Exception as e:
                print("An error occur while trying to click see_more button : ",str(e))


    def click_others_link(self, item):
        try:
            others_link = item.find_element_by_xpath(profile_click_others_selector)
            # print("=============itemitemitemitemitemitem==========", item.get_attribute('innerHTML'))
            # print("=============others_linkothers_linkothers_link==========", others_link.get_attribute('innerHTML'))

            time.sleep(0.5)
            webdriver.ActionChains(self.browser).move_to_element(others_link).perform()
            self.browser.execute_script("arguments[0].click();", others_link)
            time.sleep(0.7)
        except Exception as e:
            print("An error occur while trying to click others link : ",str(e))


    def quit_driver_and_pickup_children(self):
        self.browser.quit()
        try:
            pid = True
            while pid:
                pid = os.waitpid(-1, os.WNOHANG)
                try:
                    if pid[0] == 0:
                        pid = False
                except Exception as e:
                    print(str(e))
                    pass

        except Exception as e:
            print(str(e))
            pass

    def tearDown(self):
        if self.browser is None:
            return
        self.quit_driver_and_pickup_children()


def parse_date(content):
    year_reg = r"[1][9][9][0-9]|[2][0][0-9][0-9]"
    month_reg = r"\d*\s*January\s*\d*|\d*\s*February\s*\d*|\d*\s*March\s*\d*|\d*\s*April\s*\d*|\d*\s*May\s*\d*|\d*\s*June\s*\d*|\d*\s*July\s*\d*|\d*\s*August\s*\d*|\d*\s*September\s*\d*|\d*\s*October\s*\d*|\d*\s*November\s*\d*|\d*\s*December\s*\d*"
    published_date = ''
    if re.search(month_reg,content):
        try:
            day = re.search(r"\d+",re.search(month_reg,content).group()).group()
            month_name = re.sub(r"\d+","",re.search(month_reg,content).group())
            month_name = month_name.strip()
            date_obj = datetime.datetime.strptime(month_name,"%B")
            month = date_obj.month

            if re.search(r"\d+:\d+\s*A*M*|\d+:\d+\s*P*M*|\d+:\d+\s*[Aa]*[Mm]*|\d+:\d+\s*[Pp]*[Mm]*",content):
                hr = re.search(r"\d+|\d+",re.search(r"\d+:\d+\s*A*M*|\d+:\d+\s*P*M*|\d+:\d+\s*[Aa]*[Mm]*|\d+:\d+\s*[Pp]*[Mm]*",content).group()).group()
                mins = re.search(r":\d+",content).group()
                mins = re.sub(r":","",mins)
                if re.search(r"[Aa][Mm]|[Pp][Mm]",content):
                    print("time found")
                    am_pm = re.search(r"[Aa][Mm]|[Pp][Mm]",content).group()
                    print(am_pm)
                    am_pm = am_pm.upper()
                    if am_pm == "PM":
                        hr = int(hr) + 12
            else:
                hr , mins , secs = "00","00","00"
            if re.search(year_reg,content):
                year = re.search(year_reg,content).group()
            else:
                year = datetime.datetime.now().strftime("%Y")
            published_date = f"{year}-{month}-{day} {hr}:{mins}:00"
            print("published_date ---------------------> ",published_date)
            return published_date
        except Exception as e:
            print(f"An error occur while trying to get timestamp at month format : {e}")
            with open("error_time_formats.txt",'a') as obj:
                obj.write(content)
                obj.write("\n")
            # print(published_date)
            return published_date
    elif re.search(r"\d{4}", content):
        return content
    elif re.search(r"yesterday|Yesterday",content):
        try:
            dateobj = datetime.datetime.strftime(datetime.datetime.now()- datetime.timedelta(1),r"%Y-%m-%d")
            year , month , day = dateobj.split("-")
            hr = re.search(r"\d+",content).group()
            mins = re.search(r":\d+",content).group()
            mins = re.sub(r":","",mins)
            published_date = f"{year}-{month}-{day} {hr}:{mins}:00"
            print("published_date ---------------------> ",published_date)
            return published_date
        except Exception as e:
            print(f"An error occur while trying to get timestamp at yesterday format: {e}")
            # print(published_date)
            with open("error_time_formats.txt",'a') as obj:
                obj.write(content)
                obj.write("\n")
            return published_date
    else:
        # splited_value = content.split('')
        try:
            # time_type = splited_value[1]
            time_reg = r"\d+\s*h|\d+\s*hr|\d+\s*hrs|\d+\s*m|\d+\s*min|\d+\s*mins|\d+\s*d|\d+\s*day|\d+\s*days"
            time_type = re.search(time_reg,content).group()
            if(re.search(r"h|hr|hrs",time_type)):
                # total_hours = int(splited_value[0])
                total_hours = int(re.search(r"\d+",time_type).group())
                published_date = datetime.datetime.now() - datetime.timedelta(hours=total_hours)
                formatted_published_at = published_date.strftime("%Y-%m-%d %H:00:00")
                print(formatted_published_at)
                return formatted_published_at
            elif(re.search(r"m|min|mins",time_type)):
                # total_minutes = int(splited_value[0])
                total_minutes = int(re.search(r"\d+",time_type).group())
                published_date = datetime.datetime.now() - datetime.timedelta(minutes=total_minutes)
                formatted_published_at = published_date.strftime("%Y-%m-%d %H:%M:%S")
                print("Published_date ---------------------->",formatted_published_at)
                return formatted_published_at
            elif(re.search(r"d|day|days",time_type)):
                # total_days = int(splited_value[0])
                total_days = int(re.search(r"\d+",time_type).group())
                published_date = datetime.datetime.now() - datetime.timedelta(days=total_days)
                formatted_published_at = published_date.strftime(r"%Y-%m-%d 00:00:00")
                print("published date ---------------------->",formatted_published_at)
                return formatted_published_at
        except Exception as e:
            print(f"An error occur while trying to get timestamp at hr/min/day format: {e}")
            # print(published_date)
            with open("error_time_formats.txt",'a') as obj:
                obj.write(content)
                obj.write("\n")
            return published_date