# SPDX-License-Identifier: MIT
import json
import os

from bs4 import BeautifulSoup
import requests

from flask import Flask, Response, request, abort
from scraper import Scraper
from datahandler import DataHandler
from normalizer import Normalizer
from openai import OpenAI
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)

scraper = Scraper()
db = DataHandler()
normalizer = Normalizer()

with open('config.json', 'r') as f:
    config = json.load(f)


def is_authorized():
    return True if request.headers.get('X-Auth-Key') in config.get('authorized') else False
@app.route('/')
def hello_world():  # put application's code here
    if not is_authorized():
        abort(401)
    return 'Hello World!'


@app.route('/a/<string:realm>/<string:character>')
def get_character_achievements(realm: str, character: str):
    if not is_authorized():
        abort(401)
    achievements = scraper.get_character_achievements(realm, character)
    normalized = normalizer.character_achievements(achievements)
    db.store_character_achievement(realm, character, json.dumps(achievements))
    return normalized.to_dict()


@app.route('/extract/achievement/<int:achievement_id>')
def extract_achievement_data(achievement_id: int):
    if not is_authorized():
        abort(401)
    return recursive_extract_achievement_data(achievement_id)


def recursive_extract_achievement_data(achievement_id: int):
    # Fetch raw data using the global scraper
    raw_data = scraper.get_achievement_data(achievement_id)

    # Normalize data using the global normalizer
    normalized = normalizer.from_achievement(raw_data)

    if normalized.get_data() is None:
        return None  # Return None or handle it as needed

    # Prepare the node for this achievement
    node = {
        "id": normalized.get_data().id,
        "name": normalized.get_data().name,
        "description": normalized.get_data().description,
        "is_account_wide": normalized.get_data().is_account_wide,
        "criteria": {
            "id": normalized.get_data().criteria.id,
            "description": normalized.get_data().criteria.description,
            "amount": normalized.get_data().criteria.amount,
            "children": []
        }
    }

    # Process each child criteria if it exists
    if normalized.has_child_criteria():
        for child_criterium in normalized.get_data().criteria.child_criteria:
            # Check if there is an associated achievement with the child criteria
            if child_criterium.achievement:
                # Recursively extract data for each child achievement
                child_data = recursive_extract_achievement_data(child_criterium.achievement.id)
                node["criteria"]["children"].append({
                    "id": child_criterium.id,
                    "description": child_criterium.description,
                    "amount": child_criterium.amount,
                    "achievement": child_data
                })

    return node


@app.route('/track/achievement/<string:realm>/<string:name>/<int:achievement_id>')
def track_achievement(realm: str, name: str, achievement_id: int):
    if not is_authorized():
        abort(401)
    character_data = db.get_character_achievements(realm, name)

    # build achievement tree
    tree = []
    data = recursive_extract_achievement_data(achievement_id)
    tree.append(data)
    return tree
def check_if_response_exists(id):
    return os.path.exists(f"responses/{id}.json")


@app.route('/get-suggestions/<string:id>')
@cross_origin(origin='*')
def get_suggestions(id: str):
    if not is_authorized():
        abort(401)
    # get  achievement data, and comments from wowhead
    # get comments from wowhead
    if check_if_response_exists(id):
        print('YESSS')
        with open(f"responses/{id}.json", 'r') as f:
            return Response(f.read(), content_type='application/json; charset=utf-8')

    data = requests.get('https://www.wowhead.com/achievement=' + id)
    bs = BeautifulSoup(data.text, 'html.parser')
    script_tags = bs.find_all('script')
    body = ("Help me write a summary for this achievement, return a markdown of summarized data and priorities for the "
            "achievement. Keep it as short as possible skip all urls.")

    title_tag = bs.find_all('h1')[0]
    description = bs.find('meta', property='og:description')['content']
    requirements_tables = bs.find_all('table')
    criteria = ""
    a = []
    b = []
    try:
        a = requirements_tables[-1]
        b = requirements_tables[-2]
    except:
        pass

    for td in a.find_all('td'):
        criteria += td.text + "\n"
    for td in b.find_all('td'):
        criteria += td.text + "\n"

    body += (f"The achievement is called {title_tag.text} and it is described as {description}. The requirements for "
             f"this achievement are as follows: {criteria}\n\n")
    body += "Latest comments are: \n\n"

    for tag in script_tags:
        if 'var _ = g_users;' in tag.text:
            start_index = tag.text.find('var lv_comments0 = ')
            if start_index == -1:
                return "Keyword not found"
            text = tag.text[start_index:].replace("var lv_comments0 = ", "")

            js = json.loads(text[:-2])
            body = ""
            for comment in js:
                if int(comment['rating']) >= 0:
                    body += comment['body'] + "\n"
                    if 'replies' in comment:
                        for reply in comment['replies']:
                            if int(reply['rating']) >= 0:
                                body += reply['body'] + "\n"



    client = OpenAI()
    client.api_key = config.get('openapi').get('key')

    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system",
             "content": "You are web server assistant, you will return markdown content for various wow achievemnets and quests."},
            {"role": "user", "content": body[:6000]}
        ]
    )

    with open(f"responses/{id}.json", 'w') as f:
        f.write(completion.choices[0].message.json())

    return Response(completion.choices[0].message.json(), content_type='application/json; charset=utf-8')


if __name__ == '__main__':
    app.run(debug=True)
