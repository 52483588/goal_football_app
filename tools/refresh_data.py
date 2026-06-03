r"""
refresh_data.py - One-click refresh: XML -> his_data.js + index.html
Run at repo root (C:\Users\52483\Desktop\xml)
"""
import os, sys, subprocess, time

PYTHON = sys.executable
WORK_DIR = r"C:\Users\52483\Desktop\xml"
DATA_SRC = os.path.join(WORK_DIR, "HisData")

def run_step(script_name, desc):
    script_path = os.path.join(WORK_DIR, "tools", script_name)
    print("\n" + "=" * 50)
    print("[Step] " + desc)
    print("=" * 50)
    if not os.path.exists(script_path):
        print("[FAIL] Script not found: " + script_path)
        return False
    t0 = time.time()
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run([PYTHON, script_path], cwd=WORK_DIR,
                          capture_output=True, text=True, encoding='utf-8', env=env)
    print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    elapsed = time.time() - t0
    if result.returncode != 0:
        print("[FAIL] %s failed (%.1fs)" % (script_name, elapsed))
        return False
    print("[OK] %s done (%.1fs)" % (script_name, elapsed))
    return True

def main():
    print("=" * 50)
    print("  Data Refresh Tool")
    print("  Source: %s" % DATA_SRC)
    print("=" * 50)

    if not os.path.isdir(DATA_SRC):
        print("[FAIL] Data source not found: %s" % DATA_SRC)
        return

    t_start = time.time()

    # Step 1: Parse XML
    if not run_step("parse_xml.py", "Parse XML -> his_data.js"):
        print("\n[WARN] Step 1 failed, aborting.")
        return

    # Step 2: Build HTML
    if not run_step("build_html.py", "Generate index.html"):
        print("\n[WARN] Step 2 failed. JSON data may have issues.")

    # Summary
    elapsed = time.time() - t_start
    docs_dir = os.path.join(WORK_DIR, "docs")
    files = []
    for fn in ["his_data.js", "index.html"]:
        fp = os.path.join(docs_dir, fn)
        if os.path.exists(fp):
            size_kb = os.path.getsize(fp) / 1024
            files.append("  %s (%.0f KB)" % (fn, size_kb))

    print("\n" + "=" * 50)
    print("[DONE] All complete! Total %.1fs" % elapsed)
    print("Output in docs/:")
    for f in files:
        print(f)

if __name__ == '__main__':
    main()
