from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import os
import urllib.request


TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("GH_LOGIN")


if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN is not set")

if not USERNAME:
    raise RuntimeError("GH_LOGIN is not set")


QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {

  user(login: $login) {

    contributionsCollection(from: $from, to: $to) {

      contributionCalendar {

        totalContributions

        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }

    repositories(
      first: 100
      ownerAffiliations: OWNER
      privacy: PUBLIC
    ) {

      nodes {

        name

        languages(
          first: 10
          orderBy: {field: SIZE, direction: DESC}
        ) {

          edges {
            size

            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""


today = datetime.now(timezone.utc).date()

from_date = today - timedelta(days=364)

from_dt = datetime(
    from_date.year,
    from_date.month,
    from_date.day,
    tzinfo=timezone.utc
)

to_dt = datetime(
    today.year,
    today.month,
    today.day,
    23,
    59,
    59,
    tzinfo=timezone.utc
)


variables = {
    "login": USERNAME,
    "from": from_dt.isoformat(),
    "to": to_dt.isoformat(),
}


payload = json.dumps({
    "query": QUERY,
    "variables": variables
}).encode()


request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USERNAME,
    },
    method="POST",
)


with urllib.request.urlopen(request) as response:
    data = json.loads(response.read())


if "errors" in data:
    raise RuntimeError(data["errors"])


total = data["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]["totalContributions"]
calendar = data["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]
# --------------------------------------------------
# Calculate language statistics
# --------------------------------------------------

repositories = data["data"]["user"]["repositories"]["nodes"]

language_bytes = {}

language_colors = {}


for repo in repositories:

    if not repo:
        continue

    languages = repo.get("languages")

    if not languages:
        continue

    for edge in languages["edges"]:

        language = edge["node"]["name"]
        size = edge["size"]
        color = edge["node"].get("color")

        language_bytes[language] = (
            language_bytes.get(language, 0) + size
        )

        if color:
            language_colors[language] = color


# Sort languages by amount of code

sorted_languages = sorted(
    language_bytes.items(),
    key=lambda item: item[1],
    reverse=True
)


# Keep the top 5

top_languages = sorted_languages[:5]


total_language_bytes = sum(
    language_bytes.values()
)


print()
print("TOP LANGUAGES")
print("-------------")

for language, size in top_languages:

    percentage = (
        size / total_language_bytes * 100
        if total_language_bytes
        else 0
    )

    print(
        f"{language}: {percentage:.1f}%"
    )

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append({
            "date": day["date"],
            "count": day["contributionCount"]
        })

days.sort(key=lambda x: x["date"])
# --------------------------------------------------
# Calculate contribution streaks
# --------------------------------------------------

current_streak = 0
longest_streak = 0

current_start = None
current_end = None

longest_start = None
longest_end = None


# Calculate current streak
# Start from the most recent day.

for day in reversed(days):

    if day["count"] > 0:

        current_streak += 1

        if current_end is None:
            current_end = day["date"]

        current_start = day["date"]

    else:
        break


# Calculate longest streak

streak = 0
streak_start = None

for day in days:

    if day["count"] > 0:

        if streak == 0:
            streak_start = day["date"]

        streak += 1

        if streak > longest_streak:

            longest_streak = streak

            longest_start = streak_start
            longest_end = day["date"]

    else:

        streak = 0
        streak_start = None


print()
print("STREAK STATISTICS")
print("-----------------")

print(
    f"Current streak: {current_streak} days"
)

print(
    f"Longest streak: {longest_streak} days"
)

if current_start and current_end:
    print(
        f"Current: {current_start} → {current_end}"
    )

if longest_start and longest_end:
    print(
        f"Longest: {longest_start} → {longest_end}"
    )
print(f"Contribution days retrieved: {len(days)}")

print("Last 7 days:")

for day in days[-7:]:
    print(day["date"], day["count"])
print("GitHub statistics successfully retrieved!")
print(f"Username: {USERNAME}")
print(f"Contributions in the last year: {total}")

 

# --------------------------------------------------
# Create contribution sparkline SVG
# --------------------------------------------------

OUTPUT = Path("stats/stats.svg")

# Use the last 52 weeks of contribution data.
# 7 days × 52 weeks = 364 days.

weekly = []

for i in range(0, len(days), 7):
    week = days[i:i + 7]

    total = sum(
        day["count"]
        for day in week
    )

    weekly.append(total)


# Keep the latest 52 weeks
weekly = weekly[-52:]


# --------------------------------------------------
# Sparkline dimensions
# --------------------------------------------------

WIDTH = 600
HEIGHT = 180

LEFT = 30
RIGHT = 30

CHART_TOP = 80
CHART_BOTTOM = 150

CHART_WIDTH = WIDTH - LEFT - RIGHT
CHART_HEIGHT = CHART_BOTTOM - CHART_TOP


maximum = max(weekly) if weekly else 1


# --------------------------------------------------
# Convert weekly values into SVG points
# --------------------------------------------------

points = []

for i, value in enumerate(weekly):

    if len(weekly) == 1:
        x = LEFT
    else:
        x = (
            LEFT
            + i * CHART_WIDTH / (len(weekly) - 1)
        )

    y = (
        CHART_BOTTOM
        - (value / maximum) * CHART_HEIGHT
    )

    points.append(
        f"{x:.2f},{y:.2f}"
    )


polyline = " ".join(points)


# --------------------------------------------------
# Create SVG
# --------------------------------------------------

svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}">

    <rect
        width="100%"
        height="100%"
        fill="white"/>

    <text
        x="{LEFT}"
        y="30"
        font-family="monospace"
        font-size="16"
        fill="#555">
        GITHUB CONTRIBUTIONS
    </text>

    <text
        x="{LEFT}"
        y="65"
        font-family="monospace"
        font-size="32"
        font-weight="bold"
        fill="#111">
        {total}
    </text>

    <polyline
        points="{polyline}"
        fill="none"
        stroke="#111"
        stroke-width="2"/>

</svg>
'''


OUTPUT.write_text(
    svg,
    encoding="utf-8"
)

print(f"Stats SVG saved to: {OUTPUT}")
print(f"Weeks plotted: {len(weekly)}")
# --------------------------------------------------
# Create streak SVG
# --------------------------------------------------

STREAK_OUTPUT = Path("stats/streak.svg")

streak_svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="600"
    height="180"
    viewBox="0 0 600 180">

    <rect
        width="100%"
        height="100%"
        fill="white"/>

    <text
        x="30"
        y="35"
        font-family="monospace"
        font-size="16"
        fill="#555">
        CONTRIBUTION STREAK
    </text>

    <text
        x="30"
        y="85"
        font-family="monospace"
        font-size="36"
        font-weight="bold"
        fill="#111">
        CURRENT: {current_streak} DAYS
    </text>

    <text
        x="30"
        y="125"
        font-family="monospace"
        font-size="24"
        fill="#111">
        LONGEST: {longest_streak} DAYS
    </text>

    <text
        x="30"
        y="155"
        font-family="monospace"
        font-size="14"
        fill="#555">
        {longest_start} → {longest_end}
    </text>

</svg>
'''

STREAK_OUTPUT.write_text(
    streak_svg,
    encoding="utf-8"
)

print(f"Streak SVG saved to: {STREAK_OUTPUT}")
# --------------------------------------------------
# Create languages SVG
# --------------------------------------------------

LANG_OUTPUT = Path("stats/langs.svg")

LANG_WIDTH = 600
LANG_HEIGHT = 240

svg_parts = [
    f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{LANG_WIDTH}"
    height="{LANG_HEIGHT}"
    viewBox="0 0 {LANG_WIDTH} {LANG_HEIGHT}">

    <rect
        width="100%"
        height="100%"
        fill="white"/>

    <text
        x="30"
        y="35"
        font-family="monospace"
        font-size="16"
        fill="#555">
        TOP LANGUAGES
    </text>
'''
]


# --------------------------------------------------
# Draw each language
# --------------------------------------------------

BAR_X = 30
BAR_Y = 60
BAR_WIDTH = 540
BAR_HEIGHT = 18

GAP = 32


for index, (language, size) in enumerate(top_languages):

    percentage = (
        size / total_language_bytes * 100
        if total_language_bytes
        else 0
    )

    y = BAR_Y + index * GAP

    bar_width = (
        percentage / 100
    ) * BAR_WIDTH

    color = language_colors.get(
        language,
        "#555"
    )

    svg_parts.append(
        f'''
    <rect
        x="{BAR_X}"
        y="{y}"
        width="{BAR_WIDTH}"
        height="{BAR_HEIGHT}"
        fill="#eeeeee"/>

    <rect
        x="{BAR_X}"
        y="{y}"
        width="{bar_width:.2f}"
        height="{BAR_HEIGHT}"
        fill="{color}"/>

    <text
        x="{BAR_X}"
        y="{y + 14}"
        font-family="monospace"
        font-size="12"
        fill="#111">
        {language}
    </text>

    <text
        x="{BAR_X + BAR_WIDTH}"
        y="{y + 14}"
        text-anchor="end"
        font-family="monospace"
        font-size="12"
        fill="#555">
        {percentage:.1f}%
    </text>
'''
    )


svg_parts.append("</svg>")


LANG_OUTPUT.write_text(
    "".join(svg_parts),
    encoding="utf-8"
)

print(f"Languages SVG saved to: {LANG_OUTPUT}")
# --------------------------------------------------
# Create contribution year SVG
# --------------------------------------------------

YEAR_OUTPUT = Path("stats/year.svg")

YEAR_RAMP = " .:-=+*#%@"

YEAR_WIDTH = 900
YEAR_HEIGHT = 180

# Find the maximum daily contribution count
max_daily = max(
    (day["count"] for day in days),
    default=1
)


# Convert each day into one character
year_chars = []

for day in days:

    count = day["count"]

    if count == 0:
        char = " "
    else:
        index = int(
            count / max_daily * (len(YEAR_RAMP) - 1)
        )

        index = min(
            index,
            len(YEAR_RAMP) - 1
        )

        char = YEAR_RAMP[index]

    year_chars.append(char)


# Split into rows of 73 characters
# 365 / 73 = 5 rows

ROWS = []

for i in range(0, len(year_chars), 73):

    ROWS.append(
        "".join(year_chars[i:i + 73])
    )


YEAR_FONT_SIZE = 13
YEAR_LINE_HEIGHT = 24


svg_parts = [
    f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{YEAR_WIDTH}"
    height="{YEAR_HEIGHT}"
    viewBox="0 0 {YEAR_WIDTH} {YEAR_HEIGHT}">

    <rect
        width="100%"
        height="100%"
        fill="white"/>

    <text
        x="30"
        y="30"
        font-family="monospace"
        font-size="16"
        fill="#555">
        CONTRIBUTION YEAR
    </text>
'''
]


for i, row in enumerate(ROWS):

    y = 60 + i * YEAR_LINE_HEIGHT

    svg_parts.append(
        f'''
    <text
        x="30"
        y="{y}"
        font-family="monospace"
        font-size="{YEAR_FONT_SIZE}"
        xml:space="preserve"
        fill="#111">
        {row}
    </text>
'''
    )


svg_parts.append("</svg>")


YEAR_OUTPUT.write_text(
    "".join(svg_parts),
    encoding="utf-8"
)

print(f"Year SVG saved to: {YEAR_OUTPUT}")