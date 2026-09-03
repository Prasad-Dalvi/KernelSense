"""
System Log Dataset Generator for KernelSense NLP Intelligence Model
Generates authentic Linux system logs across multiple categories:
- OOM_KILLER: Memory starvation and kernel process termination
- KERNEL_PANIC: Kernel core faults, segmentation faults, invalid ops
- IO_ERROR: Filesystem corruption, block device errors, bad sectors
- NETWORK_FAILURE: Interface drops, connection timeouts, DNS resets
- SECURITY_ALERT: Sudo failures, brute force SSH, invalid permissions
- NORMAL_INFO: Normal daemon lifecycles, cron, systemd units
"""

import os
import random
import pandas as pd

LOG_TEMPLATES = {
    'OOM_KILLER': [
        "kernel: [ {uptime} ] Out of memory: Kill process {pid} ({proc}) score {score} or sacrifice child",
        "kernel: [ {uptime} ] invoked oom-killer: gfp_mask=0x{hex}, order=0, oom_score_adj=0",
        "kernel: [ {uptime} ] Memory cgroup out of memory: Killed process {pid} ({proc}) total-vm:{vm}kB, anon-rss:{rss}kB",
        "kernel: [ {uptime} ] page allocation failure: order:0, mode:0x{hex}(GFP_KERNEL)",
        "kernel: [ {uptime} ] oom_reaper: reaped process {pid} ({proc}), now anon-rss:0kB",
        "systemd[1]: Process {pid} ({proc}) of unit user@1000.service killed by OOM killer",
    ],
    'KERNEL_PANIC': [
        "kernel: [ {uptime} ] BUG: unable to handle page fault for address: 0x{hex}",
        "kernel: [ {uptime} ] Kernel panic - not syncing: Fatal exception in interrupt",
        "kernel: [ {uptime} ] RIP: 0010:do_syscall_64+0x{hex}/0x{hex}",
        "kernel: [ {uptime} ] Code: Bad RIP value. CR2: 00007f{hex}",
        "kernel: [ {uptime} ] Call Trace: ? handle_mm_fault+0x{hex} ? do_user_addr_fault+0x{hex}",
        "kernel: [ {uptime} ] Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block({major},{minor})",
        "kernel: [ {uptime} ] General protection fault in {proc}[{pid}]: error code 0x0",
    ],
    'IO_ERROR': [
        "kernel: [ {uptime} ] EXT4-fs error (device {dev}): ext4_lookup: deleted inode referenced: {inode}",
        "kernel: [ {uptime} ] blk_update_request: I/O error, dev {dev}, sector {sector} op 0x0:(READ) flags 0x80700",
        "kernel: [ {uptime} ] Buffer I/O error on dev {dev}, logical block {block}, async page read",
        "kernel: [ {uptime} ] EXT4-fs (device {dev}): Remounting filesystem read-only",
        "kernel: [ {uptime} ] ata1.00: failed to execute command: READ FPDMA QUEUED",
        "kernel: [ {uptime} ] smartd[542]: Device: /dev/{dev}, FAILED SMART self-check. Read failure rate exceeded threshold",
    ],
    'NETWORK_FAILURE': [
        "kernel: [ {uptime} ] {iface}: link down, carrier lost",
        "systemd-resolved[412]: Using degraded feature set (UDP) for DNS server {ip}",
        "kernel: [ {uptime} ] TCP: request_sock_TCP: Possible SYN flooding on port {port}. Dropping request.",
        "NetworkManager[621]: <warn> [ {uptime} ] connection '{con}' failed to activate: IP configuration unavailable",
        "sshd[{pid}]: Connection reset by peer {ip} port {port} [preauth]",
        "kernel: [ {uptime} ] e1000e 0000:00:1f.6 {iface}: Reset adapter unexpectedly",
    ],
    'SECURITY_ALERT': [
        "sshd[{pid}]: Failed password for invalid user {user} from {ip} port {port} ssh2",
        "sudo: {user} : 3 incorrect password attempts ; TTY=pts/1 ; PWD=/home/{user} ; USER=root ; COMMAND=/bin/bash",
        "sshd[{pid}]: PAM 2 more authentication failures; logname= uid=0 euid=0 tty=ssh ruser= rhost={ip}",
        "kernel: [ {uptime} ] audit: type=1400 audit({uptime}.001:{seq}): apparmor=\"DENIED\" operation=\"exec\" profile=\"/usr/sbin/{proc}\"",
        "sshd[{pid}]: Received disconnect from {ip} port {port}:11: Bye Bye [preauth]",
        "sudo: {user} : user NOT in sudoers ; TTY=pts/2 ; PWD=/tmp ; USER=root ; COMMAND=/usr/bin/cat /etc/shadow",
    ],
    'NORMAL_INFO': [
        "systemd[1]: Starting Daily apt download activities...",
        "systemd[1]: Finished Daily apt download activities.",
        "CRON[{pid}]: (root) CMD (   test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily ))",
        "systemd-timesyncd[350]: Synchronized to time server {ip}:123 (time.cloudflare.com).",
        "systemd[1]: Started Service for user session {pid}.",
        "NetworkManager[621]: <info> [ {uptime} ] {iface}: IP4 address successfully configured to {ip}/24",
        "kernel: [ {uptime} ] usb 1-1.2: new high-speed USB device number {pid} using xhci_hcd",
        "systemd[1]: Reached target Graphical Interface.",
    ]
}

PROCS = ['chrome', 'mysqld', 'dockerd', 'node', 'python3', 'java', 'redis-server', 'nginx', 'electron', 'rustc']
DEVS = ['sda1', 'sda2', 'nvme0n1p1', 'nvme0n1p2', 'sdb1']
IFACES = ['eth0', 'wlan0', 'enp3s0', 'docker0']
USERS = ['root', 'admin', 'deploy', 'guest', 'ubuntu', 'developer']

def format_template(template: str) -> str:
    return template.format(
        uptime=f"{random.uniform(10.0, 99999.0):.6f}",
        pid=random.randint(100, 65000),
        proc=random.choice(PROCS),
        score=random.randint(200, 1000),
        hex=f"{random.randint(10000, 999999):x}",
        vm=random.randint(200000, 8000000),
        rss=random.randint(100000, 4000000),
        dev=random.choice(DEVS),
        inode=random.randint(1000, 900000),
        sector=random.randint(100000, 90000000),
        block=random.randint(1000, 5000000),
        iface=random.choice(IFACES),
        ip=f"192.168.1.{random.randint(2, 254)}",
        port=random.randint(1024, 65535),
        user=random.choice(USERS),
        seq=random.randint(1, 999),
        major=random.randint(1, 254),
        minor=random.randint(0, 16),
        con="Wired connection 1"
    )

def generate_log_dataset(samples_per_category: int = 500, random_state: int = 42) -> pd.DataFrame:
    random.seed(random_state)
    rows = []
    
    for category, templates in LOG_TEMPLATES.items():
        is_error = 0 if category == 'NORMAL_INFO' else 1
        severity = 'info' if category == 'NORMAL_INFO' else ('warning' if category in ['SECURITY_ALERT', 'NETWORK_FAILURE'] else 'error')
        
        for _ in range(samples_per_category):
            tmpl = random.choice(templates)
            message = format_template(tmpl)
            rows.append({
                'message': message,
                'category': category,
                'severity': severity,
                'is_error': is_error
            })
            
    df = pd.DataFrame(rows)
    return df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

if __name__ == '__main__':
    dataset_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(dataset_dir, 'logs_train.csv')
    df = generate_log_dataset(samples_per_category=700)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} log samples -> {output_path}")
    print(df['category'].value_counts())
