from bs4 import BeautifulSoup
from logging import Logger
import requests
import time

BASE_URL = "https://www.basketball-reference.com"
session = requests.Session()


def api_delay() -> None:
    """
    Introduces a time delay to mitigate rate limit constraints during API calls.

    Returns:
        None

    To prevent exceeding the API rate limit, this function enforces a delay of 3.1 seconds between consecutive calls.
    This delay is implemented to ensure compliance with the rate limit, which permits a maximum of 20 calls per minute.

    Notes:
        The delay duration of 3.1 seconds has been determined to maintain adherence to the specified rate limit.
        Developers should review and adjust this delay as necessary based on the API's rate limit policy.
    """
    Logger.info("Sleeping for 3.1 seconds to avoid rate limit")
    time.sleep(3.1)


def get_team_urls() -> dict:
    """
    Retrieve links to the most recent team rosters by parsing the home page of Basketball Reference.

    Returns:
        dict: A dictionary containing team shorthand as keys and corresponding roster links as values.

    The function fetches team URLs from the home page of Basketball Reference and organizes them into a dictionary.
    Each team's shorthand (e.g., 'LAL' for Los Angeles Lakers) is used as a key, and the associated roster link
    is stored as the value. The function gracefully handles potential HTTP errors and ensures an API delay between
    requests to avoid overloading the server.
    """
    team_urls = {}
    try:
        response = session.get(BASE_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        team_table = soup.find("div", {"id": "teams"})
        for conference_table in team_table.div.find_all("table"):
            for team_header in conference_table.tbody.find_all("th"):
                team_link = team_header.a
                team_urls[team_link.text] = BASE_URL + team_link["href"]

        api_delay()

    except requests.HTTPError as e:
        Logger.warning(f"Could not get a response from {BASE_URL}: {e}")

    return team_urls


def player_info_helper(table_row) -> dict:
    """
    Parse a roster table row to extract player information.

    Args:
        table_row (bs4.element.Tag): The BeautifulSoup Tag representing a row in the roster table.

    Returns:
        dict: A dictionary containing extracted player information.

    The function accepts a BeautifulSoup Tag representing a table row from a roster table. It then extracts specific
    data points from the row, such as player name, position, height, weight, and birthdate, returning the data as 
    a dictionary.

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
    Iterate through the rows of a roster table to retrieve player data.

    Args:
        roster_table (bs4.element.Tag): The BeautifulSoup Tag representing the roster table.

    Returns:
        list: A list of dictionaries containing extracted player information.

    The function accepts a BeautifulSoup Tag representing a roster table. It then iterates over the rows in the
    table and calls the `player_info_helper()` function on each row to retrieve player data. The player data for each roster is
    returned as a list where each element is a dictionary representing a player.

    """
    players = []
    for table_row in roster_table.find_all("tr"):
        players.append(player_info_helper(table_row))
    return players


def get_rosters() -> dict:
    """
     Retrieve rosters for all NBA teams.

    Returns:
        dict: A dictionary mapping team shorthand to player rosters.

    This function fetches and compiles team rosters by iterating through a collection of team URLs. It uses the
    `get_team_urls()` function to obtain the required URLs. For each team URL, the function sends an HTTP GET request
    using a session and then extracts player roster data from the corresponding table. The collected rosters are
    organized into a dictionary with team shorthand as keys and player information as values.

    Notes:
        The function makes use of the `get_team_urls()` and `get_players()` functions to retrieve the necessary data.
        Additionally, it employs the `api_delay()` function to prevent potential rate limit issues during API calls.

    """
    rosters = {}
    team_urls = get_team_urls()
    for team in team_urls:
        print(team, team_urls[team])
        response = session.get(team_urls[team])
        soup = BeautifulSoup(response.text, "lxml")
        roster_table = soup.find("table", {"id": "roster"}).tbody
        rosters[team] = get_players(roster_table)
        api_delay()
    return rosters


print(get_rosters())
