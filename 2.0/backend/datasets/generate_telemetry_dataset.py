"""
Telemetry Dataset Generator for KernelSense ML Anomaly Detector
Generates realistic multi-variate system metric time-series data covering:
- Normal Workloads (Idle, Media Streaming, Software Compilation, Database I/O)
- System Failure / Anomaly Scenarios:
  - Memory Leaks (Monotonic RAM growth, swap saturation, page faults)
  - CPU Thrashing (Core starvation, context switch spikes, loop saturation)
  - Disk I/O Saturation (Unbounded write throughput, I/O wait peaks)
  - Network Packet Storms / Socket Floods
  - Fork Bombs / Thread Explosion
"""

import os
import numpy as np
import pandas as pd

def generate_telemetry_dataset(num_samples: int = 6000, random_state: int = 42) -> pd.DataFrame:
    np.random.seed(random_state)
    
    # 80% Normal Operations, 20% Anomalies
    num_normal = int(num_samples * 0.80)
    num_anomalies = num_samples - num_normal
    
    # -------------------------------------------------------------
    # 1. NORMAL TELEMETRY SAMPLES
    # -------------------------------------------------------------
    # CPU: Typically 5% - 55%, low variance
    cpu_percent_norm = np.random.beta(2, 5, num_normal) * 70.0 + 2.0
    cpu_variance_norm = np.random.uniform(0.5, 8.0, num_normal)
    
    # Memory: 25% - 75%, gentle slope (-0.1 to +0.1)
    mem_percent_norm = np.random.normal(50.0, 12.0, num_normal).clip(15.0, 80.0)
    mem_slope_norm = np.random.normal(0.0, 0.05, num_normal)
    swap_percent_norm = (mem_percent_norm * 0.2 * np.random.uniform(0.1, 0.5, num_normal)).clip(0.0, 25.0)
    
    # Disk I/O: 0.5 MB/s to 40 MB/s
    disk_read_norm = np.random.exponential(scale=5.0, size=num_normal).clip(0.0, 50.0)
    disk_write_norm = np.random.exponential(scale=8.0, size=num_normal).clip(0.0, 60.0)
    
    # Network: 0.1 MB/s to 15 MB/s
    net_sent_norm = np.random.exponential(scale=2.0, size=num_normal).clip(0.0, 20.0)
    net_recv_norm = np.random.exponential(scale=4.0, size=num_normal).clip(0.0, 30.0)
    
    # System stats
    context_switches_norm = np.random.normal(2500, 600, num_normal).clip(800, 6000)
    num_threads_norm = np.random.normal(1200, 250, num_normal).clip(400, 2200)
    
    normal_df = pd.DataFrame({
        'cpu_percent': cpu_percent_norm,
        'cpu_variance': cpu_variance_norm,
        'mem_percent': mem_percent_norm,
        'mem_slope': mem_slope_norm,
        'swap_percent': swap_percent_norm,
        'disk_read_mbs': disk_read_norm,
        'disk_write_mbs': disk_write_norm,
        'net_sent_mbs': net_sent_norm,
        'net_recv_mbs': net_recv_norm,
        'context_switches': context_switches_norm,
        'num_threads': num_threads_norm,
        'is_anomaly': 0,
        'anomaly_type': 'NORMAL'
    })
    
    # -------------------------------------------------------------
    # 2. ANOMALY TELEMETRY SAMPLES
    # -------------------------------------------------------------
    anomaly_splits = num_anomalies // 5
    
    # A. Memory Leak
    mem_leak_df = pd.DataFrame({
        'cpu_percent': np.random.uniform(20.0, 65.0, anomaly_splits),
        'cpu_variance': np.random.uniform(2.0, 10.0, anomaly_splits),
        'mem_percent': np.random.uniform(88.0, 99.5, anomaly_splits),
        'mem_slope': np.random.uniform(0.8, 4.5, anomaly_splits),  # Rapid expansion
        'swap_percent': np.random.uniform(70.0, 98.0, anomaly_splits),
        'disk_read_mbs': np.random.uniform(5.0, 35.0, anomaly_splits),
        'disk_write_mbs': np.random.uniform(20.0, 80.0, anomaly_splits), # Heavy swap paging
        'net_sent_mbs': np.random.uniform(0.5, 10.0, anomaly_splits),
        'net_recv_mbs': np.random.uniform(0.5, 15.0, anomaly_splits),
        'context_switches': np.random.uniform(4000, 12000, anomaly_splits),
        'num_threads': np.random.uniform(1000, 2500, anomaly_splits),
        'is_anomaly': 1,
        'anomaly_type': 'MEMORY_LEAK'
    })
    
    # B. CPU Thrashing / Infinite Loop
    cpu_thrash_df = pd.DataFrame({
        'cpu_percent': np.random.uniform(92.0, 100.0, anomaly_splits),
        'cpu_variance': np.random.uniform(0.1, 1.5, anomaly_splits), # Stuck at 100%
        'mem_percent': np.random.uniform(30.0, 75.0, anomaly_splits),
        'mem_slope': np.random.normal(0.0, 0.05, anomaly_splits),
        'swap_percent': np.random.uniform(0.0, 15.0, anomaly_splits),
        'disk_read_mbs': np.random.uniform(0.0, 10.0, anomaly_splits),
        'disk_write_mbs': np.random.uniform(0.0, 15.0, anomaly_splits),
        'net_sent_mbs': np.random.uniform(0.1, 5.0, anomaly_splits),
        'net_recv_mbs': np.random.uniform(0.1, 5.0, anomaly_splits),
        'context_switches': np.random.uniform(15000, 50000, anomaly_splits), # High thrashing
        'num_threads': np.random.uniform(1200, 3000, anomaly_splits),
        'is_anomaly': 1,
        'anomaly_type': 'CPU_THRASHING'
    })
    
    # C. Disk I/O Saturation
    disk_sat_df = pd.DataFrame({
        'cpu_percent': np.random.uniform(15.0, 45.0, anomaly_splits),
        'cpu_variance': np.random.uniform(1.0, 8.0, anomaly_splits),
        'mem_percent': np.random.uniform(40.0, 80.0, anomaly_splits),
        'mem_slope': np.random.normal(0.0, 0.1, anomaly_splits),
        'swap_percent': np.random.uniform(5.0, 30.0, anomaly_splits),
        'disk_read_mbs': np.random.uniform(180.0, 450.0, anomaly_splits), # Bottleneck throughput
        'disk_write_mbs': np.random.uniform(200.0, 550.0, anomaly_splits),
        'net_sent_mbs': np.random.uniform(0.5, 10.0, anomaly_splits),
        'net_recv_mbs': np.random.uniform(0.5, 10.0, anomaly_splits),
        'context_switches': np.random.uniform(8000, 25000, anomaly_splits),
        'num_threads': np.random.uniform(1000, 2200, anomaly_splits),
        'is_anomaly': 1,
        'anomaly_type': 'DISK_IO_SATURATION'
    })
    
    # D. Network Packet Flood / DDoS
    net_flood_df = pd.DataFrame({
        'cpu_percent': np.random.uniform(45.0, 85.0, anomaly_splits),
        'cpu_variance': np.random.uniform(5.0, 15.0, anomaly_splits),
        'mem_percent': np.random.uniform(35.0, 70.0, anomaly_splits),
        'mem_slope': np.random.normal(0.0, 0.05, anomaly_splits),
        'swap_percent': np.random.uniform(0.0, 10.0, anomaly_splits),
        'disk_read_mbs': np.random.uniform(0.5, 15.0, anomaly_splits),
        'disk_write_mbs': np.random.uniform(0.5, 20.0, anomaly_splits),
        'net_sent_mbs': np.random.uniform(85.0, 300.0, anomaly_splits), # Network flood
        'net_recv_mbs': np.random.uniform(120.0, 450.0, anomaly_splits),
        'context_switches': np.random.uniform(12000, 35000, anomaly_splits),
        'num_threads': np.random.uniform(1500, 3500, anomaly_splits),
        'is_anomaly': 1,
        'anomaly_type': 'NETWORK_FLOOD'
    })
    
    # E. Thread Explosion / Fork Bomb
    fork_bomb_df = pd.DataFrame({
        'cpu_percent': np.random.uniform(75.0, 100.0, anomaly_splits),
        'cpu_variance': np.random.uniform(2.0, 12.0, anomaly_splits),
        'mem_percent': np.random.uniform(60.0, 95.0, anomaly_splits),
        'mem_slope': np.random.uniform(0.5, 2.0, anomaly_splits),
        'swap_percent': np.random.uniform(20.0, 60.0, anomaly_splits),
        'disk_read_mbs': np.random.uniform(10.0, 40.0, anomaly_splits),
        'disk_write_mbs': np.random.uniform(10.0, 50.0, anomaly_splits),
        'net_sent_mbs': np.random.uniform(0.1, 5.0, anomaly_splits),
        'net_recv_mbs': np.random.uniform(0.1, 5.0, anomaly_splits),
        'context_switches': np.random.uniform(30000, 90000, anomaly_splits), # Extreme switching
        'num_threads': np.random.uniform(8000, 45000, anomaly_splits),        # Massive threads
        'is_anomaly': 1,
        'anomaly_type': 'FORK_BOMB'
    })
    
    full_df = pd.concat([normal_df, mem_leak_df, cpu_thrash_df, disk_sat_df, net_flood_df, fork_bomb_df], ignore_index=True)
    return full_df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

if __name__ == '__main__':
    dataset_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(dataset_dir, 'telemetry_train.csv')
    df = generate_telemetry_dataset(num_samples=8000)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} telemetry samples -> {output_path}")
    print(df['anomaly_type'].value_counts())
