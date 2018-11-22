from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import urllib.request
import time
import json
from pymongo import MongoClient


userid = "akkimysite@gmail.com"
password = "anzcallahan"

timestamp = int(time.time())
ch = os.getcwd() + '/tools/chromedriver'
options = Options()
options.add_argument("log-level=3")
driver = webdriver.Chrome(options=options, executable_path=ch)
wait = WebDriverWait(driver, 10)
driver.implicitly_wait(0.5)
driver.get("https://www.linkedin.com/")
errors = {}
client = MongoClient('mongodb://developer:5cr4p3r18@devserver.nulabs.it:27027/scraperDb')
scraperDb = client.scraperDb

def search_profile_url(searchType, keyword, page):
    keyword = "%20".join(keyword.split())
    return 'https://www.linkedin.com/search/results/' + searchType.lower() + '/?keywords=' + keyword + '&origin=GLOBAL_SEARCH_HEADER&page=' + str(page)

def search_job_url(searchType, keyword, location, start=0):
    keyword = "%20".join(keyword.split())
    return 'https://www.linkedin.com/jobs/search/?keywords=' + keyword + '&location=' + "%2C%20".join(location.split(",")) + '&start=' + str(start)


def login():
    wait.until(EC.presence_of_element_located((By.ID, "login-submit")))
    driver.find_element_by_id("login-email").send_keys(userid)
    driver.find_element_by_id("login-password").send_keys(password)
    driver.find_element_by_id("login-submit").click()


def special_exp_scrape(li, ul):
    try:
        obj = {}
        text = li.text.split("\n")
        if text[0] == "Company Name":
            obj["company"] = text[1]
        try:
            obj["linkToCompany"] = li.find_element_by_tag_name(
                "a").get_attribute("href")
        except:
            obj["linkToCompany"] = "NA"
        if text[2] == "Total Duration":
            obj["totalDuration"] = text[3]
        obj["roles"] = []
        for x in ul.find_elements_by_css_selector("div.pv-entity__role-details-container"):
            temp = {}
            content = x.text.split("\n")
            temp["title"] = content[1]
            if len(text) > 2:
                for i in range(2, len(text), 2):
                    if text[i] == "Dates Employed":
                        temp["dates"] = text[i+1]
                    if text[i] == "Employment Duration":
                        temp["duration"] = text[i+1]
                    if text[i] == "Location":
                        temp["location"] = text[i+1]
            obj["roles"].append(temp)
        return obj
    except:
        return -1


def normal_exp_scrape(li):
    try:
        obj = {}
        text = li.text.split("\n")
        obj["company"] = text[2]
        try:
            obj["linkToCompany"] = li.find_element_by_tag_name("a").get_attribute("href")
        except:
            obj["linkToCompany"] = "NA"
        obj["title"] = text[0]
        if len(text) > 3:
            for i in range(3, len(text), 2):
                if text[i] == "Dates Employed":
                    obj["dates"] = text[i+1]
                if text[i] == "Employment Duration":
                    obj["duration"] = text[i+1]
                if text[i] == "Location":
                    obj["location"] = text[i+1]
        return obj
    except Exception as e:
        print(e)
        return -1


def scrape_experiences():
    exp_sec = ""
    try:
        exp_sec = driver.find_element_by_id("experience-section")
    except:
        return "NA"
    while True:
        try:
            exp_sec = driver.find_element_by_id("experience-section")
            el = exp_sec.find_element_by_class_name("pv-profile-section__see-more-inline")
            driver.execute_script("arguments[0].click();", el)
        except:
            break
    exp_sec = driver.find_element_by_id("experience-section")
    ul = exp_sec.find_element_by_tag_name("ul")
    exps = []
    for li in ul.find_elements_by_css_selector("li.pv-profile-section"):
        try:
            inner_ul = li.find_element_by_tag_name("ul")
            temp = special_exp_scrape(li, inner_ul)
            if temp == -1:
                continue
            exps.append(temp)
        except:
            temp = normal_exp_scrape(li)
            if temp == -1:
                continue
            exps.append(normal_exp_scrape(li))
    return exps


def scrape_education():
    edu_sec = ""
    try:
        edu_sec = driver.find_element_by_id("education-section")
    except:
        return "NA"
    while True:
        try:
            edu_sec = driver.find_element_by_id("education-section")
            el = edu_sec.find_element_by_class_name("pv-profile-section__see-more-inline")
            driver.execute_script("arguments[0].click();", el)
        except:
            break
    edu_sec = driver.find_element_by_id("education-section")
    ul = edu_sec.find_element_by_tag_name("ul")
    edu = []
    for li in ul.find_elements_by_css_selector("li.pv-profile-section__section-info-item"):
        obj = {}
        text = li.text.split("\n")
        obj["institution"] = text[0]
        try:
            obj["linkToInstitution"] = li.find_element_by_tag_name(
                "a").get_attribute("href")
        except:
            obj["linkToInstitution"] = "NA"
        if len(text) > 1:
            for i in range(1, len(text), 2):
                if text[i] == "Degree Name":
                    obj["degree"] = text[i+1]
                if text[i] == "Field Of Study":
                    obj["fieldOfStudy"] = text[i+1]
                if "Dates" in text[i]:
                    obj["duration"] = text[i+1]
        edu.append(obj)
    return edu


def scrape_skills():
    skills = ""
    try:
        skills = driver.find_element_by_class_name("pv-skill-categories-section")
    except:
        return "NA"
    try:
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.pv-skills-section__additional-skills"))).click()
    except Exception as e:
        print(e)
    skillsArray = []
    for li in skills.find_elements_by_css_selector("li.pv-skill-category-entity"):
        try:
            temp = {}
            name = li.find_element_by_css_selector("div.pv-skill-category-entity__skill-wrapper")
            values = name.text.split("\n")
            temp["skill"] = values[0]
            try:
                count = name.find_element_by_class_name("pv-skill-category-entity__endorsement-count").text
                if count == "99+":
                    count = 99
                temp["endorsements"] = int(count)
            except:
                temp["endorsements"] = 0
            skillsArray.append(temp)
        except:
            continue
    return skillsArray


def scrape_recommendations(rec_sec):
    try:
        ul = rec_sec.find_element_by_tag_name("ul")
    except:
        return "NA"
    while True:
        try:
            driver.execute_script("arguments[0].click();", rec_sec.find_element_by_class_name("pv-profile-section__see-more-inline"))
        except:
            break
    recs = []
    for li in ul.find_elements_by_css_selector("li.pv-recommendation-entity"):
        temp = {}
        text = li.text.split("\n")
        temp["name"] = text[0]
        try:
            temp["linkToProfile"] = li.find_element_by_tag_name("a").get_attribute("href")
        except:
            temp["linkToProfile"] = "NA"
        temp["headline"] = text[1]
        temp["date"] = ",".join(text[2].split(",")[:2])
        temp["relation"] = text[2].split(",")[2]
        temp["content"] = " ".join(text[3:])
        recs.append(temp)
    return recs

def scrape_hardest(el, heading):
    temp = {}
    if heading == "honors":
        try:
            temp["title"] = el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
        try:
            temp["date"] = el.find_element_by_class_name("pv-accomplishment-entity__date").text.split("\n")[1]
        except:
            temp["date"] = "NA"
        try:
            temp["issuer"] = el.find_element_by_class_name("pv-accomplishment-entity__issuer").text.split("\n")[1]
        except:
            temp["issuer"] = "NA"
        try:
            temp["description"] = " ".join(el.find_element_by_class_name("pv-accomplishment-entity__description").text.split("\n")[1:])
        except:
            temp["description"] = "NA"
    if heading == "certifications":
        try:    
            temp["name"] = el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
        try:
            temp["date"] = el.find_element_by_class_name("pv-accomplishment-entity__date").text.split("\n")[1]
        except:
            temp["date"] = "NA"
        try:
            temp["license"] = el.find_element_by_class_name("pv-accomplishment-entity__license").text
        except:
            temp["license"] = "NA"
        try:
            temp["issuer"] = el.find_element_by_class_name("pv-accomplishment-entity__photo").text.split("\n")[1]
        except:
            temp["issuer"] = "NA"
    if heading == "projects":
        try:
            temp["title"] = el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
        try:
            temp["date"] = el.find_element_by_class_name("pv-accomplishment-entity__date").text.split("\n")[1]
        except:
            temp["date"] = "NA"
        try:
            temp["description"] = " ".join(el.find_element_by_class_name("pv-accomplishment-entity__description").text.split("\n")[1:])
        except:
            temp["description"] = "NA"
    if heading == "publications":
        try:
            temp["name"] = el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
        try:
            temp["date"] = el.find_element_by_class_name("pv-accomplishment-entity__date").text.split("\n")[1]
        except:
            temp["date"] = "NA"
        try:
            temp["publisher"] = el.find_element_by_class_name("pv-accomplishment-entity__publisher").text.split("\n")[1]
        except:
            temp["publisher"] = "NA"
        try:
            temp["description"] = " ".join(el.find_element_by_class_name("pv-accomplishment-entity__description").text.split("\n")[1:])
        except:
            temp["description"] = "NA"
    if heading == "testScores":
        try:
            temp["name"] = el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
        try:
            temp["date"] = el.find_element_by_class_name("pv-accomplishment-entity__date").text.split("\n")[1]
        except:
            temp["date"] = "NA"
        try:
            temp["score"] = el.find_element_by_class_name("pv-accomplishment-entity__score").text.split("\n")[1]
        except:
            temp["score"] = "NA"
        try:
            temp["description"] = " ".join(el.find_element_by_class_name("pv-accomplishment-entity__description").text.split("\n")[1:])
        except:
            temp["description"] = "NA"
    if heading == "languages":
        try:
            return el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
    if heading == "courses":
        try:
            temp["name"] = el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
        try:
            temp["courseNumber"] = el.find_element_by_class_name("pv-accomplishment-entity__course-number").text.split("\n")[1]
        except:
            temp["courseNumber"] = "NA"
    if heading == "organizations":
        try:
            temp["name"] = el.find_element_by_class_name("pv-accomplishment-entity__title").text.split("\n")[1]
        except:
            return -1
        try:
            temp["date"] = el.find_element_by_class_name("pv-accomplishment-entity__date").text.split("\n")[1]
        except:
            temp["date"] = "NA"
        try:
            temp["position"] = el.find_element_by_class_name("pv-accomplishment-entity__position").text.split("\n")[1]
        except:
            temp["position"] = "NA"
    return temp

def scrape_accomplishments():
    i = 0
    temp = {}
    acc = driver.find_element_by_class_name("pv-accomplishments-section")
    for sec in acc.find_elements_by_css_selector("section.pv-accomplishments-block"):
        driver.execute_script('document.querySelector(".pv-accomplishments-section").querySelectorAll(".pv-accomplishments-block__expand")[' + str(i) + '].click()')    
        heading = sec.find_element_by_css_selector("h3.pv-accomplishments-block__title").text.lower()
        if "honors" in heading:
            heading = "honors"
        if "test" in heading:
            heading = "test-scores"
        while True:
            try:
                driver.execute_script("arguments[0].click();", sec.find_element_by_css_selector("button.pv-profile-section__see-more-inline"))
            except:
                break
        if heading[-1] != "s":
            heading += "s"
        try:
            new_sec = driver.find_element_by_class_name(heading)    
        except:
            continue
        if heading == "test-scores":
            heading = "testScores"
        temp[heading] = []
        for li in new_sec.find_elements_by_class_name("pv-accomplishment-entity--expanded"):
            lo = scrape_hardest(li, heading)
            if lo == -1:
                continue
            temp[heading].append(lo)
        driver.execute_script('document.querySelector(".pv-accomplishments-section").querySelectorAll(".pv-accomplishments-block__expand")[' + str(i) + '].click()')    
        i += 1
    return temp

def scrape_current(x):
    arr = []
    for li in driver.find_elements_by_class_name("entity-list-item"):
        temp = {}
        text = li.text.split("\n")
        try:
            if x != "groups":
                temp["name"] = text[0]
                temp["link"] = li.find_element_by_tag_name("a").get_attribute("href")
                temp["followers"] = int("".join(text[-2][:-9].split(",")))
            else:
                temp["name"] = text[0]
                temp["link"] = li.find_element_by_tag_name("a").get_attribute("href")
                temp["members"] = int("".join(text[-1][:-7].split(",")))
        except:
            continue
        arr.append(temp)
    return arr


def scrape_interests():
    modal = driver.find_element_by_tag_name("artdeco-modal")
    nav = modal.find_element_by_tag_name("nav")
    i = 0
    interests = {}
    links = []
    seq = []
    for a in nav.find_elements_by_tag_name("a"):
        links.append(a.get_attribute("href"))
        interests[a.text.lower()] = []
        seq.append(a.text.lower())
    for link in links:
        if i != 0:
            driver.get(link)
        interests[seq[i]] = scrape_current(seq[i])
        i += 1
    return interests

def scroll_all():
    profile_scroll = 100
    prevTop = -1
    while True:
        driver.execute_script("window.scrollTo(0, " + str(profile_scroll) + ");")
        time.sleep(0.2)
        if prevTop == driver.execute_script("return window.pageYOffset;"):
            driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
            break
        prevTop = driver.execute_script("return window.pageYOffset;")
        profile_scroll += 500


def scrape_profile(count, keyword, limitResults):
    obj = {}
    obj["timestamp"] = timestamp
    obj["resultsNumber"] = [{"timestamp": timestamp, "resultsCount": count}]
    obj["keyword"] = keyword
    obj["limitResults"] = limitResults

    try:
        obj["name"] = driver.find_element_by_class_name(
            "pv-top-card-section__name").text
        if "name" in errors.keys():
            errors["name"] = 0
    except:
        obj["name"] = "NA"
        if "name" in errors.keys():
            errors["name"] += 1
        else:
            errors["name"] = 0

    try:
        obj["headline"] = driver.find_element_by_class_name("pv-top-card-section__headline").text
        if "headline" in errors.keys():
            errors["headline"] = 0
    except:
        obj["headline"] = "NA"
        if "headline" in errors.keys():
            errors["headline"] += 1
        else:
            errors["headline"] = 0

    try:
        obj["location"] = driver.find_element_by_class_name("pv-top-card-section__location").text
        if "location" in errors.keys():
            errors["location"] = 0
    except:
        obj["location"] = "NA"
        if "location" in errors.keys():
            errors["location"] += 1
        else:
            errors["location"] = 0

    scroll_all()

    obj["experience"] = scrape_experiences()
    obj["education"] = scrape_education()
    obj["skills"] = scrape_skills()
    rec_sec = ""
    try:
        rec_sec = driver.find_element_by_class_name("pv-recommendations-section")
    except:
        return "NA"
    artdecos_switch = rec_sec.find_elements_by_tag_name("artdeco-tab")
    artdecos = rec_sec.find_elements_by_tag_name("artdeco-tabpanel")
    for x in artdecos_switch:
        if "Received" in x.text:
            obj["recommendationsReceived"] = scrape_recommendations(artdecos[0])
            if len(artdecos_switch) == 2:
                driver.execute_script("arguments[0].click();", artdecos_switch[1])
        if "Given" in x.text:
            obj["recommendationsGiven"] = scrape_recommendations(artdecos[1])

    obj["accomplishments"] = scrape_accomplishments()

    driver.get(driver.current_url + "detail/interests")
    obj["interests"] = scrape_interests()

    return obj

def scrape_jobs(count, keyword, limitResults, location):
    obj = {}
    obj["timestamp"] = timestamp
    obj["resultsNumber"] = [{"timestamp": timestamp, "resultsCount": count}]
    obj["keyword"] = keyword
    obj["limitResults"] = limitResults
    obj["searchLocation"] = location
    container = driver.find_element_by_class_name("jobs-details-top-card__container")
    container = container.find_element_by_class_name("jobs-details-top-card__content-container")
    try:    
        obj["jobTitle"] = container.find_element_by_class_name("jobs-details-top-card__job-title").text
    except:
        return -1
    try:
        info = container.find_element_by_class_name("jobs-details-top-card__company-info")
        obj["company"] = info.find_element_by_tag_name("a").text
        obj["linkToCompany"] = info.find_element_by_tag_name("a").get_attribute("href")
    except:
        return -1
    try:
        obj["jobLocation"] = container.find_element_by_class_name("jobs-details-top-card__bullet").text
    except:
        return -1
    try:
        obj["jobPosted"] = container.find_element_by_class_name("jobs-details-top-card__job-info").text.split("\n")[1]
    except:
        return -1
    try:
        obj["views"] = int(container.find_element_by_class_name("jobs-details-top-card__job-info").text.split("\n")[3][:-5])
    except:
        obj["views"] = 0
    description = driver.find_element_by_class_name("jobs-description")
    see_more = description.find_element_by_tag_name("button")
    driver.execute_script("arguments[0].click();", see_more)
    description = driver.find_element_by_class_name("jobs-description__content")
    obj["jobDescription"] = description.find_element_by_tag_name("span").text
    obj["jobDetails"] = {}
    for li in driver.find_elements_by_class_name("jobs-box__group"):
        try:
            obj["jobDetails"][li.text.split("\n")[0]] = li.text.split("\n")[1]
        except:
            continue
    return obj

def scrapeLinkedInAccounts(mode, keywords, searchType, location=None, limitResults=0):
    finalResults = []
    for keyword in keywords:
        page = 1
        search_results = []
        count = 0
        if searchType == "People":
            while True:
                try:
                    driver.get(search_profile_url(searchType, keyword, page))
                    allLi = wait.until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "li")))

                    for li in allLi:
                        try:
                            if "search-result" in li.get_attribute("class"):
                                search_results.append(li.find_element_by_class_name("search-result__result-link").get_attribute("href"))
                        except:
                            pass
                    count += len(search_results)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    lis = driver.find_element_by_class_name("page-list")
                    num = int(lis.find_elements_by_tag_name("li")[-1].text)
                    if page < num:
                        page += 1
                    else:
                        break
                except:
                    break
            for link in search_results:
                driver.get(link)
                finalResults.append(scrape_profile(count, keyword, limitResults))
                if limitResults != 0 and len(finalResults) > limitResults:
                    break
        if searchType == "Jobs":
            driver.get(search_job_url(searchType, keyword, "Italy", 0))
            div = driver.find_element_by_class_name("jobs-search-dropdown--view-switcher")
            button = div.find_element_by_tag_name("button")
            driver.execute_script("arguments[0].click();", button)
            div = driver.find_element_by_class_name("jobs-search-dropdown--view-switcher")
            option = div.find_element_by_class_name("jobs-search-dropdown__option-button")
            driver.execute_script("arguments[0].click();", option)
            start = 0
            while True:
                scroll_all()
                try:
                    job_results_ul = driver.find_element_by_class_name("jobs-search-results__list")
                    for li in job_results_ul.find_elements_by_class_name("artdeco-list__item"):
                        try:
                            search_results.append(li.find_element_by_css_selector("a.job-card-search__link-wrapper").get_attribute("href"))
                        except:
                            continue
                    start += 25
                    driver.get(search_job_url(searchType, keyword, "Italy", start))
                except:
                    break
            count = len(search_results)
            for link in search_results:
                driver.get(link)
                finalResults.append(scrape_jobs(count, keyword, limitResults, "Italy"))
                if limitResults != 0 and len(finalResults) > limitResults:
                    break
    if mode == 2:
        for x in finalResults:
            try:
                scraperDb.persons.insert_one(x)
            except:
                continue
    return finalResults

lists = []
login()
for filename in os.listdir(os.getcwd() + '/files'):
    with open(os.getcwd() + '/files/' + filename, 'r') as f:
        lines = f.readlines()
        for i in range(2, len(lines), 2):
            scrapeLinkedInAccounts(2, [lines[i].split(";")[0] + lines[i].split(";")[1][:-4]], "People")

# json_data = json.dumps(lists)
# with open('test.json', 'w') as f:
#     f.write(json_data)
