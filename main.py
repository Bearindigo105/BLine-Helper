import json
import pathlib
import watchdog.observers
import linker
import handler
import time
import re


def get_key(file):
    m = re.match(r'(.+?)(\d+)$', file.stem)
    return m.group(1) if m else file.stem


def main():
    routines = {}

    with open("config.json", "r") as f:
        config = json.load(f)
        project_dir = pathlib.Path(config["project_dir"]) / "src/main/deploy/autos/paths"

    for file in project_dir.glob("*.json"):
        key = get_key(file)

        if key not in routines:
            routines[key] = []

        routines[key].append(file)

    linker.fix_routines(routines)

    event_handler = handler.Handler(routines)
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, project_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("quitting...")

    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()