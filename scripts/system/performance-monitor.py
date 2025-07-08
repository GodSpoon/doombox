#!/usr/bin/env python3
"""
Performance monitoring script for DoomBox kiosk
Monitors CPU usage, memory usage, and video playback performance
"""

import psutil
import time
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

class PerformanceMonitor:
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.start_time = time.time()
        self.measurements = []
        
    def get_system_stats(self):
        """Get current system performance statistics"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_per_core': psutil.cpu_percent(interval=1, percpu=True),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available': psutil.virtual_memory().available,
            'memory_used': psutil.virtual_memory().used,
            'swap_percent': psutil.swap_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'temperature': self.get_temperature(),
            'load_average': os.getloadavg(),
        }
        
        # Get process-specific stats if kiosk is running
        kiosk_stats = self.get_kiosk_process_stats()
        if kiosk_stats:
            stats.update(kiosk_stats)
            
        return stats
    
    def get_temperature(self):
        """Get CPU temperature if available"""
        try:
            # Try common temperature sources
            temp_files = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/class/thermal/thermal_zone1/temp',
                '/opt/vc/bin/vcgencmd measure_temp'
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        temp_str = f.read().strip()
                        if temp_str.isdigit():
                            return float(temp_str) / 1000.0  # Convert from millidegrees
                        
            # Try vcgencmd for Raspberry Pi
            try:
                result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    temp_str = result.stdout.strip()
                    if 'temp=' in temp_str:
                        return float(temp_str.split('=')[1].replace("'C", ""))
            except:
                pass
                
        except Exception as e:
            pass
            
        return None
    
    def get_kiosk_process_stats(self):
        """Get statistics for kiosk processes"""
        try:
            kiosk_processes = []
            
            # Look for kiosk-related processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    if any(keyword in proc.info['name'].lower() for keyword in ['kiosk', 'python', 'doom']):
                        kiosk_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent'],
                            'memory_rss': proc.info['memory_info'].rss,
                            'memory_vms': proc.info['memory_info'].vms,
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if kiosk_processes:
                return {
                    'kiosk_processes': kiosk_processes,
                    'total_kiosk_cpu': sum(p['cpu_percent'] for p in kiosk_processes),
                    'total_kiosk_memory': sum(p['memory_percent'] for p in kiosk_processes),
                }
        except Exception as e:
            print(f"Error getting process stats: {e}")
            
        return None
    
    def get_gpu_stats(self):
        """Get GPU statistics if available"""
        try:
            # Try to get GPU memory info
            result = subprocess.run(['vcgencmd', 'get_mem', 'gpu'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                gpu_mem = result.stdout.strip()
                return {'gpu_memory': gpu_mem}
        except:
            pass
            
        return None
    
    def get_video_codec_info(self):
        """Get information about video codec support"""
        try:
            # Check for hardware video acceleration
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                  capture_output=True, text=True, timeout=5)
            
            hw_encoders = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if any(hw in line.lower() for hw in ['v4l2', 'omx', 'mmal', 'vaapi']):
                        hw_encoders.append(line.strip())
            
            # Check decoders
            result = subprocess.run(['ffmpeg', '-hide_banner', '-decoders'], 
                                  capture_output=True, text=True, timeout=5)
            
            hw_decoders = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if any(hw in line.lower() for hw in ['v4l2', 'omx', 'mmal', 'vaapi']):
                        hw_decoders.append(line.strip())
            
            return {
                'hardware_encoders': hw_encoders,
                'hardware_decoders': hw_decoders,
                'hw_acceleration_available': len(hw_encoders) > 0 or len(hw_decoders) > 0
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def log_stats(self, stats):
        """Log statistics to file and console"""
        timestamp = stats['timestamp']
        
        # Console output
        print(f"\n=== Performance Stats - {timestamp} ===")
        print(f"CPU: {stats['cpu_percent']:.1f}% | Memory: {stats['memory_percent']:.1f}%")
        print(f"Load Average: {stats['load_average']}")
        
        if 'temperature' in stats and stats['temperature']:
            print(f"Temperature: {stats['temperature']:.1f}°C")
        
        if 'kiosk_processes' in stats:
            print(f"Kiosk CPU: {stats['total_kiosk_cpu']:.1f}% | Kiosk Memory: {stats['total_kiosk_memory']:.1f}%")
            print("Kiosk Processes:")
            for proc in stats['kiosk_processes']:
                print(f"  {proc['name']} (PID {proc['pid']}): CPU {proc['cpu_percent']:.1f}%, Memory {proc['memory_percent']:.1f}%")
        
        # File output
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(stats) + '\n')
            except Exception as e:
                print(f"Error writing to log file: {e}")
        
        self.measurements.append(stats)
    
    def run_continuous_monitoring(self, interval=5, duration=None):
        """Run continuous performance monitoring"""
        print(f"Starting performance monitoring (interval: {interval}s)")
        
        if duration:
            print(f"Monitoring for {duration} seconds")
            end_time = time.time() + duration
        else:
            print("Monitoring indefinitely (Ctrl+C to stop)")
            end_time = float('inf')
        
        try:
            while time.time() < end_time:
                stats = self.get_system_stats()
                self.log_stats(stats)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        
        self.print_summary()
    
    def print_summary(self):
        """Print monitoring summary"""
        if not self.measurements:
            return
            
        print("\n=== Monitoring Summary ===")
        
        cpu_values = [m['cpu_percent'] for m in self.measurements]
        memory_values = [m['memory_percent'] for m in self.measurements]
        
        print(f"Duration: {time.time() - self.start_time:.1f} seconds")
        print(f"Measurements: {len(self.measurements)}")
        print(f"CPU - Avg: {sum(cpu_values)/len(cpu_values):.1f}%, Max: {max(cpu_values):.1f}%")
        print(f"Memory - Avg: {sum(memory_values)/len(memory_values):.1f}%, Max: {max(memory_values):.1f}%")
        
        # Check for concerning patterns
        high_cpu_count = sum(1 for cpu in cpu_values if cpu > 80)
        high_memory_count = sum(1 for mem in memory_values if mem > 80)
        
        if high_cpu_count > 0:
            print(f"⚠️  High CPU usage detected {high_cpu_count} times")
        
        if high_memory_count > 0:
            print(f"⚠️  High memory usage detected {high_memory_count} times")
    
    def run_system_info(self):
        """Display system information"""
        print("=== System Information ===")
        
        # Basic system info
        print(f"Platform: {psutil.platform}")
        print(f"CPU Count: {psutil.cpu_count()}")
        print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        print(f"Boot Time: {datetime.fromtimestamp(psutil.boot_time())}")
        
        # Video codec info
        print("\n=== Video Codec Support ===")
        codec_info = self.get_video_codec_info()
        
        if 'hw_acceleration_available' in codec_info:
            if codec_info['hw_acceleration_available']:
                print("✅ Hardware acceleration available")
                if codec_info['hardware_encoders']:
                    print("Hardware Encoders:")
                    for encoder in codec_info['hardware_encoders'][:5]:  # Limit output
                        print(f"  {encoder}")
                if codec_info['hardware_decoders']:
                    print("Hardware Decoders:")
                    for decoder in codec_info['hardware_decoders'][:5]:  # Limit output
                        print(f"  {decoder}")
            else:
                print("❌ No hardware acceleration detected")
        else:
            print("❓ Could not determine hardware acceleration support")
        
        # GPU info
        gpu_stats = self.get_gpu_stats()
        if gpu_stats:
            print(f"\n=== GPU Information ===")
            print(f"GPU Memory: {gpu_stats.get('gpu_memory', 'Unknown')}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='DoomBox Performance Monitor')
    parser.add_argument('--interval', '-i', type=int, default=5, 
                       help='Monitoring interval in seconds (default: 5)')
    parser.add_argument('--duration', '-d', type=int, 
                       help='Monitoring duration in seconds (default: continuous)')
    parser.add_argument('--log-file', '-l', type=str, 
                       help='Log file path (default: no logging)')
    parser.add_argument('--info', action='store_true',
                       help='Show system information and exit')
    
    args = parser.parse_args()
    
    # Create logs directory if logging
    if args.log_file:
        log_path = Path(args.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    monitor = PerformanceMonitor(args.log_file)
    
    if args.info:
        monitor.run_system_info()
    else:
        monitor.run_continuous_monitoring(args.interval, args.duration)


if __name__ == "__main__":
    main()
