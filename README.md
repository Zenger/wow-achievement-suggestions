This is a sample API companion that should go along with https://github.com/Zenger/wow-achievement-tracker. 

Before launching make sure to install the packages form requirements.txt and create a config.json file or copy and modify the config.template.json.

Sample:

```
{
  "authorized": [
    // array of user ids
  ],
  "wow": {
    "client_id": "", // your wow developer credentials
    "client_secret": "",
    "region": "us",
    "locale": "en_US"
  },

  "openapi": {
    "key": "" // your openai key
  }
}
```
My particular API also adds a few extra helper endpoints:

| Method | Endpoint  | Purpose |
| --- | ------------- | ------------- |
| GET | /a/<string:realm>/<string:character> | Extracts achievment data for the whole character |
| GET | /extract/achievement/<int:achievement_id> | Extract a single achievement data from wow api |
| GET | /track/achievement/<string:realm>/<string:name>/<int:achievement_id> | Returns selected character achievement status (completness, steps left and so forth) |
| GET | /get-suggestions/<string:id> | Scrapes wowhead comments for advice and information, then sends it all to OpenAI to generate suggestions |




> [!IMPORTANT]
> All requests are stored in a local sqlite database and all suggestions are saved in a json file.
> 
> This means some of the suggestions and results might seem stale, this is done to prevent spamming the scraper and return existing suggestions.
