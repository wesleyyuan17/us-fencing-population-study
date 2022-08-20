import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from tqdm import tqdm

base_url = 'https://askfred.net/Results/past.php?f%5Bevent_weapon_eq%5D=&f%5Bevent_gender_eq%5D=men&f%5Bevent_age_eq%5D=senior-open&f%5Bradius_mi%5D=300&vals%5Bloc%5D=&f%5Bname_contains%5D=&ops%5Bdate%5D=start_date_eq&vals%5Bdate%5D=&f%5Bevent_is_team%5D=&f%5Bevent_entries_gte%5D=&ops%5Bevent_rating%5D=event_rating_eq&vals%5Bevent_rating%5D=&f%5Bdivision_id%5D=&page_id={}'


def get_event_type(row_text):
    '''
    Takes text from html table and extracts type of tournament (age group, gender, weapon), number of competitors and event classification
    
    Args:
        row_text: str, string from html table
    '''
    if len(row_text.split('\xa0')) < 4:
        return None, None, None
    category, _, _, n_rating = row_text.split('\xa0')
    if 'Team' in category:
        return 'Team Event', None, None
    category = category.replace(':', '')
    n, rating = n_rating.split(', ')
    n = int(n.replace('Competitors', ''))
    rating = rating.replace('a ', '').replace(' Event', '')

    return category, n, rating


def get_event_info(tournament_page):
    '''
    Takes html-parsed tournament results page as BeautifulSoup object and returns date/location of tournament

    Args:
        tournament_page: BeautifulSoup object, parsed BeautifulSoup object of tournament results page
    '''
    info = tournament_page.find('div', {'id': 'results-head'})
    if info is None:
        return None, None

    date, location = info.text.split('\n')[1:3]
    return date, location


if __name__ == '__main__':
    if os.path.exists('tournament_result_links.txt'):
        print('Reading tournament links from file...')
        with open('tournament_result_links.txt', 'r') as f:
            tournament_result_links = f.read().split('\n')
    else:
        print('Getting tournament links from askfred...')
        tournament_result_links = []
        i = 1 # page count
        while True:
            response = requests.get(base_url.format(i))
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if soup.find('h3') is None:
                # still tournaments being shown
                tournament_result_links += [a['href'] for a in soup.find('table', {'id': 'past-tours'}).findAll('a') if 'results' in a['href']]
            else:
                # end of all tournaments in history for search, end
                break

            i += 1 # increment page count

        print('Writing tournament links to file...')
        with open('tournament_result_links.txt', 'w') as f:
            f.write('\n'.join(tournament_result_links))

    print('Getting results from tournaments...')
    dfs = []
    for link in tqdm(tournament_result_links):
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')

        rows = [r.text.strip() for t in soup.findAll('table', {'class': 'box'}) for r in t.findAll('tr')]
        if len(rows) < 1:
            continue

        date, location = get_event_info(soup)
        category, n, rating = get_event_type(rows[0])
        if category == 'Team Event':
            continue

        data = []
        for r in rows:
            if ':' in r:
                # get event info but don't add it as a row
                category, n, rating = get_event_type(r)
                continue
            
            if 'Rating Earned' in r:
                # skip column header
                continue

            if 'Results not posted yet.' in r:
                # skip tables where organizers didn't put in information
                continue
            
            row_data = [t.strip() for t in r.split('\n') if t != '']
            if len(row_data) < 6:
                row_data += ['']
            data.append([date, location, category, n, rating] + row_data)

        dfs.append(pd.DataFrame(data, columns=['Date', 'Location', 'Event', 'NumCompetitors', 'EventRating', 'Place', 'Name', 'ClubAbbr', 'Club', 'Rating', 'RatingEarned']))

    out = pd.concat(dfs, ignore_index=True)

    print('Writing results to file...')
    out.to_csv('data.csv', index=False)
