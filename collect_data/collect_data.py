import datetime
import os
from api_calls.api_orgs import collect_api_orgs
from api_calls.api_repos_licenses import collect_api_repos_licenses
from api_calls.api_licenses import collect_api_licenses
from dbkit.db_connector import psqlConnector
from dbkit.queries import API_ORGS_TABLE_INSERT_SQL, API_LICENSES_TABLE_INSERT_SQL, API_REPOS_LICENSES_TABLE_INSERT_SQL
from dotenv import load_dotenv

load_dotenv()


HEADERS = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {os.environ.get("API_TOKEN")}',
    'X-GitHub-Api-Version': '2022-11-28'
}

ORGS = ['moloco', 'woowabros', 'daangn', 'toss',
        'ncsoft', 'line', 'kakao', 'naver', 'nhn']


LICENSES = ['agpl-3.0', 'apache-2.0', 'bsd-2-clause', 'bsd-3-clause', 'bsl-1.0', 'cc0-1.0', 'epl-2.0', 'gpl-2.0', 'gpl-3.0', 'lgpl-2.1', 'mit', 'mpl-2.0', 'unlicense']





def run():
    db = psqlConnector()
    CURRENT_TIME = datetime.datetime.now()

    orgs_data = collect_api_orgs(HEADERS, ORGS, CURRENT_TIME)
    for values in orgs_data:
        db.insert_data(API_ORGS_TABLE_INSERT_SQL, values)

    # repos를 받아와서 처리하는 부분 아직 미완성

    # repos_licenses_data = collect_api_repos_licenses(HEADERS, repos, CURRENT_TIME)
    # for values in repos_licenses_data:
    #     db.insert_data(API_REPOS_LICENSES_TABLE_INSERT_SQL, values)


    # 라이센스가 이미 db에 저장된 경우 pk 충돌 일어남, 이 부분 수정 필요

    # licenses_data = collect_api_licenses(HEADERS, LICENSES, CURRENT_TIME)
    # for values in licenses_data:
    #     db.insert_data(API_LICENSES_TABLE_INSERT_SQL, values)


    db.disconnect()




if __name__ == "__main__":
    run()
