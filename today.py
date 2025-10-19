import datetime
from dateutil import relativedelta
import requests
import os
import shutil
from pathlib import Path
from lxml import etree

HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']


def simple_request(func_name, query, variables):
    request = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS,
    )
    if request.status_code == 200:
        return request
    raise Exception(func_name + ' failed', request.status_code, request.text)


def follower_getter(username):
    query = '''
    query($login: String!){
        user(login: $login) {
            followers { totalCount }
        }
    }'''
    request = simple_request(follower_getter.__name__, query, {'login': username})
    return int(request.json()['data']['user']['followers']['totalCount'])


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data, contrib_data, follower_data, loc_data):
    filename = ensure_svg_file(filename)
    tree = etree.parse(filename)
    root = tree.getroot()
    # Align uptime with dot padding to push the value to the right
    justify_format(root, 'age_data', age_data, 22)
    justify_format(root, 'follower_data', follower_data, 10)
    justify_format(root, 'commit_data', commit_data, 22)
    justify_format(root, 'star_data', star_data, 14)
    justify_format(root, 'repo_data', repo_data, 6)
    justify_format(root, 'contrib_data', contrib_data)
    justify_format(root, 'loc_data', loc_data[2], 9)
    justify_format(root, 'loc_add', loc_data[0])
    justify_format(root, 'loc_del', loc_data[1], 7)
    # Inject custom profile fields and ASCII art (non-destructive: adds nodes if missing)
    apply_customizations(root, filename)
    tree.write(filename, encoding='utf-8', xml_declaration=True)


def justify_format(root, element_id, new_text, length=0):
    if isinstance(new_text, int):
        new_text = f"{'{:,}'.format(new_text)}"
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    just_len = max(0, length - len(new_text))
    if just_len <= 2:
        dot_map = {0: '', 1: ' ', 2: '. '}
        dot_string = dot_map[just_len]
    else:
        dot_string = ' ' + ('.' * just_len) + ' '
    find_and_replace(root, f"{element_id}_dots", dot_string)


def find_and_replace(root, element_id, new_text):
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text


def ensure_svg_file(filename: str) -> str:
    """
    Ensure the target SVG exists at repo root. If missing, copy from reference/<name>.
    Returns the absolute or relative path to the ensured file.
    """
    target = Path(filename)
    if target.exists():
        return str(target)
    ref = Path('reference') / target.name
    if ref.exists():
        try:
            shutil.copyfile(ref, target)
            return str(target)
        except Exception:
            # Fall back to reading directly from reference
            return str(ref)
    raise FileNotFoundError(f"SVG template not found: {filename} (also looked for {ref})")


def apply_customizations(root, filename):
    """
    Adds/updates custom profile fields and injects 25-line ASCII art.
    This function only adds nodes if they don't already exist, so it won't
    disturb existing layout. Coordinates are chosen to match the right column
    area near the existing metrics and the left ASCII block area seen in refs.
    """
    theme = 'dark' if 'dark' in filename.lower() else 'light'
    ascii_lines = load_ascii_lines()
    strip_template_content(root)
    inject_ascii(root, ascii_lines, theme)
    inject_profile_fields(root)


def load_ascii_lines():
    ascii_path_candidates = [
        '25charascii',  # preferred new file with exactly 25 lines
        'ascii',        # fallback
    ]
    lines = []
    for p in ascii_path_candidates:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.read().splitlines()
                break
            except Exception:
                continue
    # Normalize to exactly 25 lines
    target = 25
    if not lines:
        lines = [''] * target
    if len(lines) < target:
        lines = lines + [''] * (target - len(lines))
    elif len(lines) > target:
        lines = lines[:target]
    return lines


def inject_ascii(root, lines, theme):
    from lxml import etree as _et
    try:
        # Remove previous ASCII block if present to avoid duplication
        prev = root.find(".//*[@id='ascii_block']")
        if prev is not None and prev.getparent() is not None:
            prev.getparent().remove(prev)

        # Create a group to contain all ASCII lines (monospace for alignment)
        g = _et.SubElement(root, 'g', id='ascii_block')
        fill = '#c9d1d9' if theme == 'dark' else '#24292f'
        x_start = '15'
        y_base = 30  # matches refs
        line_height = 12
        for idx, line in enumerate(lines):
            y_val = str(y_base + idx * line_height)
            _et.SubElement(
                g,
                'text',
                {
                    'x': x_start,
                    'y': y_val,
                    'fill': fill,
                    'font-family': 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                    'font-size': '10px',
                    'class': 'ascii',
                },
            ).text = line
    except Exception:
        # Fallback: if any issue arises, remove partial block and skip ASCII injection
        if 'g' in locals() and g is not None and g.getparent() is not None:
            g.getparent().remove(g)
        return


def inject_profile_fields(root):
    from lxml import etree as _et

    # Desired content from user's request
    fields = [
        ('name_data',               'Name: Hashim'),
        ('os_data',                 'OS: Windows 10 (WSL), iOS and macOS'),
        ('host_data',               'Host: WilliamHill'),
        ('kernel_data',             'Kernel: Service Operations Analyst'),
        ('ide_data',                'IDE: VSCode/Cursor'),
        ('prog_langs_data',         'Programming: Python, JavaScript, C#'),
        ('languages_comp_data',     'Languages.computer: Python, JavaScript, C#'),
        ('languages_real_data',     'Languages.real: English, Urdu, Punjabi'),
        ('hobbies_software_data',   'Hobbies.software: building websites and apps'),
        ('hobbies_real_data',       'Hobbies.real: hiking, cooking, weightlifting'),
        ('email_personal_data',     'Email.personal: Hashim.rafiq332@gmail.com'),
        ('linkedin_data',           'LinkedIn: Hashim Rafiq'),
        ('portfolio_data',          'Portfolio: rafiq.codes'),
    ]

    # Remove existing profile block to prevent duplication
    prev = root.find(".//*[@id='profile_block']")
    if prev is not None and prev.getparent() is not None:
        prev.getparent().remove(prev)

    # Right column positioning below Uptime; tune as necessary to fit
    g = _et.SubElement(root, 'g', id='profile_block')
    x_right = 390
    y_start = 90
    line_height = 18
    for idx, (elem_id, text_value) in enumerate(fields):
        y_val = str(y_start + idx * line_height)
        # Create <text> with a single <tspan> carrying the id for easy updates later
        text_node = _et.SubElement(g, 'text', {
            'x': str(x_right),
            'y': y_val,
            'class': 'value',
        })
        tspan = _et.SubElement(text_node, 'tspan', {'id': elem_id})
        tspan.text = text_value


def strip_template_content(root):
    """Remove existing ASCII nodes and template right-column content without IDs."""
    # Remove nodes with class="ascii"
    for node in list(root.findall(".//*[@class='ascii']")):
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)

    # Keep metric ids we still manage
    allowed_ids = {
        'age_data', 'age_data_dots',
        'repo_data', 'repo_data_dots', 'contrib_data',
        'star_data', 'star_data_dots',
        'commit_data', 'commit_data_dots',
        'follower_data', 'follower_data_dots',
        'loc_data', 'loc_data_dots', 'loc_add', 'loc_del', 'loc_del_dots'
    }

    def should_remove(elem):
        elem_id = elem.get('id')
        if elem_id and elem_id in allowed_ids:
            return False
        cls = (elem.get('class') or '').strip()
        if cls in ('key', 'value', 'cc'):
            return True
        # Remove right-column items (x >= 380) that lack ids
        x_attr = elem.get('x')
        try:
            if x_attr is not None and float(x_attr) >= 380:
                return True
        except Exception:
            pass
        # Heuristic: remove text containing template labels
        content = ''.join(elem.itertext()).strip().lower()
        keywords = [
            'os:', 'uptime:', 'host:', 'kernel:', 'ide:',
            'languages', 'hobbies', 'contact', 'linkedin', 'discord', 'portfolio',
            'andrew', 'grant', 'ttm', 'idea'
        ]
        if any(k in content for k in keywords):
            return True
        return False

    # First remove entire right-column text nodes that don't carry our metric ids
    for text_elem in list(root.findall('.//text')):
        # If any descendant has an allowed id, keep the whole block
        has_allowed = any(
            (child.get('id') in allowed_ids)
            for child in text_elem.findall('.//tspan')
        )
        x_attr = text_elem.get('x')
        x_val = None
        try:
            if x_attr is not None:
                x_val = float(x_attr)
        except Exception:
            x_val = None

        if (x_val is not None and x_val >= 380) and not has_allowed:
            parent = text_elem.getparent()
            if parent is not None:
                parent.remove(text_elem)

    # Then remove leftover tspans that are styling-only or template labels
    for tspan in list(root.findall('.//tspan')):
        if tspan.get('id') in allowed_ids:
            continue
        if (tspan.get('class') or '').strip() in ('key', 'value', 'cc'):
            parent = tspan.getparent()
            if parent is not None:
                parent.remove(tspan)
            continue
        if should_remove(tspan):
            parent = tspan.getparent()
            if parent is not None:
                parent.remove(tspan)


if __name__ == '__main__':
    # Fetch followers
    follower_data = follower_getter(USER_NAME)

    # Compute age from env BIRTHDAY=YYYY-MM-DD (default: 2000-01-01)
    birthday_str = os.environ.get('BIRTHDAY', '2001-08-24')
    try:
        year, month, day = [int(x) for x in birthday_str.split('-')]
        diff = relativedelta.relativedelta(datetime.datetime.today(), datetime.datetime(year, month, day))
        age_data = '{} {}, {} {}, {} {}{}'.format(
            diff.years, 'year' + ('s' if diff.years != 1 else ''),
            diff.months, 'month' + ('s' if diff.months != 1 else ''),
            diff.days, 'day' + ('s' if diff.days != 1 else ''),
            ' 🎂' if (diff.months == 0 and diff.days == 0) else ''
        )
    except Exception:
        age_data = ''

    # Other metrics off for now
    commit_data = 0
    star_data = 0
    repo_data = 0
    contrib_data = 0
    total_loc = [0, 0, 0]

    generate_mode = os.environ.get('GENERATE_SVG', '0') == '1'
    if generate_mode:
        from lxml import etree as _et

        def build_svg(theme: str):
            width = 900
            height = 540
            bg = '#0d1117' if theme == 'dark' else '#ffffff'
            fg = '#c9d1d9' if theme == 'dark' else '#24292f'
            svg = _et.Element('svg', xmlns="http://www.w3.org/2000/svg", version="1.1", width=str(width), height=str(height))
            _et.SubElement(svg, 'rect', x='0', y='0', width=str(width), height=str(height), rx='8', fill=bg)
            # Title bar
            _et.SubElement(svg, 'text', x='20', y='24', fill=fg, **{'font-size': '14px', 'font-family': 'Segoe UI, Ubuntu, Sans-Serif'}).text = USER_NAME
            # Left: ASCII
            inject_ascii(svg, load_ascii_lines(), theme)
            # Right: metrics block header
            _et.SubElement(svg, 'text', x='380', y='30', fill=fg, **{'font-size': '12px', 'font-family': 'Segoe UI, Ubuntu, Sans-Serif'}).text = '— Profile —'
            # Insert metric ids in a minimal way to keep workflow compatibility
            justify_format(svg, 'age_data', age_data, 22)
            justify_format(svg, 'follower_data', follower_data, 10)
            justify_format(svg, 'commit_data', commit_data, 22)
            justify_format(svg, 'star_data', star_data, 14)
            justify_format(svg, 'repo_data', repo_data, 6)
            justify_format(svg, 'contrib_data', contrib_data)
            justify_format(svg, 'loc_data', total_loc[2], 9)
            justify_format(svg, 'loc_add', total_loc[0])
            justify_format(svg, 'loc_del', total_loc[1], 7)
            # Add custom profile fields
            inject_profile_fields(svg)
            return _et.ElementTree(svg)

        build_svg('dark').write('dark_mode.svg', encoding='utf-8', xml_declaration=True)
        build_svg('light').write('light_mode.svg', encoding='utf-8', xml_declaration=True)
    else:
        svg_overwrite('dark_mode.svg', age_data, commit_data, star_data, repo_data, contrib_data, follower_data, total_loc)
        svg_overwrite('light_mode.svg', age_data, commit_data, star_data, repo_data, contrib_data, follower_data, total_loc)