#!bin/bash

scrapy crawl match_spider -O ./match_data/matches_v2_0.csv
scrapy crawl match_spider -O ./match_data/matches_v2_1.csv -a "match_date_path"="match_dates_buffer.json"
scrapy crawl match_spider -O ./match_data/matches_v2_2.csv -a "match_date_path"="match_dates_buffer.json"
scrapy crawl match_spider -O ./match_data/matches_v2_3.csv -a "match_date_path"="match_dates_buffer.json"
scrapy crawl match_spider -O ./match_data/matches_v2_4.csv -a "match_date_path"="match_dates_buffer.json"