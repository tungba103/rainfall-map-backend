import requests
from bs4 import BeautifulSoup
import argparse
import os
import calendar
from concurrent.futures import ThreadPoolExecutor, as_completed

# Authentication details
USERNAME = 'tungba100302@gmail.com'
PASSWORD = 'tungba100302@gmail.com'

def get_file_urls(session, year, month, day):
    base_url = f'https://arthurhouhttps.pps.eosdis.nasa.gov/gpmdata/{year}/{month:02d}/{day:02d}/gis/'
    response = session.get(base_url)

    # Return early if the request was unsuccessful
    if response.status_code != 200:
        print(f"Cannot access URL: {base_url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    file_urls = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.tif') and '-DAY-' in href:
            full_url = base_url + href
            file_urls.append(full_url)
    
    return file_urls

def process_month(session, year, month):
    days_in_month = calendar.monthrange(year, month)[1]
    month_urls = []

    # Using ThreadPoolExecutor to fetch data for each day concurrently
    with ThreadPoolExecutor(max_workers=8) as day_executor:
        day_futures = {day_executor.submit(get_file_urls, session, year, month, day): day for day in range(1, days_in_month + 1)}

        for future in as_completed(day_futures):
            day = day_futures[future]
            try:
                urls = future.result()
                month_urls.extend(urls)
            except Exception as e:
                print(f"Error processing Day {day:02d} of Month {month:02d}: {e}")

    return month_urls

def main():
    parser = argparse.ArgumentParser(description='Retrieve list of file URLs for a specific year.')
    parser.add_argument('year', type=int, help='The year to retrieve data for')

    args = parser.parse_args()
    year = args.year

    output_dir = "urls"
    output_file = os.path.join(output_dir, f"{year}.txt")
    os.makedirs(output_dir, exist_ok=True)

    # Use session and executor for concurrent month processing
    all_urls = []
    with requests.Session() as session:
        session.auth = (USERNAME, PASSWORD)
        
        # Sequentially process each month and collect URLs in memory
        with ThreadPoolExecutor(max_workers=4) as month_executor:
            month_futures = {month_executor.submit(process_month, session, year, month): month for month in range(1, 13)}

            for future in as_completed(month_futures):
                month = month_futures[future]
                try:
                    urls = future.result()
                    all_urls.extend(urls)
                    print(f"Processed URLs for Year {year}, Month {month:02d}")
                except Exception as e:
                    print(f"Error processing Month {month:02d}: {e}")

    # Write all collected URLs to the file at once
    if all_urls:
        with open(output_file, 'w') as file:
            for url in sorted(all_urls):
                file.write(url + '\n')
        print(f'URL list has been saved to {output_file}')
    else:
        print(f"No URLs found for the year {year}.")

if __name__ == "__main__":
    main()
