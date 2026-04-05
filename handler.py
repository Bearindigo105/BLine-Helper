import pathlib
import time
import watchdog.events
import linker
import threading
import re

class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self, routines):
        self.routines = routines
        watchdog.events.PatternMatchingEventHandler.__init__(
            self, patterns=["*.json"], ignore_directories=True, case_sensitive=False
        )
        self._lock = threading.Lock()
        self._pending = False
        self.modify_flag = False
        
    def _schedule_fix(self):
        with self._lock:
            if not self._pending:
                self._pending = True
                threading.Timer(0.1, self._run_fix).start()

    def _run_fix(self):
        with self._lock:
            self._pending = False
        try:
            import linker
            linker.fix_routines(self.routines)
            print("routines fixed")
        except Exception as e:
            print("Error fixing routines:", e)
        
        time.sleep(0.1)
        self.modify_flag = False
        

    def on_created(self, event):
        file = pathlib.Path(event.src_path)
        key = self.get_key(file)

        if key not in self.routines:
            self.routines[key] = []

        if file not in self.routines[key]:
            self.routines[key].append(file)

        self._schedule_fix()
        
        print("created", file.name)
        
    def on_deleted(self, event):
        file = pathlib.Path(event.src_path)
        key = self.get_key(file)

        if key in self.routines:
            self.routines[key] = [p for p in self.routines[key] if p != file]

            def get_index(p):
                import re
                m = re.search(r'(\d+)$', p.stem)
                return int(m.group(1)) if m else 0

            self.routines[key].sort(key=get_index)

            new_paths = []
            for i, p in enumerate(self.routines[key], start=1):
                new_name = f"{key}{i}.json"
                new_path = p.with_name(new_name)

                if p != new_path:
                    p.rename(new_path)

                new_paths.append(new_path)

            self.routines[key] = new_paths

            self._schedule_fix()
            
            print("removed", file.name)
            

    def on_modified(self, event):
        if self.modify_flag:
            return
        
        self.modify_flag = True
        
        file = pathlib.Path(event.src_path)
        key = self.get_key(file)
        
        if key not in self.routines:
            return

        if file not in self.routines[key]:
            self.routines[key].append(file)

        self._schedule_fix()
        
        print("modified", file.name)
            
    def get_key(self, file):
        m = re.match(r'(.+?)(\d+)$', file.stem)
        return m.group(1) if m else file.stem
