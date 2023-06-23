import csv
from dataclasses import dataclass, asdict
import httpx
import numpy as np
import pandas as pd
from selectolax.parser import HTMLParser

@dataclass
class CapFriendlyTrade:
    post_id: str
    post_name: str
    post_date: str
    team: str
    trade_id: str
    players_traded: list
    players_received: list
    team_traded: str
    team_trade_with: str

def get_html(link: str):
    resp = httpx.get(link)
    html = HTMLParser(resp.text)
    return html

def append_to_csv(file_path, data):
    with open(file_path, 'a', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)

def get_posts_links(page_number: str, excluded_links: set):
    html = get_html("https://www.capfriendly.com/forums/armchair-gm/"+ page_number)
    rows = html.css("tr")
    post_links = []
    for post in rows:
        text = post.css_first("a")
        if text is not None:
            link = text.attributes['href']
            if link not in excluded_links:
                post_links.append(link)
    return post_links

def scrape_post(post_link: str):
    html = get_html("https://www.capfriendly.com" + post_link)
    post_id = post_link.replace("/forums/thread/", "").replace("/armchair-gm/team/", "")
    post_name = html.css_first(".mt10.cb.l").text()
    post_date = html.css_first("body > div:nth-child(11) > div:nth-child(1) > div:nth-child(1) > div:nth-child(9)").text().replace("Published: ", "")
    team = html.css_first("body > div:nth-child(11) > div:nth-child(1) > div:nth-child(1) > div:nth-child(7)").text().replace("Team: ", "")
    trades = html.css("div[class='agm_trade mb10 rel']")
    for i, trade in enumerate(trades, start=1):
        trade_data = get_trade(trade, post_id, post_name, post_date, team, i)
        append_to_csv("trades.csv", trade_data.__dict__.values())

def get_trade(trade, post_id, post_name, post_date, team, i):
    trade_data = CapFriendlyTrade(
        post_id=post_id,
        post_name=post_name,
        post_date=post_date,
        team=team,
        trade_id=i,
        players_traded=[player.text() for player in trade.css("div[class='l']")[0].css("li")],
        players_received=[player.text() for player in trade.css("div[class='l']")[1].css("li")],
        team_traded=trade.css("div[class='l']")[0].css_first("div[class='r']").text(),
        team_trade_with=trade.css("div[class='l']")[1].css_first("div[class='r']").text()
    )
    return trade_data

def main():
    excluded_links = {
        "/forums/thread/560376",
        "/forums/thread/692782",
        "/forums/thread/649275",
        "/forums/thread/687037",
        "/forums/thread/622214",
        "/forums/thread/209232"
    }

    try:
        df = pd.read_csv("trades.csv", encoding='latin-1')
    except FileNotFoundError:
        df = pd.DataFrame()

    for page in range(1, 900, 1):
        post_links = get_posts_links(str(page), excluded_links)
        for link in post_links:
            post_id = np.int64(link.replace("/forums/thread/", "").replace("/armchair-gm/team/", ""))
            if post_id not in df["post_id"].unique():
                scrape_post(link)
                df = pd.read_csv("trades.csv", encoding='latin-1')  # Refresh DataFrame
        print(page)

    df.to_csv("trades.csv", index=False, encoding='latin-1')


if __name__ == "__main__":
    main()
