from pathlib import Path
import html


INPUT = Path("stats/portrait.txt")
OUTPUT = Path("stats/portrait.svg")

FONT_SIZE = 12.9
CHAR_WIDTH = 7.74
LINE_HEIGHT = 15.0

lines = INPUT.read_text(encoding="utf-8").splitlines()

# Remove completely empty lines only from the beginning/end
while lines and not lines[0].strip():
    lines.pop(0)

while lines and not lines[-1].strip():
    lines.pop()

if not lines:
    raise RuntimeError("portrait.txt is empty")

rows = len(lines)
cols = max(len(line) for line in lines)

width = cols * CHAR_WIDTH
height = rows * LINE_HEIGHT


svg_parts = []

svg_parts.append(
    f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{width:.0f}"
    height="{height:.0f}"
    viewBox="0 0 {width:.0f} {height:.0f}">
'''
)

svg_parts.append(
    f'''<rect width="100%" height="100%" fill="white"/>
'''
)

svg_parts.append(
    f'''<style>
    .ascii {{
        font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
        font-size: {FONT_SIZE}px;
        font-weight: 400;
        white-space: pre;
    }}
</style>
'''
)


for i, line in enumerate(lines):

    escaped = html.escape(line)

    y = FONT_SIZE + i * LINE_HEIGHT

    delay = i * 0.09

    svg_parts.append(
        f'''
<defs>
    <clipPath id="clip{i}">
        <rect
            x="0"
            y="{i * LINE_HEIGHT:.2f}"
            width="0"
            height="{LINE_HEIGHT:.2f}">
            <animate
                attributeName="width"
                from="0"
                to="{width:.2f}"
                dur="0.8s"
                begin="{delay:.2f}s"
                fill="freeze"/>
        </rect>
    </clipPath>
</defs>

<g clip-path="url(#clip{i})">

    <text
        x="0"
        y="{y:.2f}"
        class="ascii"
        fill="#111"
        xml:space="preserve">
        <tspan>{escaped}</tspan>
    </text>

</g>
'''
    )


svg_parts.append("</svg>")

OUTPUT.write_text(
    "".join(svg_parts),
    encoding="utf-8"
)

print("SVG generated successfully!")
print(f"Rows: {rows}")
print(f"Columns: {cols}")
print(f"Size: {width:.0f} x {height:.0f}")
print(f"Saved to: {OUTPUT}")