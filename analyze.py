import json
import os.path
from typing import List, Optional, Tuple

import print_color
from prettytable import PrettyTable

from run import load_tasks_from_json, Task


def load_result_from_file(path: str):
    with open(path, 'r') as file:
        return json.loads(file.read())


def order_by_app_and_countries(result_data: dict):
    cleaned_data = {}
    """
    cleaned_data = {
        'app_name': {
           'us': [],
           'in': []
        }
    }
    """
    for data in result_data:
        for keyword, country_data in data.items():
            if not cleaned_data.get(keyword):
                cleaned_data[keyword] = {}

            for country, rank_data in country_data.items():
                if not cleaned_data[keyword].get(country):
                    cleaned_data[keyword][country] = []

                cleaned_data[keyword][country].append(rank_data)

    return cleaned_data


def analyze_result(task) -> Optional[dict]:
    if not os.path.exists(task.result_path):
        return

    result_data = load_result_from_file(task.result_path)
    cleaned_data = order_by_app_and_countries(result_data)
    return cleaned_data


def get_latest_app_rank(rank_data: List[dict]) -> int:
    last_crawl_rank_detail = rank_data[-1]
    return last_crawl_rank_detail['app_rank']


def get_growth(rank_data: List[dict]) -> Tuple[int, int]:
    """
    Returns previous growth and new growth
    :param rank_data:
    :return: previous_growth, new_growth
    """
    if len(rank_data) < 2:
        return 0, 0

    if len(rank_data) > 3:
        previous_growth = rank_data[-2]['app_rank'] - rank_data[-3]['app_rank']
    else:
        previous_growth = 0

    new_growth = rank_data[-1]['app_rank'] - rank_data[-2]['app_rank']

    return new_growth, previous_growth


def get_average_rank(rank_data: List[dict]) -> int:
    total = 0
    days_considered = 30 * 2  # 2 months

    for rank in rank_data[:days_considered]:
        total += rank['app_rank']

    return round(total / len(rank_data), 1)


def prepare_summary(task: Task, result: dict):
    table = PrettyTable()
    table.field_names = ['S.N', 'KEYWORD', 'COUNTRY', 'AVERAGE RANK', 'CURRENT RANK', 'GROWTH']

    previous_growth = 0
    new_growth = 0

    col_count = 0
    for keyword, country_data in result.items():

        # Iterate through each country ranks
        for country, rank_data in country_data.items():
            if len(rank_data) == 0:
                """
                Rank data list for the given country is empty.
                """
                continue

            latest_app_rank = get_latest_app_rank(rank_data)
            average_app_rank = get_average_rank(rank_data)
            new_growth, previous_growth = get_growth(rank_data)

            # Compute previous and new growth based on the country for given keyword
            previous_growth += previous_growth
            new_growth += new_growth

            if latest_app_rank == 0:
                formatted_growth = 'LOST RANKING'
            elif new_growth > 0:
                formatted_growth = f'+{new_growth}'
            else:
                formatted_growth = new_growth

            col_count += 1
            table.add_row([col_count, keyword, country.upper(), average_app_rank, latest_app_rank, formatted_growth])

    table.align['S.N'] = 'r'
    table.align['KEYWORD'] = 'l'
    table.align['AVERAGE RANK'] = 'r'
    table.align['CURRENT RANK'] = 'r'
    table.align['GROWTH'] = 'r'

    print_color.print(f'Package: {task.app_package_id}', color='green')
    print(table)

    # Print growth information
    growth_difference = new_growth - previous_growth

    if growth_difference >= 0:
        print_color.print(f'Overall growth: +{new_growth - previous_growth}', color='green')
    else:
        print_color.print(f'Overall growth: {new_growth - previous_growth}', color='red')

    print('\n')


def analyze(task: Task):
    result = analyze_result(task)

    if result:
        # Lazy file path hack
        out_path = task.result_path.replace('.json', '-formatted.json')
        with open(out_path, 'w') as file:
            file.write(json.dumps(result, indent=2, ensure_ascii=False))

        prepare_summary(task, result)


def main():
    tasks = load_tasks_from_json()

    for task in tasks:
        analyze(task)


if __name__ == '__main__':
    main()
