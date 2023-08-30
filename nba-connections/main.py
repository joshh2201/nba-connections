from bs4 import BeautifulSoup
import logging
import requests
import time
import re

BASE_URL = "https://www.basketball-reference.com"
session = requests.Session()


def get_page_html(url: str) -> str:
    """
    Retrieves the html of a webpage. Handles HTTPErrors and implements a delay.

    Args:
        url (str): URL to make a get request

    Returns:
        response.text (str): the html of the url as a string

    Notes:
        Introduces a 3.1 time delay to mitigate rate limit constraints during API calls. This delay is implemented
        to ensure compliance with the rate limit, which permits a maximum of 20 calls per minute.

    """
    try:
        response = session.get(url)
        response.raise_for_status()
        logging.info("Sleeping for 3.1 seconds to avoid rate limit")
        time.sleep(3.1)
    except requests.HTTPError as e:
        logging.warning(f"Could not get a response from {url}: {e}")

    return response.text


def get_team_urls() -> dict:
    """
    Retrieve links to the most recent team rosters by parsing the home page of Basketball Reference as a dictionary.
    Each team's shorthand (e.g., 'LAL' for Los Angeles Lakers) is used as a key, and the associated roster link
    is stored as the value. It handles potential HTTP errors and ensures an API delay between
    requests to avoid overloading the server.

    Returns:
        dict: A dictionary containing team shorthand as keys and corresponding roster links as values.

    """
    team_urls = {}
    html_response = get_page_html(BASE_URL)
    soup = BeautifulSoup(html_response, "lxml")
    team_table = soup.find("div", {"id": "teams"})

    for conference_table in team_table.div.find_all("table"):
        for team_header in conference_table.tbody.find_all("th"):
            team_link = team_header.a
            team_urls[team_link.text] = BASE_URL + team_link["href"]

    return team_urls


def player_info_helper(table_row) -> dict:
    """
    Parse a roster table row to extract player information such as player name, position,
    height, weight, and birthdate.

    Args:
        table_row (bs4.element.Tag): The BeautifulSoup Tag representing a row in the roster table.

    Returns:
        dict: A dictionary containing extracted player information.

    """
    return dict(
        name=table_row.find("td", {"data-stat": "player"}).a.text,
        position=table_row.find("td", {"data-stat": "pos"}).text,
        height=table_row.find("td", {"data-stat": "height"}).text,
        weight=table_row.find("td", {"data-stat": "weight"}).text,
        birthdate=table_row.find("td", {"data-stat": "birth_date"}).text,
    )


def get_players(roster_table) -> list:
    """
    Iterate through the rows of a roster table to retrieve player data. The player data for each roster is
    returned as a list where each element is a dictionary representing a player.

    Args:
        roster_table (bs4.element.Tag): The BeautifulSoup Tag representing the roster table.

    Returns:
        list: A list of dictionaries containing extracted player information.

    """
    players = []
    for table_row in roster_table.find_all("tr"):
        players.append(player_info_helper(table_row))
    return players


def get_current_rosters() -> dict:
    """
    Retrieve most recent rosters for all NBA teams. For each team URL, the function sends an HTTP GET request
    and then extracts player roster data from the corresponding table. The collected rosters are organized
    into a dictionary with team shorthand as keys and a list of player information as values.

    Returns:
        rosters (dict): A dictionary mapping team shorthand to player rosters.

    """
    rosters = {}
    team_urls = get_team_urls()
    for team in team_urls:
        html_response = get_page_html(team_urls[team])
        soup = BeautifulSoup(response.text, "lxml")
        roster_table = soup.find("table", {"id": "roster"}).tbody
        rosters[team] = get_players(roster_table)

    return rosters


def get_historic_rosters() -> dict:
    """
    Retrieve historic rosters for all NBA teams. For each team URL, the function sends an HTTP GET request
    using a session and then extracts player roster data from the corresponding table. The collected rosters
    are organized into a dictionary with team shorthand as keys mapping to a dictionary with season/year as
    a key and a list of players as a value

    Returns:
        rosters (dict(dict: list)): A dictionary mapping team shorthand to a dictionary
                                    mapping season to a list of players.

    """
    rosters = {}
    team_urls = get_team_urls()
    for team in team_urls:
        current_url = team_urls[team]
        historic_rosters = {}
        while True:
            response = session.get(current_url)
            api_delay()
            # parse the year out of the url
            year = int(re.search(r"\d{4}", current_url).group(0))

            soup = BeautifulSoup(response.text, "lxml")
            roster_table = soup.find("table", {"id": "roster"}).tbody
            historic_rosters[year] = get_players(roster_table)

            # check for previous season and update current_url
            prev_season_endpoint = f"/teams/{team}/{year - 1}.html"
            if soup.find("a", {"href": prev_season_endpoint}):
                current_url = BASE_URL + prev_season_endpoint
            else:
                break

        rosters[team] = historic_rosters

    return rosters


print(get_team_urls())
