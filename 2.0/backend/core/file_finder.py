"""
Universal High-Speed Local File & Document Discovery Engine for KernelSense
Features:
- Sub-Millisecond Priority Scanning in Downloads, Desktop, Documents, Notes
- Recursive Multi-Depth (Depth 4) Discovery with Fast Pruning
- Score-Based Filename Ranking (Exact Match First)
- Robust Natural Language Filename Matching (e.g. 'open Java-Notes.pdf file', 'find USS1.pdf')
- In-Memory Path Caching to prevent redundant disk IO
"""

import os
import re
import time
import platform
from typing import List, Dict, Any, Optional

class FileFinderEngine:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.user_home = os.path.expanduser("~")
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Priority scan folders where user documents reside
        self.fast_folders = [
            "d:\\Desktop",
            "d:\\Downloads",
            "d:\\Documents",
            "d:\\Desktop\\NOTES",
            "d:\\Desktop\\KernalSense",
            os.path.join(self.user_home, "Desktop"),
            os.path.join(self.user_home, "Downloads"),
            os.path.join(self.user_home, "Documents"),
            os.path.join(self.user_home, "Pictures")
        ]
        self.valid_fast_folders = [f for f in self.fast_folders if os.path.exists(f)]

    def clean_target(self, query: str) -> str:
        clean = query.strip()
        # Check if query has an explicit file extension: e.g. Java-Notes.pdf, notes.txt
        ext_match = re.search(r'\.(pdf|docx?|pptx?|xlsx?|txt|csv|png|jpe?g|json|log|py|java|cpp|c|html|css|js)\b', clean, re.I)
        if ext_match:
            candidate = clean[:ext_match.end()].strip()
            clean = re.sub(r'^(open|find|search\s+for|search|locate|view|show|read|cat|run)\s+', '', candidate, flags=re.I).strip()
            return clean

        clean = re.sub(r'^(open|find|search\s+for|search|locate|view|show|read|cat|run)\s+', '', clean, flags=re.I).strip()
        clean = re.sub(r'\s+(file|document|doc)$', '', clean, flags=re.I).strip()
        return clean

    def search_files(self, filename_or_query: str, max_results: int = 8, time_limit_sec: float = 0.8) -> List[Dict[str, Any]]:
        """
        Performs ultra-fast breadth-first discovery bounded by a strict hard time limit.
        """
        target = self.clean_target(filename_or_query)
        if not target:
            return []

        target_lower = target.lower()
        if target_lower in self._cache:
            return self._cache[target_lower]

        target_stem = os.path.splitext(target_lower)[0]
        ext_filter = os.path.splitext(target_lower)[1] if '.' in target_lower else None
        tokens = [t for t in re.split(r'[\s._\-]+', target_stem) if len(t) >= 2]

        start_time = time.time()
        results = []
        seen = set()

        # ── 1. Priority Fast Scan across fast folders (recursive up to depth 4) ──
        for folder in self.valid_fast_folders:
            if time.time() - start_time > time_limit_sec or len(results) >= max_results:
                break
            for dirpath, dirnames, filenames in os.walk(folder):
                if time.time() - start_time > time_limit_sec or len(results) >= max_results:
                    break
                rel = os.path.relpath(dirpath, folder)
                if rel != '.' and rel.count(os.sep) >= 4:
                    dirnames.clear()
                    continue
                # Skip build, cache, and hidden directories
                dirnames[:] = [d for d in dirnames if not d.startswith('.') and d.lower() not in [
                    'node_modules', '__pycache__', 'dist', 'build', '.git', '$recycle.bin', 'appdata', 'system volume information'
                ]]
                for f in filenames:
                    f_lower = f.lower()
                    match = False
                    score = 100

                    if f_lower == target_lower:
                        match = True
                        score = 0   # Exact match
                    elif target_lower in f_lower:
                        match = True
                        score = 10
                    elif target_stem and target_stem in f_lower:
                        if ext_filter and f_lower.endswith(ext_filter):
                            match = True
                            score = 15
                        elif not ext_filter:
                            match = True
                            score = 20
                    elif tokens and all(t in f_lower for t in tokens):
                        if ext_filter and f_lower.endswith(ext_filter):
                            match = True
                            score = 25
                        elif not ext_filter:
                            match = True
                            score = 30

                    if match:
                        full = os.path.join(dirpath, f)
                        if full not in seen:
                            seen.add(full)
                            try:
                                st = os.stat(full)
                                size_mb = round(st.st_size / (1024 * 1024), 2)
                                size_human = f"{size_mb} MB" if size_mb >= 0.1 else f"{round(st.st_size / 1024, 1)} KB"
                                mod_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))
                            except Exception:
                                size_human = "N/A"
                                mod_time = "N/A"
                            results.append({
                                "filename": f,
                                "path": full,
                                "extension": os.path.splitext(f)[1].lower(),
                                "size": size_human,
                                "modified": mod_time,
                                "is_dir": False,
                                "score": score
                            })

        # ── 2. Secondary Bounded Scan (if not found in fast folders) ──────────
        if not results:
            secondary_roots = ["d:\\", self.user_home]
            for root in secondary_roots:
                if time.time() - start_time > time_limit_sec or len(results) >= max_results:
                    break
                if not os.path.exists(root):
                    continue
                for dirpath, dirnames, filenames in os.walk(root):
                    if time.time() - start_time > time_limit_sec or len(results) >= max_results:
                        break
                    rel = os.path.relpath(dirpath, root)
                    if rel != '.' and rel.count(os.sep) >= 2:
                        dirnames.clear()
                        continue
                    dirnames[:] = [d for d in dirnames if not d.startswith('.') and d.lower() not in [
                        'node_modules', '$recycle.bin', 'system volume information', 'appdata', 
                        'windows', 'program files', 'program files (x86)', 'site-packages', 
                        '__pycache__', 'dist', 'build', '.git', '.cache'
                    ]]
                    for f in filenames:
                        f_lower = f.lower()
                        match = False
                        score = 100
                        if f_lower == target_lower:
                            match = True
                            score = 0
                        elif target_lower in f_lower:
                            match = True
                            score = 10
                        elif tokens and all(t in f_lower for t in tokens):
                            match = True
                            score = 30
                        if match:
                            full = os.path.join(dirpath, f)
                            if full not in seen:
                                seen.add(full)
                                try:
                                    st = os.stat(full)
                                    size_mb = round(st.st_size / (1024 * 1024), 2)
                                    size_human = f"{size_mb} MB" if size_mb >= 0.1 else f"{round(st.st_size / 1024, 1)} KB"
                                    mod_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))
                                except Exception:
                                    size_human = "N/A"
                                    mod_time = "N/A"
                                results.append({
                                    "filename": f,
                                    "path": full,
                                    "extension": os.path.splitext(f)[1].lower(),
                                    "size": size_human,
                                    "modified": mod_time,
                                    "is_dir": False,
                                    "score": score
                                })

        # Sort by score (exact match first)
        results.sort(key=lambda x: (x["score"], len(x["filename"])))
        for r in results:
            del r["score"]

        final_res = results[:max_results]
        if final_res:
            self._cache[target_lower] = final_res

        return final_res

    def format_open_command(self, file_path: str) -> Dict[str, Any]:
        """
        Formats interactive Ubuntu terminal command to launch the file in its default desktop application.
        """
        norm_path = file_path.replace("/", "\\")
        filename = os.path.basename(norm_path)
        
        ubuntu_cmd = (
            f'wsl.exe -d Ubuntu bash -c "'
            f'echo =================================================; '
            f'echo  KernelSense: Launching Local File: {filename}; '
            f'echo  Path: {norm_path}; '
            f'echo =================================================; '
            f'cmd.exe /c start \\"\\" \\"{norm_path}\\"; exec bash"'
        )
        
        return {
            "command": ubuntu_cmd,
            "filename": filename,
            "path": norm_path,
            "explanation": f"Opens '{filename}' in its default Windows application via interactive Ubuntu terminal."
        }

file_finder = FileFinderEngine()
