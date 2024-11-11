import json
import os

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import google_play_scraper


@dataclass
class Task:
    result_path: str
    app_package_id: str
    keywords: List[str]
    countries: List[str]
    n_hits: Optional[int] = 30
    language: Optional[str] = 'en'


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
        for country in task.countries:
            app_rank: int = 0
            app_listings: List[dict[str, dict]] = []

            search_results = google_play_scraper.search(
                keyword,
                lang='en',
                country=country,
                n_hits=task.n_hits,
            )

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
                    app_rank = position
                    print(f'Found ==> keyword: {keyword}   country={country}  rank: {app_rank}')

            if app_rank == 0:
                print(f'Not ranked ==> keyword: {keyword}   country={country}')

                search_result[keyword] = {
                    country: {
                        'app_rank': app_rank,
                        'app_listings': app_listings
                    }
                }

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
        file.write(json.dumps(json_data))


def main():
    tasks = load_tasks_from_json()

    for task in tasks:
        print(f'Looking up: {task.app_package_id}')
        task_result = execute_task(task)
        write_result(task_result, task)

    print('Saved results')


if __name__ == '__main__':
    main()
