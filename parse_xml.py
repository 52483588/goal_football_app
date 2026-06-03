"""
parse_xml.py - Parse XML files from HisData/ and output his_data.js
Output: docs/his_data.js  (var RAW_DATA = {...})
"""
import os, re, json, time

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))   # 脚本所在目录（仓库根目录）
DATA_SRC = os.path.join(REPO_ROOT, "HisData")
OUTPUT_DIR = os.path.join(REPO_ROOT, "docs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "his_data.js")

OC_ATTRS = ['id','gt','st','sh','sa']
NG_ATTRS = ['id','h1','h2','h3','h4','h5','h6','a1','a2','a3','a4','a5','a6']
OU_ATTRS = ['id','oo','uo','li','hi_var']

def parse_fixtures(filepath, attrs):
    """Extract specified attributes from all <Fixture> tags in an XML file."""
    result = {}
    if not os.path.exists(filepath):
        return result
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.finditer(r'<Fixture\s+([^/]*/?)>', content):
        tag = m.group(1)
        id_m = re.search(r'\bid="([^"]+)"', tag)
        if not id_m:
            continue
        fid = id_m.group(1)
        row = {}
        for attr in attrs:
            am = re.search(r'\b' + attr + r'="([^"]*)"', tag)
            row[attr] = am.group(1) if am else ''
        result[fid] = row
    return result

def main():
    t0 = time.time()
    if not os.path.isdir(DATA_SRC):
        print("[FAIL] Data source not found: %s" % DATA_SRC)
        return

    folders = sorted([
        f for f in os.listdir(DATA_SRC)
        if os.path.isdir(os.path.join(DATA_SRC, f)) and re.match(r'\d{8}_\d{6}', f)
    ])

    if not folders:
        print("[FAIL] No timestamp folders found in %s" % DATA_SRC)
        return

    print("Found %d timestamp folders" % len(folders))

    raw_data = {}
    id_set = set()

    for folder in folders:
        fp = os.path.join(DATA_SRC, folder)
        raw_data[folder] = {}

        oc = parse_fixtures(os.path.join(fp, 'odds_config.xml'), OC_ATTRS)
        ng = parse_fixtures(os.path.join(fp, 'numberofgoals.xml'), NG_ATTRS)
        ou = parse_fixtures(os.path.join(fp, 'overunder.xml'), OU_ATTRS)

        all_ids = set(oc.keys()) | set(ng.keys()) | set(ou.keys())
        id_set.update(all_ids)

        for fid in all_ids:
            raw_data[folder][fid] = {
                'oc': oc.get(fid, {}),
                'ng': ng.get(fid, {}),
                'ou': ou.get(fid, {})
            }

    # Build index: { id => latest non-empty values }
    idx = {}
    for folder in reversed(folders):
        for fid, rec in raw_data[folder].items():
            if fid not in idx:
                idx[fid] = {'oc': {}, 'ng': {}, 'ou': {}}
            for key in ('oc','ng','ou'):
                if rec[key] and not idx[fid][key]:
                    idx[fid][key] = dict(rec[key])

    # Write JS file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('var RAW_DATA = ')
        json.dump(raw_data, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
        f.write('var FOLDERS = ')
        json.dump(folders, f, ensure_ascii=False)
        f.write(';\n')
        f.write('var ID_INDEX = ')
        json.dump(idx, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    elapsed = time.time() - t0
    print("[OK] %s (%d folders, %d unique IDs)" % (OUTPUT_FILE, len(folders), len(id_set)))
    print("[OK] his_data.js: %.0f KB (%.1fs)" % (size_kb, elapsed))

if __name__ == '__main__':
    main()