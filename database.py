"""
スクレイピングしたデータを保存するためのデータベース (SQLite) の処理
"""

import sqlite3
from datetime import datetime

DB_PATH = "google_repos.db"


def connect():
    """データベースに接続する (ファイルが無ければ自動で作られる)"""
    return sqlite3.connect(DB_PATH)


def create_table(conn):
    """リポジトリの情報を入れるテーブルを作る"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,  -- リポジトリ名 (同じ名前は1つだけ)
            language   TEXT,                     -- 主要な言語 (無いときは NULL)
            stars      INTEGER NOT NULL,         -- スターの数
            scraped_at TEXT    NOT NULL          -- スクレイピングした日時
        )
    """)
    conn.commit()


def save_repositories(conn, repositories):
    """
    リポジトリのリストを保存する
    前回のデータは消して, 今回スクレイピングした最新のデータだけを入れる。
    with conn: の中で行うので, 途中でエラーが起きたら全部元に戻る。
    """
    scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with conn:
        conn.execute("DELETE FROM repositories")
        for repo in repositories:
            # 万が一同じリポジトリが2回出てきても, 重複せずに上書きする
            conn.execute("""
                INSERT INTO repositories (name, language, stars, scraped_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    language   = excluded.language,
                    stars      = excluded.stars,
                    scraped_at = excluded.scraped_at
            """, (repo["name"], repo["language"], repo["stars"], scraped_at))
