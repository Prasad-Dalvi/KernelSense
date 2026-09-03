"""
Dynamic Command Knowledge & Manual Engine for KernelSense
Synthesizes comprehensive CLI manuals, argument breakdowns, risk analyses, and executable recipes.
Works dynamically for any Linux / Windows system command.
"""

import os
import re
import subprocess
from typing import Dict, Any, List, Optional
from ubuntu.bridge import ubuntu_bridge

# ─────────────────────────────────────────────────────────────────────────────
# Built-in High-Utility Command Knowledge Base (Curated Best-Practice Manuals)
# ─────────────────────────────────────────────────────────────────────────────
CORE_MANUALS = {
    "htop": {
        "title": "htop — Interactive Linux Process Viewer & System Monitor",
        "description": "An interactive, real-time process viewer and system monitor for Unix-like systems. An advanced alternative to classic `top` with color-coded CPU core meters, memory/swap graphs, process tree navigation, and interactive kill signals.",
        "syntax": "htop [options]",
        "risk_level": "LOW",
        "flags": [
            ("-d, --delay=DELAY", "Update interval in tenths of a second (e.g., -d 10 for 1 sec)"),
            ("-u, --user=USERNAME", "Filter and show only processes owned by the given user"),
            ("-p, --pid=PID,PID...", "Monitor only specified process IDs"),
            ("-s, --sort-key=COLUMN", "Sort by column name (e.g., PERCENT_CPU, PERCENT_MEM, TIME)"),
            ("-t, --tree", "Display processes in hierarchical parent-child process tree format")
        ],
        "examples": [
            ("htop", "Launch the full interactive color process monitor"),
            ("htop -s PERCENT_MEM", "Launch htop sorted immediately by memory utilization"),
            ("htop -u root", "Monitor only system and root daemon processes"),
            ("htop -t", "Inspect process hierarchy in tree view")
        ],
        "default_command": "wsl.exe -d Ubuntu bash -c \"htop; exec bash\"",
        "command_explanation": "Spawns interactive htop process monitor inside the desktop Ubuntu terminal."
    },
    "chmod": {
        "title": "chmod — Change File Access Permissions and Modes",
        "description": "Controls read (`r=4`), write (`w=2`), and execute (`x=1`) access permissions for files and directories across Owner (`u`), Group (`g`), and Others (`o`).",
        "syntax": "chmod [OPTION]... MODE[,MODE]... FILE...",
        "risk_level": "MEDIUM",
        "flags": [
            ("-R, --recursive", "Change files and directories recursively across subtrees"),
            ("-v, --verbose", "Output a diagnostic message for every file processed"),
            ("-c, --changes", "Like verbose, but report only when a permission change is made"),
            ("--reference=RFILE", "Use RFILE's permissions instead of specifying MODE values")
        ],
        "examples": [
            ("chmod +x script.sh", "Make a script executable for all users"),
            ("chmod 755 /var/www/html", "Standard web directory permissions (rwxr-xr-x)"),
            ("chmod 600 ~/.ssh/id_rsa", "Secure private key file so only the owner can read/write it"),
            ("chmod -R 750 /opt/app", "Grant full access to owner, read/exec to group, none to others")
        ],
        "default_command": "ls -ld . && echo 'Current directory permissions shown above.'",
        "command_explanation": "Inspects current directory permission bits before applying chmod changes."
    },
    "grep": {
        "title": "grep — Global Regular Expression Print & Search Tool",
        "description": "Searches input files or standard input streams for lines matching regular expressions and prints matching results with highlighting and line numbers.",
        "syntax": "grep [OPTIONS] PATTERN [FILE...]",
        "risk_level": "LOW",
        "flags": [
            ("-i, --ignore-case", "Perform case-insensitive matching"),
            ("-r, -R, --recursive", "Recursively search all files under directory tree"),
            ("-n, --line-number", "Prefix each line of output with its 1-based line number"),
            ("-v, --invert-match", "Select non-matching lines (exclude matches)"),
            ("-c, --count", "Suppress normal output and print only count of matching lines"),
            ("-E, --extended-regexp", "Interpret PATTERN as extended regular expression (ERE)"),
            ("-l, --files-with-matches", "Print only names of files with matching lines")
        ],
        "examples": [
            ("grep -rn 'ERROR' /var/log/", "Recursively search for 'ERROR' in log directories with line numbers"),
            ("grep -i 'failed' /var/log/auth.log", "Case-insensitive search for failed logins"),
            ("ps aux | grep nginx", "Find active Nginx master and worker PIDs"),
            ("grep -v '^#' /etc/nginx/nginx.conf", "Display configuration file omitting comments")
        ],
        "default_command": "grep -rn 'error' /var/log/ 2>/dev/null | head -n 10",
        "command_explanation": "Searches recent system logs for error entries."
    },
    "tar": {
        "title": "tar — Tape Archive Packing & Compression Utility",
        "description": "Archives multiple files and directories into a single `.tar` archive file, optionally compressing with gzip (`-z`), bzip2 (`-j`), or xz (`-J`).",
        "syntax": "tar [OPTIONS] [ARCHIVE_NAME] [FILES...]",
        "risk_level": "LOW",
        "flags": [
            ("-c, --create", "Create a new tar archive"),
            ("-x, --extract", "Extract files from an existing archive"),
            ("-v, --verbose", "Verbosely list files being processed"),
            ("-f, --file=ARCHIVE", "Specify the archive filename"),
            ("-z, --gzip", "Filter the archive through gzip (.tar.gz / .tgz)"),
            ("-j, --bzip2", "Filter the archive through bzip2 (.tar.bz2)"),
            ("-C, --directory=DIR", "Change to target directory before performing operation")
        ],
        "examples": [
            ("tar -czvf backup.tar.gz /home/user/data", "Compress directory into a gzip archive"),
            ("tar -xzvf archive.tar.gz -C /opt/", "Extract gzip archive into /opt/ directory"),
            ("tar -tvf archive.tar.gz", "List table of contents inside archive without extracting")
        ],
        "default_command": "tar --version | head -n 1",
        "command_explanation": "Checks tar version and supported compression algorithms."
    },
    "systemctl": {
        "title": "systemctl — Systemd Service & Unit Management Control",
        "description": "Primary CLI utility to inspect and control the systemd system and service manager, controlling service states, daemons, targets, sockets, and timers.",
        "syntax": "systemctl [COMMAND] [NAME...]",
        "risk_level": "MEDIUM",
        "flags": [
            ("status [UNIT]", "Show runtime status, PID, memory, and recent log journal entries for unit"),
            ("start / stop [UNIT]", "Activate or deactivate a systemd service immediately"),
            ("restart / reload [UNIT]", "Restart daemon or reload configuration without dropping connections"),
            ("enable / disable [UNIT]", "Enable or disable service auto-start at system boot"),
            ("list-units --type=service", "List all currently loaded active services on system")
        ],
        "examples": [
            ("systemctl status nginx", "Check active health, memory, and uptime of nginx"),
            ("systemctl list-units --failed", "Find any broken or crashed systemd services"),
            ("systemctl restart networking", "Restart network management daemon")
        ],
        "default_command": "systemctl list-units --type=service --state=running | head -n 10",
        "command_explanation": "Lists currently running systemd service units."
    },
    "iptables": {
        "title": "iptables — Linux Kernel Packet Filter & Firewall Administration",
        "description": "Configures IP packet filter rulesets in the Linux kernel network stack across chains: `INPUT`, `OUTPUT`, `FORWARD`, and tables: `filter`, `nat`, `mangle`.",
        "syntax": "iptables [-t table] COMMAND chain [rule-specification]",
        "risk_level": "HIGH",
        "flags": [
            ("-L, --list", "List all rules in the selected chain or all chains"),
            ("-n, --numeric", "Display IP addresses and port numbers in numeric format"),
            ("-v, --verbose", "Show packet and byte counters, interface names, options"),
            ("-A, --append", "Append one or more rules to the end of selected chain"),
            ("-D, --delete", "Delete one or more rules from selected chain by specification or index"),
            ("-F, --flush", "Flush (delete) all rules in chain or all tables (DANGEROUS)")
        ],
        "examples": [
            ("iptables -L -n -v", "Display all active firewall rules with packet statistics"),
            ("iptables -A INPUT -p tcp --dport 22 -j ACCEPT", "Allow incoming SSH connections on port 22"),
            ("iptables -A INPUT -s 192.168.1.100 -j DROP", "Block all traffic from specific IP address")
        ],
        "default_command": "iptables -L -n -v 2>/dev/null || echo 'Requires root privileges or iptables-legacy.'",
        "command_explanation": "Lists current packet filtering rules without modifying state."
    },
    "awk": {
        "title": "awk — Pattern Scanning and Text Processing Language",
        "description": "A Turing-complete pattern matching and columnar text processing language for data extraction, log reporting, and stream transformations.",
        "syntax": "awk 'pattern { action }' input-file",
        "risk_level": "LOW",
        "flags": [
            ("-F fs", "Define input field separator (e.g. -F: for /etc/passwd or -F',' for CSV)"),
            ("-v var=val", "Assign external variable value accessible inside awk script"),
            ("-f progfile", "Read awk script source code from a file rather than inline argument")
        ],
        "examples": [
            ("awk -F: '{print $1, $6}' /etc/passwd", "Print username ($1) and home directory ($6) from /etc/passwd"),
            ("df -h | awk '$5 > 80 {print $1, $5}'", "Filter and print partitions exceeding 80% disk capacity"),
            ("awk '{sum += $1} END {print sum}' numbers.txt", "Sum values in column 1 of a file")
        ],
        "default_command": "ps -eo pid,user,comm,%mem | awk 'NR==1 || $4 > 1.0' | head -n 10",
        "command_explanation": "Extracts process columns and filters tasks using more than 1% memory."
    },
    "curl": {
        "title": "curl — Command-Line Client for URL Data Transfers",
        "description": "Transfers data to or from servers supporting HTTP, HTTPS, FTP, FTPS, SCP, SFTP, TFTP, DICT, TELNET, LDAP, and FILE protocols with SSL encryption, cookies, and authentication.",
        "syntax": "curl [options] [URL...]",
        "risk_level": "LOW",
        "flags": [
            ("-I, --head", "Fetch HTTP response headers only (HEAD request)"),
            ("-s, --silent", "Silent mode (suppress progress meter and error messages)"),
            ("-X, --request [METHOD]", "Specify custom HTTP request method (GET, POST, PUT, DELETE)"),
            ("-d, --data [DATA]", "Sends specified data in HTTP POST request body"),
            ("-H, --header [LINE]", "Pass custom header to server (e.g. -H 'Content-Type: application/json')"),
            ("-o, --output [FILE]", "Write output to destination file instead of stdout"),
            ("-L, --location", "Follow HTTP 3xx redirects automatically")
        ],
        "examples": [
            ("curl -I https://google.com", "Check HTTP status code and response headers"),
            ("curl -s https://api.ipify.org", "Fetch external public IP address"),
            ("curl -X POST https://api.site.com/data -H 'Content-Type: application/json' -d '{\"key\":\"val\"}'", "Send JSON payload")
        ],
        "default_command": "curl -I -s -L https://1.1.1.1 | head -n 5",
        "command_explanation": "Tests network connectivity by probing Cloudflare DNS gateway headers."
    },
    "lsof": {
        "title": "lsof — List Open Files and Associated Processes",
        "description": "Lists information about files opened by running processes, including network sockets, Unix domain sockets, pipes, regular files, and mounted devices.",
        "syntax": "lsof [options]",
        "risk_level": "LOW",
        "flags": [
            ("-i [:[port]]", "Select listening or established internet network files/ports (e.g. -i :8000)"),
            ("-p PID", "List open files belonging to a specific process ID"),
            ("-u USER", "List open files belonging to specified login user"),
            ("+D DIR", "Search for open files within directory tree DIR")
        ],
        "examples": [
            ("lsof -i :8000", "Find which process is currently listening on port 8000"),
            ("lsof -i -P -n | grep LISTEN", "List all listening ports with numeric addresses (no DNS delay)"),
            ("lsof -u root", "View open file descriptors held by root services")
        ],
        "default_command": "netstat -tuln 2>/dev/null || ss -tuln 2>/dev/null || lsof -i -P -n | head -n 10",
        "command_explanation": "Displays active listening ports and network sockets."
    },
    "find": {
        "title": "find — Search for Files in a Directory Hierarchy",
        "description": "Recursively searches directory trees for files matching expressions based on name, size, permissions, modification time, file type, and owner.",
        "syntax": "find [path...] [expression]",
        "risk_level": "LOW",
        "flags": [
            ("-name pattern", "Match filenames case-sensitively using shell wildcard patterns"),
            ("-iname pattern", "Match filenames case-insensitively"),
            ("-type [f|d|l]", "Filter by file type: `f` (regular file), `d` (directory), `l` (symlink)"),
            ("-size [+|-]N[c|k|M|G]", "Filter by size (e.g., +100M for files larger than 100 megabytes)"),
            ("-mtime [+|-]N", "File data last modified N*24 hours ago (-7 means within last 7 days)"),
            ("-exec cmd {} +", "Execute shell command on all matching file paths")
        ],
        "examples": [
            ("find /var/log -type f -name '*.log'", "Find all log files under /var/log"),
            ("find /home -type f -size +50M", "Find all files larger than 50MB in home directory"),
            ("find . -name '*.pyc' -delete", "Find and delete cached Python bytecode files")
        ],
        "default_command": "find . -maxdepth 2 -type f | head -n 10",
        "command_explanation": "Lists top files within current directory hierarchy."
    }
}


class KnowledgeEngine:
    """
    Intelligent Dynamic Knowledge & Manual Engine.
    Produces comprehensive technical breakdowns and executable command recipes.
    """

    def explain_command(self, command_name: str, query_phrase: str = "") -> Dict[str, Any]:
        """
        Generates structured technical documentation and actionable execution commands
        for the given command or operational inquiry.
        """
        clean_cmd = command_name.strip().lower()

        # 1. Check Curated Knowledge Base
        if clean_cmd in CORE_MANUALS:
            manual = CORE_MANUALS[clean_cmd]
            return self._format_response(manual, clean_cmd)

        # 2. Dynamic Manual Generation for any other system utility
        return self._generate_dynamic_manual(clean_cmd, query_phrase)

    def _format_response(self, manual: Dict[str, Any], command_name: str) -> Dict[str, Any]:
        """Formats curated manual dictionary into rich Markdown and approval cards."""
        flags_md = "\n".join([f"| `{flag}` | {desc} |" for flag, desc in manual["flags"]])
        examples_md = "\n".join([f"```bash\n# {desc}\n{code}\n```" for code, desc in manual["examples"]])

        risk = manual.get("risk_level", "LOW")
        risk_badge = "🟢 **LOW RISK**" if risk == "LOW" else ("🟡 **MEDIUM RISK**" if risk == "MEDIUM" else "🔴 **HIGH RISK**")

        markdown_body = f"""### 📖 Command Knowledge Manual: `{command_name}`

**{manual['title']}**  
{manual['description']}

---

#### ⚙️ Command Syntax & Structure:
```bash
{manual['syntax']}
```
**Operational Safety Level:** {risk_badge}

---

#### 📋 Key Options & Flags:
| Flag / Option | Description |
| :--- | :--- |
{flags_md}

---

#### 💡 Practical Examples:
{examples_md}

---

#### 🚀 Recommended Demonstration Command:
*You can approve and run the safe demonstration command below to test `{command_name}` interactively in your environment.*
"""

        proposed_command = {
            "id": f"cmd-manual-{command_name}",
            "command": manual["default_command"],
            "explanation": manual["command_explanation"],
            "risk_level": risk
        }

        root_cause = {
            "nodes": [
                {"id": "user_query", "label": f"Manual Query: {command_name}", "type": "process"},
                {"id": "cmd_manual", "label": f"Syntax & Flags ({command_name})", "type": "system"},
                {"id": "cmd_exec", "label": "Interactive Execution", "type": "impact"}
            ],
            "edges": [
                {"from": "user_query", "to": "cmd_manual"},
                {"from": "cmd_manual", "to": "cmd_exec"}
            ]
        }

        return {
            "markdown": markdown_body,
            "commands": [proposed_command],
            "root_cause": root_cause,
            "recommendations": [
                f"Refer to the syntax flags above for configuring `{command_name}`.",
                f"Test the command using the proposed interactive approval card below."
            ]
        }

    def _generate_dynamic_manual(self, command_name: str, query_phrase: str) -> Dict[str, Any]:
        """
        Dynamically introspects and synthesizes a manual for arbitrary utilities (e.g. docker, git, ping, etc.)
        """
        # Try to fetch live help output if available
        live_help = ""
        try:
            res = ubuntu_bridge.run_command(f"{command_name} --help", timeout_sec=2)
            if res.get("success") and res.get("output"):
                lines = res["output"].splitlines()[:15]
                live_help = "\n".join(lines)
        except Exception:
            live_help = ""

        help_section = f"\n\n#### 📟 Live System Help Snippet (`{command_name} --help`):\n```text\n{live_help}\n```" if live_help else ""

        markdown_body = f"""### 📖 Command Knowledge Manual: `{command_name}`

**Utility:** `{command_name}`  
**Operational Scope:** Linux / Windows System & Terminal Operations

---

#### ⚙️ Standard Usage Pattern:
```bash
{command_name} [OPTIONS] [ARGUMENTS...]
```
**Safety Level:** 🟢 **STANDARD UTILITY** (Inspect options before executing with root permissions)

---

#### 💡 Common Invocations:
```bash
# View command help documentation
{command_name} --help

# Check installed version
{command_name} --version
```
{help_section}

---

#### 🚀 Interactive Test Command:
*Approve the command below to inspect `{command_name}` live in your Ubuntu / WSL2 environment.*
"""

        proposed_command = {
            "id": f"cmd-dynamic-{command_name}",
            "command": f"wsl.exe -d Ubuntu bash -c \"{command_name} --help || echo 'Command {command_name}'; exec bash\"",
            "explanation": f"Opens interactive Ubuntu terminal executing '{command_name} --help'.",
            "risk_level": "LOW"
        }

        root_cause = {
            "nodes": [
                {"id": "query_node", "label": f"Inquiry: {command_name}", "type": "process"},
                {"id": "dynamic_doc", "label": "Dynamic CLI Manual", "type": "system"},
                {"id": "wsl_terminal", "label": "WSL2 Terminal Inspection", "type": "impact"}
            ],
            "edges": [
                {"from": "query_node", "to": "dynamic_doc"},
                {"from": "dynamic_doc", "to": "wsl_terminal"}
            ]
        }

        return {
            "markdown": markdown_body,
            "commands": [proposed_command],
            "root_cause": root_cause,
            "recommendations": [
                f"Run `{command_name} --help` to view all supported parameters in your distribution.",
                "Execute the proposed command card below to open the interactive terminal."
            ]
        }


knowledge_engine = KnowledgeEngine()
