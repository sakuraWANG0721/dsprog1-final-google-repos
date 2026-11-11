# DS Programming 1 最終個人課題

GitHub で Google が管理しているリポジトリ ( https://github.com/google ) の情報をスクレイピングして,
SQLite のデータベースに保存し, SELECT 文で表示するプログラムです。

取得する情報は **リポジトリ名, 主要な言語, スターの数** の3つです。

## ファイル構成

| ファイル | 内容 |
|---|---|
| `scraper.py` | GitHub のページをスクレイピングしてリポジトリの情報を取り出す |
| `database.py` | テーブルの作成と, データの保存 (SQLite) |
| `main.py` | スクレイピング → DB に保存 をまとめて実行する |
| `show.py` | 保存したデータを SELECT 文で表示する |
| `google_repos.db` | 実際にスクレイピングしたデータ (2026-11-11 取得, 2945 件) |
| `requirements.txt` | 使っているライブラリ |

## 実行方法

```bash
# 1. 仮想環境を作ってライブラリを入れる (最初の1回だけ)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. スクレイピングして DB に保存する (5〜10分くらいかかる)
python main.py

# 3. 保存したデータを表示する
python show.py           # スター数ランキングと言語別の集計
python show.py Python    # Python のリポジトリだけ表示 (言語名は変えられる)
```

`google_repos.db` はリポジトリに入れてあるので, 2 を飛ばして 3 だけでも結果を見られます。

## テーブルの設計

```sql
CREATE TABLE repositories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE,  -- リポジトリ名
    language   TEXT,                     -- 主要な言語 (無いときは NULL)
    stars      INTEGER NOT NULL,         -- スターの数
    scraped_at TEXT    NOT NULL          -- スクレイピングした日時
);
```

- 同じリポジトリが2回入らないように `name` に `UNIQUE` をつけた。
- 言語が無いリポジトリ (ドキュメントだけのものなど) もあるので, `language` は NULL を許可した。

## スクレイピングのやり方

- **GitHub の API は使っていない。** ブラウザで見るのと同じページ
  `https://github.com/orgs/google/repositories?q=sort:name-asc&page=1` を requests で取得し, BeautifulSoup で解析している。
- **1回アクセスするごとに `time.sleep(1)` を入れている。** GitHub の robots.txt にも `Crawl-delay: 1` と書いてあり,
  このページ (`/orgs/*/repositories?q=*`) は `Allow` になっていることも確認した。
- 1ページに30件ずつのっているので, 1ページ目から最後のページ (99ページ) まで順番に取得した。

### やってみて困ったことと工夫したこと

1. **`github.com/google?tab=repositories` だと10件しか取れなかった**
   ログインしていない状態だとページ送りのリンクが出ず, `page=2` にしても1ページ目と同じ内容が返ってきた。
   `github.com/orgs/google/repositories` の方はページ送りができたので, こちらを使った。

2. **画面のスター数が「20k」「1.5k」のように省略されていた**
   画面の文字をそのまま使うと正確な数にならない。
   同じ HTML の中に, ページを表示するためのデータが `<script data-target="react-app.embeddedData">` として
   埋め込まれていて, そこには `19954` のような正確な数が入っていたので, そこから読むようにした。
   (API ではなく, ページの HTML の一部を BeautifulSoup で探して読んでいる。)

3. **並び順が途中で変わる問題**
   最初の並び順は「最近更新された順」なので, スクレイピングしている数分の間にリポジトリが更新されると
   順番がずれて, 取りこぼしや重複が出る可能性がある。`q=sort:name-asc` で名前順にして, 順番が変わらないようにした。

4. **50ページくらいで「429 Too Many Requests」になった**
   `time.sleep(1)` を入れていても, 50ページくらい続けてアクセスすると GitHub に止められた。
   そのとき返ってくる `Retry-After: 120` (120秒待ってね, という意味) を読んで, その秒数だけ待ってからやり直すようにした。
   実際に 41ページ目と79ページ目で止められたが, 最後まで取得できた。

5. **途中でエラーが起きたときに DB が中途半端にならないようにした**
   保存は `with conn:` (トランザクション) の中で行うので, 途中で失敗したら前のデータに戻る。

## 実行結果

`python show.py` の結果 (2026-11-11 にスクレイピングしたデータ)

```text
保存されているリポジトリ: 2945 件 (取得日時: 2026-11-11 09:18:28)

■ スターの数が多いリポジトリ TOP 20
name                   language    stars
---------------------  ----------  -----
material-design-icons  (none)      54272
guava                  Java        51922
zx                     JavaScript  45838
styleguide             Emacs Lisp  39818
googletest             C++         39722
leveldb                C++         39535
langextract            Python      39298
comprehensive-rust     Rust        33519
material-design-lite   HTML        32194
python-fire            Python      28226
flatbuffers            C++         26625
gson                   Java        24231
skills                 Python      23829
eng-practices          (none)      23276
adk-python             Python      22178
ExoPlayer              Java        21931
iosched                Kotlin      21623
fonts                  HTML        20750
filament               C++         20731
gvisor                 Go          19954

■ 言語別のリポジトリ数 TOP 10
language    repos  total_stars
----------  -----  -----------
Python        629       392528
C++           363       431083
Go            309       294649
Java          241       281946
JavaScript    227       134517
(none)        193       122314
TypeScript    122        67027
Rust          110        81107
C             109        67883
Dart           91        17482
```

- 取得したリポジトリは **2945 件** で, GitHub のページに表示されている数 (2945) と同じだった。
- リポジトリの数は Python が一番多いが, スターの合計は C++ の方が多かった。

## Git の進め方

授業のルールに沿って, `main` では直接作業せず, 機能ごとにブランチを切ってから `main` に merge した。

| ブランチ | 内容 |
|---|---|
| `feature/scraper` | スクレイピングの処理 |
| `feature/database` | DB の作成と保存の処理 |
| `fix/rate-limit` | 429 エラーへの対応 (実際に動かして見つかった問題の修正) |
| `feature/select` | SELECT 文で表示する処理 |
| `docs/readme` | README と取得したデータ |
| `fix/sleep` | 課題の指示通り `time.sleep(1)` と書くように修正 |

merge は `git merge --no-ff` で行い, どのブランチから入ったかが履歴に残るようにした。
