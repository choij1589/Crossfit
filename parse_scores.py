from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# updated 020324
# total 219 pages
# 50 athletes per page
# 10944 athletes in total
driver = webdriver.Chrome()

def get_scores(page):
    #driver.get(f"https://games.crossfit.com/leaderboard/open/2024?view=0&division=1&region=28&scaled=0&sort=0&page={page}")
    driver.get(f"https://games.crossfit.com/leaderboard/open/2024?view=0&division=1&region=28&scaled=0&sort=2&page={page}")
    wait = WebDriverWait(driver, 10)
    leaderboard_loaded = EC.presence_of_element_located((By.ID, 'leaderboardSponsorVisible'))
    wait.until(leaderboard_loaded)

    scores = []
    for i in range(1, 51):
        #css_selector = f"#leaderboardSponsorVisible > div > div.inner-container > table > tbody > tr:nth-child({i}) > td.score > div > div.rank-result > span > span.result"
        css_selector = f"#leaderboardSponsorVisible > div > div.inner-container > table > tbody > tr:nth-child({i}) > td.score.active-sort > div > div.rank-result > span > span.result"
        score_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        scores.append(score_element.text)

    return scores

scores = []
for page in range(1, 220):
    print(f"Processing page {page}")
    page_scores = get_scores(page)
    if page_scores[0] == "(--)":
        break
    scores += page_scores

# write in a csv format with date and current time
DATE = datetime.now().strftime("%Y-%m-%d")
TIME = datetime.now().strftime("%H-%M-%S")
with open(f"logs/scores.{DATE}.{TIME}.csv", "w") as file:
    for score in scores:
        file.write(f"{score}\n")

driver.quit()
