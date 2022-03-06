#!/usr/bin/env python3


# suggested cron command (at 1:00 AM of every day)
# 0 1 * * * python fetch_menu.py >> fetch_menu.log 2>> fetch_menu.log


# imports

from datetime import date as Date, datetime as Datetime, timedelta as Timedelta
from bs4 import BeautifulSoup 
from bs4.element import Tag
from os.path import exists

import time
import requests
import json
import traceback


# settings

WEEKS = 2
MENU_NAME_FORMAT = '%Y-%W'


# error class

class ParseError(Exception):
    pass


# network

def make_time(date: Date) -> int:
    datetime = Datetime.combine(date, Datetime.min.time())
    timestamp = time.mktime(datetime.timetuple())
    return int(timestamp)

def download_page(date: Date, reduced: bool) -> str:
    r = requests.get('https://opera4u.operaunitn.cloud/menu/{}/0/{}/2'
                        .format(make_time(date), 1 if not reduced else 2))

    # check status code
    if r.status_code != 200:
        raise ParseError('Unable to download menu')

    return r.text


# parse menu

def parse_service_course(course: Tag, title: str) -> list:
    # get course title
    try:
        html_title: str = course.find('th').text
    except Exception as e:
        raise ParseError('Error in parsing service course title')

    # check title
    if html_title != title:
        raise ParseError('Wrong course title ({} != {})'.format(html_title, title))

    # get course food
    try:
        columns = course.find_all('td')
    except Exception as e:
        raise ParseError('Error in parsing service course items') from e
    
    # check columns length
    if len(columns) != 7: # 7 days in a week
        raise ParseError('Number of days in a week is not 7')

    # parse course items
    result = []
    for i in range(5):
        items_day = []
        column: Tag = columns[i]
        items = column.find_all('p')

        # parse items
        for item in items:
            
            try:
                food: str = item.find('a').text
                food = food.strip().capitalize()
                items_day.append(food)
            except Exception as e:
                raise ParseError('Error in extracting item name') from e
        
        result.append(items_day)

    return result

def parse_service(table: Tag, type: str) -> list:
    # get courses
    try:
        rows = table.find_all('tr')
    except Exception as e:
        raise ParseError('Error in parsing service details')

    # check rows amount
    if len(rows) < 3 or len(rows) > 4: # title, first, second, side
        raise ParseError('Wrong number of rows')

    # get service type
    try:
        service_type: str = rows[0].find('th').find('h5').text
    except Exception as e:
        raise ParseError('Error in finding service type') from e

    # check service type
    if service_type != type:
        raise ParseError('Service type miss-match ({} != {})'.format(service_type, type))

    # courses
    result = []
    first = parse_service_course(rows[1], 'Primi Piatti')
    second = parse_service_course(rows[2], 'Secondi Piatti')
    if len(rows) == 4:
        side = parse_service_course(rows[3], 'Contorni')
    else:
        side = [[], [], [], [], []]

    for i in range(5):
        result.append({
            'first': first[i],
            'second': second[i],
            'side': side[i]
        })

    return result

def parse_menu(page: str, has_dinner: bool = True) -> dict:
    # parse page
    try:
        parser = BeautifulSoup(page, 'html.parser')
    except Exception as e:
        raise ParseError('Error in parsing HTML page') from e

    # find tables
    tables = parser.find_all('table')

    if len(tables) != (2 if has_dinner else 1):
        print(len(tables))
        raise ParseError('Wrong number of tables')

    # services
    result = {}
    result['lunch'] = parse_service(tables[0], 'Pranzo')
    if has_dinner:
        result['dinner'] = parse_service(tables[1], 'Cena')
    return result

def menu_lunch(date: Date) -> list:
    try:
        # get standard menu
        standard = parse_menu(download_page(date, False), True)

        # get reduced menu
        reduced = parse_menu(download_page(date, True), False)

        result = []
        for i in range(5): # working day in a week
            day = {}
            # first & second
            for course in ['first', 'second']:
                items = []
                for item in standard['lunch'][i][course]:
                    in_reduced = item == reduced['lunch'][i][course][0]
                    items.append({'name': item, 'in_reduced': in_reduced})
                day[course] = items
            
            # side
            items = []
            for item in standard['lunch'][i]['side']:
                items.append({'name': item, 'in_reduced': True})
            day['side'] = items
            result.append(day)

        return result
    except ParseError as e:
        raise e
    except Exception as e:
        raise ParseError('Unrecognized error') from e


# general

def main():
    # get current monday
    current = Date.today()

    # weeks
    for i in range(WEEKS):
        week = current + Timedelta(weeks=i)
        print('Downloading for week {} of year {}... '.format(week.year, week.strftime('%W')), end='')
        
        try:
            filename = '../data/menu/{}.json'.format(week.strftime(MENU_NAME_FORMAT))

            # check if already exist
            if not exists(filename):
                # get menu
                menu = menu_lunch(week)

                # write to file 
                with open(filename, 'w') as f:
                    json.dump(menu, f)

                print('success')
            else:
                print('already')


        except ParseError:
            print('failed')
            traceback.print_exc()


if __name__ == '__main__':
    main()
