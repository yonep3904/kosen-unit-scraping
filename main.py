import requests
from bs4 import BeautifulSoup
from pathlib import Path
from dataclasses import dataclass
from typing import Literal
import csv
import time

DIR = Path(__file__).parent
SAVE_PATH = DIR / "output.csv"

BASE_URL = "https://syllabus.kosen-k.go.jp"
URL: list[tuple[str, int]] = [
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=36&year=2021&lang=ja", 1),  # 1年次(学科共通)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=36&year=2022&lang=ja", 2),  # 2年次(学科共通)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=36&year=2023&lang=ja", 3),  # 3年次(学科共通)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=36&year=2024&lang=ja", 4),  # 4年次(学科共通)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=36&year=2025&lang=ja", 5),  # 5年次(学科共通)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=34&year=2021&lang=ja", 1),  # 1年次(情報システムコース)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=34&year=2022&lang=ja", 2),  # 2年次(情報システムコース)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=34&year=2023&lang=ja", 3),  # 3年次(情報システムコース)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=34&year=2024&lang=ja", 4),  # 4年次(情報システムコース)
    ("https://syllabus.kosen-k.go.jp/Pages/PublicSubjects?school_id=44&department_id=34&year=2025&lang=ja", 5),  # 5年次(情報システムコース)
]


def main():
    units: list[KosenUnit] = []

    # すべてのURLからシラバスを取得して解析し、単位情報を収集
    for url, grade in URL:
        print(f"Fetching {url} ...")

        html = get_syllabus(url)
        units_all = parse_syllabus(html)
        units_filtered = filter(
            lambda x: x.grade == grade, units_all
        )  # 学年でフィルタリング
        units.extend(units_filtered)

        # サーバーへの負荷を避けるために待機
        time.sleep(0.5)

    # 学年→ 専門/一般 → 必修/選択 → 科目番号の順でソート
    units.sort(key=lambda x: (x.grade, x.category, x.required, x.code))

    # CSVに保存
    csv_headers = [
        "学年",
        "必修/選択など種別",
        "科目",
        "シラバスURL",
        "単位",
        "履修状況",
    ]
    csv_rows = [
        [
            u.grade,
            u.required,
            u.name,
            u.url,
            u.credit,
            "合格",
        ]
        for u in units
    ]

    with open(SAVE_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        writer.writerows(csv_rows)

    print("Done! Saved to", SAVE_PATH)


@dataclass
class KosenUnit:
    category: Literal["専門", "一般"]  # 専門/一般
    required: Literal["必修", "選択"]  # 必修/選択
    name: str  # 科目名
    code: str  # 科目番号
    credit: int  # 単位数
    grade: int  # 学年
    teacher: str  # 担当教員
    url: str  # URL

    def __str__(self) -> str:
        return f"{self.code} {self.name} ({self.credit}単位) - {self.teacher} [{self.category} {self.required}]"


def get_syllabus(url: str) -> str:
    # 403エラー対策で User-Agent を指定
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ja",
    }

    res = requests.get(url, headers=headers)
    return res.text


# <tr data-course-value="" class="">
#     <td class="c1">一般</td>
#     <td>必修</td>
#     <td>
#     <div class="subject-item" id="subject_0015">
#         <a
#         class="mcc-show"
#         href="/Pages/PublicSyllabus?school_id=44&department_id=36&subject_code=1Z002&year=2025&lang=ja"
#         >基礎解析学</a
#         >
#         <span class="mcc-hide">基礎解析学</span>
#     </div>
#     </td>
#     <td>1Z002</td>
#     <td>履修単位</td>
#     <td>4</td>

#     <td class="c1m" colspan="2">2</td>
#     <td class="c1m" style="display: none"></td>
#     <td class="c1m" colspan="2">2</td>
#     <td class="c1m" style="display: none"></td>

#     <td class="c2m" colspan="2"></td>
#     <td class="c2m" style="display: none"></td>
#     <td class="c2m" colspan="2"></td>
#     <td class="c2m" style="display: none"></td>

#     <td class="c3m" colspan="2"></td>
#     <td class="c3m" style="display: none"></td>
#     <td class="c3m" colspan="2"></td>
#     <td class="c3m" style="display: none"></td>

#     <td class="c4m" colspan="2"></td>
#     <td class="c4m" style="display: none"></td>
#     <td class="c4m" colspan="2"></td>
#     <td class="c4m" style="display: none"></td>

#     <td class="c5m" colspan="2"></td>
#     <td class="c5m" style="display: none"></td>
#     <td class="c5m" colspan="2"></td>
#     <td class="c5m" style="display: none"></td>

#     <td width="122">
#     ここに担当教員名が入る
#     </td>
#     <td style=""></td>
# </tr>

# <td> タグの順番
# 0: 科目区分 (専門/一般)
# 1: 科目区分 (必修/選択)
# 2: 科目名 (a タグの中)
# 3: 科目番号
# 4: 単位種別 (履修単位/学修単位)
# 5: 単位数
# 6-15: 学年別週当授業時数
# 16: 担当教員
# 17: 履修上の区分


def parse_syllabus(html: str) -> list[KosenUnit]:
    units: list[KosenUnit] = []
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="sytablenc")
    if table is None:
        return units

    rows = table.find_all("tr", attrs={"data-course-value": True})

    for row in rows:
        tds = row.find_all("td")

        category = tds[0].get_text(strip=True)
        required = tds[1].get_text(strip=True)

        subject_link = tds[2].find("a")
        name = subject_link.get_text(strip=True)
        url = BASE_URL + subject_link["href"]

        code = tds[3].get_text(strip=True)

        credit = int(tds[5].get_text(strip=True) or 0)

        teacher = tds[-2].get_text(strip=True)

        # 学年判定
        grade = 0
        for g in range(1, 6):
            cells = row.find_all("td", class_=f"c{g}m")
            for c in cells:
                if c.get_text(strip=True):
                    grade = g
                    break
            if grade:
                break

        units.append(
            KosenUnit(
                category=category,
                required=required,
                name=name,
                code=code,
                credit=credit,
                grade=grade,
                teacher=teacher,
                url=url,
            )
        )

    return units


if __name__ == "__main__":
    main()
