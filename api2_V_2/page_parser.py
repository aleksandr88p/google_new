


import asyncio

from bs4 import BeautifulSoup
import datetime
from urllib.parse import urlparse
import json


class DekstopScrape:
    def __init__(self): 
        pass

    ###################
    # organic results #
    ###################
    def searching_organic(self, soup):
        organic_list = []
        seen_urls = set()  # Create a set to store seen URLs
        
        # Новый селектор для органических результатов
        all_organic = soup.find_all('div', class_='MjjYud')
        # Исключаем рекламные блоки
        all_organic = [div for div in all_organic if not div.find('div', class_='uEierd')]
        
        c = 0
        for num, item in enumerate(all_organic):
            try:
                # Ищем ссылку в новой структуре
                link_element = item.find('a', class_='zReHs')
                if not link_element:
                    continue
                
                link = link_element.get('href')
                if not link or link in seen_urls:
                    continue  # Skip this result if the URL is already seen
                
                seen_urls.add(link)  # Add the URL to the seen set
                
                # Ищем заголовок
                head_element = item.find('h3', class_='LC20lb')
                if not head_element:
                    continue
                
                head = head_element.text.strip()
                
                # Ищем сниппет текста (описание)
                snippet_element = item.find('div', class_='VwiC3b')
                snippet = snippet_element.text.strip() if snippet_element else ' '
                
                if snippet:
                    c += 1
                
                try:
                    d_key = urlparse(link).netloc
                except:
                    d_key = ''
                    print('error in domain in organic')
                
                # Collect sitelinks if they exist
                sitelinks = []
                # Ищем сайтлинки в новой структуре
                sitelinks_container = item.find('div', class_=['HiHjCd', 'X7NTVe'])
                if sitelinks_container:
                    sitelinks_elements = sitelinks_container.find_all('a', href=True)
                    for slink in sitelinks_elements:
                        sitelink_url = slink['href']
                        sitelink_text = slink.text.strip()
                        sitelinks.append({'url': sitelink_url, 'text': sitelink_text})
                
                # Если сайтлинки не найдены, поищем в других контейнерах
                if not sitelinks:
                    sitelinks_container = item.find('table', class_='jmjoTe')
                    if sitelinks_container:
                        sitelinks_elements = sitelinks_container.find_all('a', href=True)
                        for slink in sitelinks_elements:
                            sitelink_url = slink['href']
                            sitelink_text = slink.text.strip()
                            sitelinks.append({'url': sitelink_url, 'text': sitelink_text})
                
                organic_list.append({
                    'position': f'{c}', 
                    'domain': d_key, 
                    'title': head, 
                    'snippet': snippet, 
                    'link': link,
                    'sitelinks': sitelinks
                })
                
            except Exception as e:
                print(f'error in organic results: {e}')
        
        return organic_list



    def searching_sponsored(self, soup):
        all_sponsored = soup.find_all('div', class_='uEierd')
        spons = []
        c = 0  # счетчик позиции

        for item in all_sponsored:
            c += 1

            sponsor_name = item.find('div', class_='Aozhyc Sqrs4e TElO2c OSrXXb')
            sponsor_name = sponsor_name.text if sponsor_name else None

            sponsor_link = item.find('a', class_='sVXRqc')
            if sponsor_link:
                title_tag = sponsor_link.find('div', {'role': 'heading'})
                title = title_tag.text if title_tag else None
                tracking_link = sponsor_link.get('data-rw')
                href_link = sponsor_link.get('href')

                domain = urlparse(href_link).netloc if href_link else None
            else:
                title = tracking_link = href_link = domain = None

            description_tag = item.find('div', class_='p4wth')
            spons_descr = description_tag.text.strip() if description_tag else None

            sublinks_section = item.find('div', class_='dcuivd')
            sublinks_list = []

            if sublinks_section:
                sublinks = sublinks_section.find_all('a')

                for sub in sublinks:
                    sub_title = sub.text.strip() if sub else None
                    sub_href = sub.get('href')
                    sub_tracking_link = sub.get('data-rw')

                    if sub_title and sub_href:
                        sublinks_list.append({
                            'title': sub_title,
                            'description': None,  # Описание для sublink-ов отсутствует
                            'link': sub_href,
                            'tracking_link': sub_tracking_link
                        })

            ad_data = {
                'position': c,
                'domain': domain,
                'source': sponsor_name,
                'link': href_link,
                'tracking_link': tracking_link,
                'title': title,
                'description': spons_descr
            }

            if sublinks_list:
                ad_data['sitelinks'] = sublinks_list

            spons.append(ad_data)

        return spons



    async def make_json(self, content):
        try:
            # Сохраняем HTML для дебага
            with open('last_response_desktop.html', 'w', encoding='utf-8') as f:
                f.write(content)
                
            soup = BeautifulSoup(content, 'lxml')
            to_json = {}
            to_json['organic'] = self.searching_organic(soup)
            to_json['ads'] = self.searching_sponsored(soup)
            # my_json = json.dumps(to_json, indent=4, ensure_ascii=False)
            return to_json
        except Exception as e:
            print(f'error in make_json {e}')

# scrap = DekstopScrape()

# with open('results/burger.html', 'r') as f:
#     cont = f.read()
# d = asyncio.run(scrap.make_json(cont))
# print(json.dumps(d, indent=4))


