import argparse
from asyncio import base_events
from re import L
import requests
from bs4 import BeautifulSoup

base_url = 'https://askfred.net/Results/past.php?f%5Bevent_weapon_eq%5D={}&f%5Bevent_gender_eq%5D=men&f%5Bevent_age_eq%5D=senior-open&f%5Bradius_mi%5D=300&vals%5Bloc%5D=&f%5Bname_contains%5D=&ops%5Bdate%5D=start_date_eq&vals%5Bdate%5D=&f%5Bevent_is_team%5D=&f%5Bevent_entries_gte%5D=&ops%5Bevent_rating%5D=event_rating_eq&vals%5Bevent_rating%5D=&f%5Bdivision_id%5D=&page_id={}'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weapon', 
                        dest='weapon',
                        required=True,
                        choices=['Epee', 'Foil', 'Saber'],
                        help='weapon of tournaments to search through')
    args = parser.parse_args()

    tournament_result_links = []
    # for i in range(10):
    while True:
        response = requests.get(base_url.format(args.weapon, i))
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if (soup.find('h3') is None )and (soup.find('h3').text != 'No tournaments were found.'):
            # still tournaments being shown
            tournament_result_links += [a['href'] for a in soup.find('table', {'id': 'past-tours'}).findAll('a') if 'results' in a['href']]
        else:
            # end of all tournaments in history for search, end
            break

    with open('touranment_result_links.txt', 'w') as f:
        f.write('\n'.join(tournament_result_links))

    names = []
    for link in tournament_result_links:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')

        page_names = [r.text.strip().split('\n\n')[0].split('\xa0')[-1] for t in soup.findAll('table', {'class': 'box'}) for r in t.findAll('tr')]
        page_names = [n for n in names if (n != '') and ('Competitors' not in n) and ('Rating Earned' not in n)]
        names += page_names

    with open('names.txt', 'w') as f:
        f.write('\n'.join(names))
