import scrapy
import json
import os
from urllib.parse import quote
from pathlib import Path


class MatchSpider(scrapy.Spider):
    name = 'match_spider'
    # Remember to change the region if needed
    start_urls = [f'https://www.op.gg/_next/data/xbsaN8YvrzlIsIV7N8lUS/leaderboards/tier.json?region=euw&page={i}' for i in range(1, 200)]

    def __init__(self, end_date:str = '2022-11-15', match_date_path:str = None):
        self.match_date_path = match_date_path
        self.matches_searched = {}
        self.match_dates_for_dumping = {}
        self.region = 'euw'
        
        # If crawling from specific match_dates
        if match_date_path != None:
            self.use_recorded_match_dates = True

            # Load json and format dates (unicode percent)
            with open(match_date_path) as match_dates_json:
                self.match_dates_from_file = json.load(match_dates_json)
            self.match_dates_from_file = {k: quote(v) for k, v in self.match_dates_from_file.items()}

        else:
            # Use end date given as argument
            self.use_recorded_match_dates = False
            self.end_date = quote(end_date) + quote("T00:00:00+00:00")
            self.page = 0
                        

    def parse(self, response):
        if self.use_recorded_match_dates == True:
            yield from self._parse_from_file()
        else:
            yield from self._parse_from_end_date(response)
            
    
    # Evaluates by default after spider terminates
    def closed(self, reason):
        # Remove old match_dates_buffer file
        if self.use_recorded_match_dates == True:
            os.remove(self.match_date_path)
        # Dump current match_date buffer file (using page number)
        with open(f'match_dates_buffer.json', 'a') as fp:
            json.dump(self.match_dates_for_dumping, fp)
    

    def _parse_from_file(self):
        for summoner_id, date in self.match_dates_from_file.items():
            matches_url = f"https://op.gg/api/v1.0/internal/bypass/games/{self.region}/summoners/{summoner_id}?&ended_at={date}&limit=20&hl=en_US&game_type=soloranked"

            yield scrapy.Request(url=matches_url, callback=self._parse_matches, cb_kwargs={'summoner_id': summoner_id})
        

    def _parse_from_end_date(self, response):
        # Load info from hiscores
        player_json_response = json.loads(response.body)
        for player in player_json_response['pageProps']['data']: 
            # Get link to match history
            summoner_id = player['summoner']['summoner_id']
            matches_url = f"https://op.gg/api/v1.0/internal/bypass/games/{self.region}/summoners/{summoner_id}?&ended_at={self.end_date}&limit=20&hl=en_US&game_type=soloranked"

            yield scrapy.Request(url=matches_url, callback=self._parse_matches, cb_kwargs={'summoner_id': summoner_id})


    def _parse_matches(self, response, summoner_id):

        match_json_response = json.loads(response.body)
        
        # If there are more games to search, record last game date for json dump
        if len(match_json_response['data']) == 20:
            self.match_dates_for_dumping[summoner_id] = match_json_response['meta']['last_game_created_at']
        
        # Parse match history one at a time
        for i, match in enumerate(match_json_response['data']):
            # Check if match is duplicate
            if self.matches_searched.get(match['id'], False) == False:
                yield from self._parse_match(match)

    
    def _parse_match(self, match):
        # Match specific information
        match_info = {'match_id': match['id'],
                      'created_at': match['created_at'],
                      'is_remake': match['is_remake'],
                      'blue_win': match['teams'][0]['game_stat']['is_win'],
                      'patch': match['version']
                      }

        # Participant information
        for i, participant in enumerate(match['participants']):
            match_info[f'p{i+1}_puuid'] = participant['summoner']['puuid']
            match_info[f'p{i+1}_name'] = participant['summoner']['name']
            match_info[f'p{i+1}_champ'] = participant['champion_id']
            match_info[f'p{i+1}_team'] = participant['team_key']
            match_info[f'p{i+1}_position'] = participant['position']

        # Set match as searched
        self.matches_searched[match['id']] = True

        yield match_info