from bs4 import BeautifulSoup
from logging import Logger
import requests

BASE_URL = "https://www.basketball-reference.com"


def get_team_url():
    """
    Parse the home page of basketball reference to get links to
    most recent team rosters.

    Returns a dictionary with team shorthand as the key and the link as the value
    """
    team_urls = {}
    try:
        response = requests.get(BASE_URL)
    except HTTPError as e:
        Logger.warning(f"Could not get a response from {BASE_URL}: {e}")
    soup = BeautifulSoup(response.text, "lxml")
    team_table = soup.find("div", {"id": "teams"})
    for conference_table in team_table.div.find_all("table"):
        for team_header in conference_table.tbody.find_all("th"):
            team_link = team_header.a
            team_urls[team_link.text] = BASE_URL + team_link["href"]
    return team_urls


get_team_links()
