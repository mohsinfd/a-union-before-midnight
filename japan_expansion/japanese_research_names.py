"""Authentic Japanese names for the ten added research entries.

ASCII romanisation avoids glyph corruption in Darkest Hour's Western font.
Research specialties remain a game abstraction; names are actual institutions.
"""
NAMES = {
    286010: ('Kaigun Daigakko', 1938),
    286011: ('Kaijo Goei Soshireibu', 1943),
    286012: ('Shanhai Kaigun Tokubetsu Rikusentai', 1937),
    286013: ('Rikugun Jidosha Gakko', 1937),
    286014: ('Rikugun Koku Gijutsu Kenkyujo', 1940),
    286015: ('Kaigun Gijutsu Kenkyujo', 1941),
    286016: ('Chiba Rikugun Sensha Gakko', 1942),
    286017: ('Gunjusho', 1943),
    286018: ('Rikugun Hohei Gakko', 1933),
    286019: ('Rikugun Heiki Gyosei Honbu', 1943),
}


def apply(target, read, write):
    path = target / 'db/tech/teams/teams_jap.csv'
    rows, found = [], set()
    for line in read(path).splitlines():
        cells = line.split(';')
        if cells[0].isdigit() and int(cells[0]) in NAMES:
            tid = int(cells[0])
            assert tid not in found, ('Duplicate added research team', tid)
            cells[1], start = NAMES[tid]
            cells[4] = str(start)
            line = ';'.join(cells)
            found.add(tid)
        rows.append(line)
    assert found == set(NAMES), ('Missing research teams', set(NAMES) - found)
    write(path, '\n'.join(rows) + '\n')
