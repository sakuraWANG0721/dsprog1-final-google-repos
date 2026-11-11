"""
メインのプログラム
1. Google のリポジトリをスクレイピングする
2. データベースに保存する

実行: python main.py
"""

import database
import scraper


def main():
    print("スクレイピングを開始します (1ページごとに1秒待つので, 数分かかります)")
    repositories = scraper.scrape_all()

    conn = database.connect()
    database.create_table(conn)
    database.save_repositories(conn, repositories)

    count = conn.execute("SELECT COUNT(*) FROM repositories").fetchone()[0]
    conn.close()

    print(f"完了: {count} 件のリポジトリを {database.DB_PATH} に保存しました")


if __name__ == "__main__":
    main()
