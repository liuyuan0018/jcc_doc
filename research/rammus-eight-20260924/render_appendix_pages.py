#!/usr/bin/env python3
"""Render the audited static Rammus score pages in the reference layout."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = ROOT / "exports/frontline-rammus-eight-v1/source/assets/rammus-appendix-results.json"
OUT = ROOT / "exports/frontline-rammus-eight-v1/production-v1/appendix-pages"
ICONS = ROOT / "assets/ranking"
HERO = ROOT / "../.." / "project/game/projects/jcc/client/Assets/Res/GUI/Image/HeadIcon/rammus.png"

ICON_BY_NAME = {
    "饮血剑": "2006.png", "大天使之杖": "2017.png", "适应性头盔": "adaptivehelm.png",
    "冕卫": "crownguard.png", "泰坦的坚决": "2052.png",
    "灭世者的死亡之帽": "2016.png", "振奋盔甲": "spiritvisage.png",
    "正义之手": "2039.png", "蓝霸符": "2222.png", "石像鬼石板甲": "2248.png",
    "圣盾使的誓约": "2023.png", "巨龙之爪": "2031.png", "虚空之杖": "voidstaff.png",
}
SHORT = {
    "饮血剑": "饮血", "大天使之杖": "大天使", "适应性头盔": "头盔",
    "冕卫": "冕卫", "泰坦的坚决": "泰坦", "灭世者的死亡之帽": "帽子",
    "振奋盔甲": "振奋", "正义之手": "正义", "蓝霸符": "蓝霸符",
    "石像鬼石板甲": "板甲", "圣盾使的誓约": "冰甲",
    "巨龙之爪": "龙牙", "虚空之杖": "虚空杖",
}
PURPLE = "#7047ff"
INK = "#160b46"
MUTED = "#68549b"
YELLOW = "#fff12d"


def font(size, number=False):
    path = ("/System/Library/Fonts/Supplemental/Arial Narrow Bold Italic.ttf" if number
            else "/System/Library/Fonts/Hiragino Sans GB.ttc")
    return ImageFont.truetype(path, size, index=0 if number else 2)


def render(all_rows, page, output):
    page_sizes = [8] * 6 + [5, 5] if len(all_rows) == 58 else [8] * (len(all_rows) // 8) + ([len(all_rows) % 8] if len(all_rows) % 8 else [])
    page_count = len(page_sizes)
    assert 1 <= page <= page_count
    first_index = sum(page_sizes[:page-1])
    rows = all_rows[first_index:first_index+page_sizes[page-1]]
    assert rows
    image = Image.new("RGB", (1080, 1920))
    draw = ImageDraw.Draw(image)
    for y in range(1920):
        t = y / 1920
        draw.line((0, y, 1080, y), fill=(int(247-10*t), int(245-9*t), int(255-5*t)))

    def txt(x, y, label, size=30, color=INK, anchor=None, number=False):
        draw.text((x, y), str(label), font=font(size, number), fill=color, anchor=anchor)

    def box(rect, color, radius=10, edge=None, width=1):
        draw.rounded_rectangle(rect, radius, fill=color, outline=edge, width=width)

    draw.polygon([(38, 65), (63, 65), (41, 175), (16, 175)], fill=PURPLE)
    hero = Image.open(HERO).convert("RGB").resize((138, 138), Image.Resampling.LANCZOS)
    image.paste(hero, (75, 62))
    draw.rectangle((74, 61, 214, 201), outline=PURPLE, width=3)
    txt(240, 55, "龙龟，怎么配更能扛？", 52)
    txt(242, 128, "三星 · 6护卫 · 无指定海克斯", 32, MUTED)
    txt(242, 176, f"同条件高分配装 {len(all_rows)} 套", 25, MUTED)
    draw.line((36, 240, 1044, 240), fill="#d6cff0", width=2)
    txt(43, 267, "配装组合", 27, MUTED)
    txt(1031, 267, "最高通过来伤 / 秒", 26, MUTED, "rt")
    if page > 1 and rows[0]["rank"] == all_rows[first_index-1]["rank"]:
        txt(215, 269, f"续：并列 {rows[0]['rank']}", 23, MUTED)

    episode_ids = {b["id"]: b["key"] for b in
                   json.loads((HERE / "source-verification.json").read_text())["builds"]}
    for i, row in enumerate(rows):
        y = 322 + i * 143
        top = row["passedDps"] == all_rows[0]["passedDps"]
        if top:
            glow = Image.new("RGBA", image.size)
            gd = ImageDraw.Draw(glow)
            gd.rounded_rectangle((31, y-3, 1049, y+133), 14, outline="#fadd38", width=8)
            alpha = glow.getchannel("A").filter(ImageFilter.GaussianBlur(9))
            glow = Image.new("RGBA", image.size, "#ffdf36")
            glow.putalpha(alpha)
            image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
            draw = ImageDraw.Draw(image)
        box((36, y, 1044, y+130), "#fffef5" if top else "#fcfbff", 12,
            "#f4d72d" if top else "#d9d1ed", 3 if top else 2)
        marker = episode_ids.get(row["id"])
        if top:
            box((48, y+9, 188, y+36), YELLOW, 4)
            txt(118, y+21, "并列最高", 19, INK, "mm")
            if marker:
                txt(207, y+12, f"本期 {marker}", 20, MUTED)
        else:
            txt(57, y+12, f"并列 {row['rank']}", 20, MUTED)
            if marker:
                txt(180, y+12, f"本期 {marker}", 20, MUTED)
        for j, name in enumerate(row["itemNames"]):
            x = 58 + j * 191
            icon_file = ICONS / ICON_BY_NAME[name]
            assert icon_file.exists(), icon_file
            icon = Image.open(icon_file).convert("RGB").resize((60, 60), Image.Resampling.LANCZOS)
            image.paste(icon, (x, y+47))
            draw.rectangle((x-1, y+46, x+60, y+107), outline="#281652", width=2)
            short = SHORT[name]
            assert font(25).getlength(short) <= 104, (name, short)
            txt(x+70, y+77, short, 25, INK, "lm")
            if j < 2:
                txt(x+174, y+78, "+", 23, MUTED, "mm")
        bx, by, bar_width = 641, y+57, 249
        draw.rectangle((bx, by, bx+bar_width, by+40), fill="#e3def1")
        fill_width = round(bar_width * row["passedDps"] / 1900)
        for xx in range(fill_width):
            color = ((255, 232 + int(17*xx/max(1, fill_width)), 44) if top else
                     (112 + int(20*xx/max(1, fill_width)), 65 + int(27*xx/max(1, fill_width)), 255))
            draw.line((bx+xx, by, bx+xx, by+40), fill=color)
        txt(1021, y+76, row["passedDps"], 58, INK, "rm", True)

    box((36, 1515, 1044, 1749), "#f8f6ff", 12, "#d9d1ed", 2)
    draw.polygon([(55,1540),(78,1540),(65,1586),(42,1586)], fill=PURPLE)
    txt(91,1535,"统一条件",34)
    conditions = [("三星龙龟 · 6护卫", "无指定海克斯"),
                  ("5人集火 / 33%重伤", "双抗各降30%"),
                  ("物理魔法各半", "无控制"),
                  ("每档满血重开30秒", "来伤每档增加50")]
    for j, (a, b) in enumerate(conditions):
        cx = 163 + j*250
        txt(cx,1620,a,22,MUTED,"mm")
        txt(cx,1663,b,22,MUTED,"mm")
        if j < 3:
            draw.line((288+j*250,1603,288+j*250,1686),fill="#b6a7e6",width=2)
    draw.line((52,1708,1028,1708), fill="#c7b9ee", width=2)
    txt(57,1728,"固定条件模拟 · 同档并列 · 非实机对战",21,MUTED,"lm")
    txt(43,1800,f"{page:02d} / {page_count:02d}",36,INK,number=True)
    start = first_index+1
    end = start + len(rows)-1
    txt(1035,1800,f"暂停查看   ·   条目 {start}—{end} / {len(all_rows)}",27,MUTED,"rt")
    txt(43,1860,"按最高连续通过档排序 · 同档顺序不分高低",22,"#9283af")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", default="1,2,8", help="Comma-separated page numbers, or all")
    args = parser.parse_args()
    data = json.loads(DATA.read_text())
    assert data["verified"] and data["selectedCount"] == len(data["rows"])
    pages = (range(1, (8 if len(data["rows"]) == 58 else (len(data["rows"])+7)//8)+1) if args.pages == "all" else
             [int(x) for x in args.pages.split(",")])
    for page in pages:
        output = OUT / f"page-{page:02d}.png"
        print(render(data["rows"], page, output))


if __name__ == "__main__":
    main()
