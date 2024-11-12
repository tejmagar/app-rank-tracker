import json
import os
from datetime import datetime

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import google_play_scraper
import print_color


@dataclass
class Task:
    result_path: str
    app_package_id: str
    keywords: List[str]
    countries: List[str]
    n_hits: Optional[int] = 30
    language: Optional[str] = 'en'
    active: Optional[bool] = True


def load_tasks_from_json():
    tasks: List[Task] = []

    with open('tasks.json', 'r') as file:
        tasks_json: List[dict] = json.load(file)
        for task in tasks_json:
            tasks.append(Task(**task))

    return tasks


def get_search_result(task: Task):
    search_result = {}

    for keyword in task.keywords:
        countries = {}

        for country in task.countries:
            app_rank: int = 0
            app_listings: List[dict[str, dict]] = []

            # noinspection PyBroadException
            try:
                search_results = google_play_scraper.search(
                    keyword,
                    lang='en',
                    country=country,
                    n_hits=task.n_hits,
                )
            except Exception as _:
                print_color.print(
                    f'keyword: {keyword}   country={country}',
                    tag='Failed to fetch', tag_color='yellow', color='yellow'
                )
                continue

            for position, result in enumerate(search_results):
                app_id: str = result['appId']
                title: str = result['title']
                score: float = result['score']
                installs: str = result['installs']

                app_listings.append({
                    app_id: {
                        'title': title,
                        'score': score,
                        'installs': installs
                    }
                })

                if app_id == task.app_package_id:
                    app_rank = position + 1
                    print_color.print(
                        f'keyword: {keyword}   country={country}  rank: {app_rank}',
                        tag='Found', tag_color='green', color='green'
                    )

            if app_rank == 0:
                print_color.print(
                    f'keyword: {keyword}   country={country}',
                    tag='Not Ranked', tag_color='red', color='red'
                )

            country_result = {
                'app_rank': app_rank,
                'app_listings': app_listings,
                'time': str(datetime.now())
            }
            countries[country] = country_result

        search_result[keyword] = countries

    return search_result


def execute_task(task: Task):
    return get_search_result(task)


def write_result(result: dict, task: Task):
    path = Path(task.result_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    if os.path.exists(task.result_path):
        with open(task.result_path, 'r') as file:
            json_data = json.loads(file.read())
    else:
        json_data = []

    json_data.append(result)

    with open(task.result_path, 'w') as file:
        file.write(json.dumps(json_data, indent=2, ensure_ascii=False))


def main():
    tasks = load_tasks_from_json()

    for task in tasks:
        if not task.active:
            continue

        print_color.print(f'Looking up: {task.app_package_id}', tag='progress', tag_color='magenta', color='magenta')
        task_result = execute_task(task)
        write_result(task_result, task)

    print('Saved results')


if __name__ == '__main__':
    main()
