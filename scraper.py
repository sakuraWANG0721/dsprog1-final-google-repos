"""
GitHub の Google のリポジトリ一覧ページをスクレイピングするプログラム

取得する情報: リポジトリ名, 主要な言語, スターの数
GitHub の API は使わず, ブラウザで見るページ (HTML) から情報を取り出す。

ページ: https://github.com/orgs/google/repositories?q=sort:name-asc&page=1
  - 1ページに 30 個のリポジトリがのっている
  - q=sort:name-asc で名前順にしている
    (デフォルトの「更新順」だと, スクレイピング中に順番が変わって
     取りこぼしや重複が出るため)
"""

import json
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://github.com/orgs/google/repositories"
HEADERS = {
    # どのプログラムからのアクセスか分かるように User-Agent をつける
    "User-Agent": "Mozilla/5.0 (DS Programming 1 student assignment)"
}
MAX_RETRY = 5       # エラーのときに何回までやり直すか
DEFAULT_WAIT_429 = 60   # 429 (アクセスしすぎ) で待つ秒数が分からないときに待つ秒数


def fetch_html(page):
    """指定したページ番号の HTML を取得して返す"""
    params = {"q": "sort:name-asc", "page": page}

    for attempt in range(1, MAX_RETRY + 1):
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)

            # 429 = アクセスしすぎ。1秒ずつ待っていても, 50ページくらい続けると返ってくる。
            # GitHub は「Retry-After: 120」のように待つ秒数を教えてくれるので, その通り待つ。
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "")
                wait = int(retry_after) if retry_after.isdigit() else DEFAULT_WAIT_429
                print(f"  page {page}: アクセスが多すぎると言われたので {wait} 秒待ちます "
                      f"({attempt}/{MAX_RETRY}回目)")
                time.sleep(wait)
                continue

            response.raise_for_status()   # 404 や 500 などのときはエラーにする
            return response.text
        except requests.RequestException as e:
            print(f"  page {page} の取得に失敗 ({attempt}/{MAX_RETRY}回目): {e}")
            if attempt == MAX_RETRY:
                raise
            time.sleep(5)   # 少し長めに待ってからやり直す

    raise RuntimeError(f"page {page} を {MAX_RETRY} 回試しても取得できませんでした")


def parse_repositories(html):
    """
    HTML からリポジトリの情報を取り出す

    画面に表示されているスター数は「20k」「1.5k」のように省略されているので,
    同じ HTML の中にある <script data-target="react-app.embeddedData"> の
    データ (ページを表示するために埋め込まれている JSON) から正確な値を読む。

    戻り値: (リポジトリのリスト, 全部のページ数)
    """
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", attrs={"data-target": "react-app.embeddedData"})
    if script is None:
        raise ValueError("リポジトリのデータが見つかりません (ページの構造が変わった可能性があります)")

    data = json.loads(script.string)
    page_data = data["payload"]["orgReposPageRoute"]

    repositories = []
    for repo in page_data["repositories"]:
        # 言語が無いリポジトリ (ドキュメントだけなど) は None になる
        language = repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None
        repositories.append({
            "name": repo["name"],
            "language": language,
            "stars": repo["starsCount"],
        })

    return repositories, page_data["pageCount"]


def scrape_all(max_pages=None):
    """
    1ページ目から最後のページまで順番にスクレイピングする
    max_pages を指定すると, そのページ数で止める (テスト用)
    """
    all_repositories = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        html = fetch_html(page)
        repositories, total_pages = parse_repositories(html)
        if max_pages is not None:
            total_pages = min(total_pages, max_pages)

        all_repositories.extend(repositories)
        print(f"page {page}/{total_pages}: {len(repositories)} 件 (合計 {len(all_repositories)} 件)")

        page += 1
        time.sleep(1)   # サーバーに負担をかけないため, 次のページに行く前に必ず1秒待つ

    return all_repositories


if __name__ == "__main__":
    # 動作確認: 最初の2ページだけ取得して表示する
    for repo in scrape_all(max_pages=2)[:10]:
        print(repo)
