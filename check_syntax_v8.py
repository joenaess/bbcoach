import py_compile

files = ["app.py", "src/bbcoach/data/scrapers.py", "src/bbcoach/data/storage.py"]

for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"Syntax OK: {f}")
    except py_compile.PyCompileError as e:
        print(f"Syntax Error in {f}: {e}")
