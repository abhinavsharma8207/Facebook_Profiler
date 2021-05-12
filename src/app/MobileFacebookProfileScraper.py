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

from .MobileElementSelectors import *


regex_query_remove_url = r'https?:\/\/[^\s]*[\r\n]*'
regex_patt_hashtag = r'\s(#[^\s]+)'
regex_patt_mention = r'(@[^\s]+)'

DB_PATH = '/app/database/'


class MobileFacebookProfileScraper:
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

        response, intro_dict = self._extract_profile_html(profile)


        self.browser.close()
        return response, intro_dict

    def check_height(self, old_height):
        new_height = self.browser.execute_script("return document.body.scrollHeight")
        return new_height != old_height


    def _extract_profile_html(self, profile):
        #Getting Intro
        intro_dict = dict()

        # Skip to the post index directly
        articles = self.browser.find_elements_by_xpath(articles_selector)

        # source_data = self.browser.page_source
        # Throw your source into BeautifulSoup and start parsing!
        # bs_data = bs(source_data, 'html.parser')
        # print("bs_databs_databs_databs_data", bs_data)


        post_dict_list = dict()
        extra_post_dict_list = list()

        ''' Skip to desire post number.Only use when large amount of posts are crawled '''
        # posts = posts[current_post_index:] ## Can use desire number.
        for index, item in enumerate(articles):
            post_dict = dict()
            # scroll user into view
            content_header, content_footer, content_footer_text = self._extract_profile_post_text(item)
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
                post_dict['location'] = self._extract_profile_checkin_location(item)
                post_dict['place'] = self._extract_profile_checkin_location(item)
                post_dict['mentions'] = list([])
                post_dict['datestamp'] = post_time
                post_dict['urls'] = self._extract_url_from_post(content_header)
                post_dict['photos'] = content_footer["img_links"]
                post_dict['profile_image_url'] = ''
                if content_header != "":
                    post_dict['facebook_post'] = content_header
                else:
                    post_dict['facebook_post'] = content_footer_text
                post_dict['hashtags'] = self._extract_hashtags(content_header)
                post_dict['reaction'] = self._extract_profile_reaction(item)
                post_dict['image_paths'] = None
                post_dict['video_url'] = content_footer["video_links"]
                post_dict['location_country'] = None
                post_dict['location_address'] = None
                post_dict['place_country'] = None
                post_dict['place_address'] = None
                post_dict['post_no_urls'] = self.remove_urls(content_header)
                post_dict['post_no_urls_mentions'] = self.remove_urls_mentions(content_header)

                #Extra Information
                if bool(content_footer["extra_info"]):
                    extra_post_dict_list.append(post_dict)

                post_dict_list[conversation_id] = post_dict


        # Add extra information
        for extra_info in extra_post_dict_list:
            link = f"https://m.facebook.com/{extra_info['user_id']}/posts/pcb.{extra_info['id']}"
            self.browser.get(link)
            time.sleep(3)

            video_links, img_links = self._extract_album()
            extra_info['photos'] = img_links
            extra_info['video_url'] = video_links

            post_dict_list[extra_info["id"]] = extra_info



        print("=======================TOTAL ITEMS:==========================", len(articles))
        response = post_dict_list.values()
        return list(response), intro_dict


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
            date_content = item.find_element_by_css_selector(date_content_selector).text
            print("post_time: ", date_content)

            return self.get_publish_at(date_content)
        except (NoSuchElementException, StaleElementReferenceException) as error:
            return None

    def _extract_profile_checkin_location(self, item):
        try:
            location = item.find_element_by_css_selector(location_content_selector).get_attribute("innerText")
            print("location: ", location)

            return location
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
            author_name = item.find_element_by_css_selector(profile_author_name_other_text_selector).get_property("textContent")
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
                time.sleep(0.3)
                webdriver.ActionChains(self.browser).move_to_element(other_link).perform()
                time.sleep(0.5)

                tooltips = self.browser.find_element_by_css_selector("span[role='tooltip']")
                # moving mouse to other place -> reload tooltip
                webdriver.ActionChains(self.browser).move_by_offset(10, 20).perform()

                persons.extend(tooltips.text.splitlines())

            return persons, locations

        except (NoSuchElementException, StaleElementReferenceException) as error:
            print("Error retrieving mentions, checkin places: ",str(error))

        self.click_esc_key()
        return persons, locations


    def _extract_profile_owner_id_link(self, item):
        owner_link = item.find_element_by_xpath(profile_user_id_link_selector).get_attribute("href")
        owner_link_sanitize = owner_link.split("?")[0]
        owner_id = os.path.basename(os.path.normpath(owner_link_sanitize))
        return owner_link_sanitize,owner_id


    def _extract_profile_post_text(self, item):

        # print("=================================================================================================================")
        # print("=============_extract_profile_post_text==========", item.get_attribute('innerHTML'))
        # print("=================================================================================================================")
        content_header = ""
        content_footer = dict()
        content_footer_text = ""
        video_links = []
        embedded_links = []
        img_links = []
        # Extract post content header
        self.browser.set_page_load_timeout(1000)
        stale_element = True
        extra_info = False

        while stale_element:
            try:
                post_content = item.find_element_by_css_selector(profile_post_content_up_selector)
                print("post_content: ", post_content.text)
                content_header = self.get_see_more_content(item, post_content)
                stale_element = False
            except (NoSuchElementException) as error:
                try:
                    print("Exception post_content ----> exception: ", error)
                    post_content= item.find_element_by_css_selector(profile_post_content_up_1_selector)
                    print("post_content - profile_post_content_up_1_selector: ", post_content.text)
                    content_header = self.get_see_more_content(item, post_content)
                    stale_element = False
                except (NoSuchElementException) as error:
                    try:
                        print("Exception post_content ----> exception: ", error)
                        post_content = item.find_element_by_css_selector(profile_post_content_up_2_selector)
                        print("post_content - profile_post_content_up_2_selector: ", post_content.text)
                        content_header = self.get_see_more_content(item, post_content)
                        stale_element = False
                    except (NoSuchElementException) as error:
                        print("Exception post_content ----> None: ", error)
                        stale_element = False

            except (StaleElementReferenceException) as error:
                stale_element = True


        try:
            # Extract post content footer
            # WebDriverWait(self.browser, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, profile_post_content_down_selector)))
            WebDriverWait(self.browser,100).until(
                lambda x: x.find_element(By.CSS_SELECTOR, profile_post_content_down_selector)
            )
            post_content_footer = item.find_element_by_css_selector(profile_post_content_down_selector)
            print("post_content_footer ---------->", post_content_footer.get_attribute("innerText"))
            content_footer_text = post_content_footer.get_attribute("innerText")

            # Extract single Uploaded Video from post content
            try:
                video_link = post_content_footer.find_element_by_css_selector("div[data-sigil='inlineVideo']").get_attribute("data-store")
                if not not video_link:
                    video_link_dict = json.loads(video_link)
                    print("getting video_link_dict -------------->", video_link_dict)
                    video_links.append(video_link_dict["src"])

            except (NoSuchElementException, StaleElementReferenceException) as error:
                print("post don't have video upload: ", error)

            # Extract embedded link from post content
            try:
                embedded_link = post_content_footer.find_element_by_css_selector("a[data-sigil='show-save-caret-nux-on-click MLynx_asynclazy']").get_attribute("href")
                print("getting embedded_link -------------->", embedded_link)
                if not not embedded_link:
                    parsed = urlparse.urlparse(embedded_link)
                    print("getting embedded_src -------------->", parse_qs(parsed.query)['u'][0])
                    embedded_links.append(parse_qs(parsed.query)['u'][0])

            except (NoSuchElementException, StaleElementReferenceException) as error:
                print("post don't have embedded link: ", error)

            # Extract single uploaded image
            try:
                img_url_element = post_content_footer.find_element_by_css_selector("div[class='_5uso _5t8z'] > a > div > div > i").value_of_css_property("background-image")
                print("========-img_url_element----------------->", img_url_element)

                if not not img_url_element:
                    print("getting full imgsrc -------------->", str(img_url_element).lstrip('url("').rstrip('")'))
                    img_links.append(str(img_url_element).lstrip('url("').rstrip('")'))

            except (NoSuchElementException, StaleElementReferenceException) as error:
                print("post don't have image: ", error)

            # Extract multiple uploaded image or videos
            try:
                # multiple_imgs_videos = WebDriverWait(self.browser, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class='_-_a _5t8z']")))
                multiple_imgs_videos = post_content_footer.find_elements_by_css_selector("div[class='_-_a _5t8z'] > div > a")
                if len(multiple_imgs_videos) > 1:
                    extra_info = True

            except (NoSuchElementException, StaleElementReferenceException) as error:
                print("post don't have image group: ", error)

        except (NoSuchElementException, StaleElementReferenceException) as error:
            print("post content footer not available: ", error)

        content_footer["embedded_link"] = embedded_links
        content_footer["video_links"] = video_links
        content_footer["img_links"] = img_links
        content_footer["extra_info"] = extra_info
        return content_header, content_footer, content_footer_text


    def _extract_album(self):
        video_links = []
        img_links = []
        try:
            album_elements = self.browser.find_elements_by_xpath("//div[@class='_56be']")
            print("-----len album ------------------>", len(album_elements))
            for album_element in album_elements:
                try:
                    video_links.append(album_element.find_element_by_tag_name("video").get_attribute("src"))
                    print("video group ------------>", album_element.find_element_by_tag_name("video").get_attribute("src"))
                except (NoSuchElementException, StaleElementReferenceException) as error:
                    img_links.append(album_element.find_element_by_tag_name("img").get_attribute("src"))
                    print("image group ------------->", album_element.find_element_by_tag_name("img").get_attribute("src"))

        except (NoSuchElementException, StaleElementReferenceException) as error:
            print("post don't have image group: ", error)

        return video_links, img_links


    def get_see_more_content(self, item, post_content):
        # print("================get_see_more_content==========html==", item.get_attribute('innerHTML'))
        response = post_content.text
        if re.search('… More', post_content.text, re.IGNORECASE):
            self.click_see_more_button(post_content)
            try:
                post_content = item.find_element_by_css_selector(profile_post_content_up_selector)
                print("after click see more - post_content: ", post_content.text)
                response = post_content.text

            except (NoSuchElementException, StaleElementReferenceException) as error:
                try:
                    post_content = item.find_element_by_css_selector(profile_post_content_up_1_selector)
                    print("after click see more - post_content: ", post_content.text)
                    response = post_content.text

                except (NoSuchElementException, StaleElementReferenceException) as error:
                    try:
                        print("Exception post_content ----> exception: ", error)
                        post_content = item.find_element_by_css_selector(profile_post_content_up_2_selector)

                        response = post_content.text
                    except (NoSuchElementException, StaleElementReferenceException) as error:
                        return ""

        return re.sub('See translation', '', response)


    def _extract_profile_link(self, item):
        try:
            int_conversation_id = 0
            url = item.find_element_by_css_selector(post_link_selector).get_attribute("href")
            time.sleep(0.2)
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
            like_count = 0

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
                f"window.scrollTo(0, document.body.scrollHeight)")

            time.sleep(sleep_times)
            articles = self.browser.find_elements_by_xpath(articles_selector)

            print(f"========================SCROLLING========================", len(articles))

            if (old_length == len(articles)):
                count += 1
            else:
                old_length = len(articles)
                count = 0

            if len(articles) - 2 >= total_posts or count >= 2:
                match = True

        time.sleep(0.5)
        self.browser.execute_script(
            "window.scrollTo(document.body.scrollHeight,0)")
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
            see_more = post.find_element_by_css_selector(profile_click_see_more_selector)
            webdriver.ActionChains(self.browser).move_to_element(see_more).click().perform()
            # time.sleep(0.5)
            # self.browser.execute_script("arguments[0].click();", see_more)
            time.sleep(0.7)
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

