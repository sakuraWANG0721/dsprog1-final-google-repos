"""
データベースに保存したデータを SELECT 文で表示するプログラム

実行:
  python show.py            -> 全体の件数, スター数ランキング, 言語別の集計を表示
  python show.py Python     -> 指定した言語のリポジトリだけをスター数順に表示
"""

import os
import sys

import database


def print_table(headers, rows):
    """SELECT の結果を表の形で表示する"""
    # 列ごとに一番長い文字数に合わせて幅をそろえる
    widths = [len(h) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))

    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        cells = []
        for i, value in enumerate(row):
            # 数字は右寄せ, 文字は左寄せ
            if isinstance(value, int):
                cells.append(str(value).rjust(widths[i]))
            else:
                cells.append(str(value).ljust(widths[i]))
        print("  ".join(cells))
    print()


def show_summary(conn):
    total, last_time = conn.execute(
        "SELECT COUNT(*), MAX(scraped_at) FROM repositories"
    ).fetchone()
    print(f"保存されているリポジトリ: {total} 件 (取得日時: {last_time})\n")


def show_top_stars(conn, limit=20):
    print(f"■ スターの数が多いリポジトリ TOP {limit}")
    rows = conn.execute("""
        SELECT name, IFNULL(language, '(none)'), stars
        FROM repositories
        ORDER BY stars DESC
        LIMIT ?
    """, (limit,)).fetchall()
    print_table(["name", "language", "stars"], rows)


def show_languages(conn, limit=10):
    print(f"■ 言語別のリポジトリ数 TOP {limit}")
    rows = conn.execute("""
        SELECT IFNULL(language, '(none)'), COUNT(*) AS repo_count, SUM(stars)
        FROM repositories
        GROUP BY language
        ORDER BY repo_count DESC
        LIMIT ?
    """, (limit,)).fetchall()
    print_table(["language", "repos", "total_stars"], rows)


def show_by_language(conn, language, limit=10):
    print(f"■ {language} のリポジトリ (スター数順 TOP {limit})")
    rows = conn.execute("""
        SELECT name, stars
        FROM repositories
        WHERE language = ?
        ORDER BY stars DESC
        LIMIT ?
    """, (language, limit)).fetchall()
    if rows:
        print_table(["name", "stars"], rows)
    else:
        print(f"{language} のリポジトリは見つかりませんでした\n")


def main():
    # DB ファイルが無いのに connect() すると空のファイルが作られてしまうので先に確認する
    if not os.path.exists(database.DB_PATH):
        print("データがありません。先に python main.py を実行してください。")
        return

    conn = database.connect()

    # テーブルがまだ無い (main.py を実行していない) ときのチェック
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'repositories'"
    ).fetchone()
    if exists is None:
        print("データがありません。先に python main.py を実行してください。")
        conn.close()
        return

    show_summary(conn)
    if len(sys.argv) >= 2:
        show_by_language(conn, sys.argv[1])
    else:
        show_top_stars(conn)
        show_languages(conn)

    conn.close()


if __name__ == "__main__":
    main()
