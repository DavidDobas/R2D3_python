#!/usr/bin/env python3
"""
Test script for Intel RealSense cameras.
Tests camera connection, frame capture, and displays basic statistics.
"""

import argparse
import sys
import numpy as np
import cv2
import time

try:
    import pyrealsense2 as rs
except ImportError:
    print("Error: pyrealsense2 not installed.")
    print("Install with: pip install pyrealsense2")
    sys.exit(1)


class RealSenseTester:
    """Test and display RealSense camera capabilities."""
    
    def __init__(self, device_id=None, width=640, height=480, fps=30):
        """
        Initialize RealSense tester.
        
        Args:
            device_id: Serial number or None for first available camera
            width: Color stream width
            height: Color stream height
            fps: Frames per second
        """
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        
        self.pipeline = None
        self.config = None
        self.device = None
        
    def list_devices(self):
        """List all available RealSense devices."""
        print("\n" + "="*70)
        print("Available RealSense Devices:")
        print("="*70)
        
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            print("No RealSense devices found.")
            return []
        
        device_list = []
        for i, device in enumerate(devices):
            serial = device.get_info(rs.camera_info.serial_number)
            name = device.get_info(rs.camera_info.name)
            firmware = device.get_info(rs.camera_info.firmware_version)
            
            device_list.append({
                'index': i,
                'serial': serial,
                'name': name,
                'firmware': firmware
            })
            
            print(f"\nDevice {i}:")
            print(f"  Serial Number: {serial}")
            print(f"  Name: {name}")
            print(f"  Firmware: {firmware}")
        
        print("\n" + "="*70)
        return device_list
    
    def connect(self):
        """Connect to RealSense camera."""
        print("\nConnecting to RealSense camera...")
        
        # Create pipeline and config
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        # Configure streams
        self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
        
        # Find device
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            print("✗ No RealSense devices found")
            return False
        
        # Select device
        if self.device_id:
            # Find by serial number
            device_found = False
            for device in devices:
                if device.get_info(rs.camera_info.serial_number) == self.device_id:
                    self.config.enable_device(self.device_id)
                    self.device = device
                    device_found = True
                    break
            if not device_found:
                print(f"✗ Device with serial {self.device_id} not found")
                return False
        else:
            # Use first available device
            self.device = devices[0]
            serial = self.device.get_info(rs.camera_info.serial_number)
            self.config.enable_device(serial)
        
        # Start pipeline
        try:
            profile = self.pipeline.start(self.config)
            print(f"✓ Connected to device: {self.device.get_info(rs.camera_info.name)}")
            print(f"  Serial: {self.device.get_info(rs.camera_info.serial_number)}")
            print(f"  Firmware: {self.device.get_info(rs.camera_info.firmware_version)}")
            
            # Get stream profiles
            color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
            depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
            
            print(f"\nColor Stream:")
            print(f"  Resolution: {color_profile.width()}x{color_profile.height()}")
            print(f"  Format: {color_profile.format()}")
            print(f"  FPS: {color_profile.fps()}")
            
            print(f"\nDepth Stream:")
            print(f"  Resolution: {depth_profile.width()}x{depth_profile.height()}")
            print(f"  Format: {depth_profile.format()}")
            print(f"  FPS: {depth_profile.fps()}")
            
            return True
        except Exception as e:
            print(f"✗ Failed to start pipeline: {e}")
            return False
    
    def test_capture(self, num_frames=30, display=True, save_images=False):
        """
        Test frame capture and display statistics.
        
        Args:
            num_frames: Number of frames to capture
            display: Whether to display frames in window
            save_images: Whether to save sample images
        """
        if not self.pipeline:
            print("✗ Camera not connected. Call connect() first.")
            return False
        
        print(f"\n{'='*70}")
        print(f"Capturing {num_frames} frames for testing...")
        print(f"{'='*70}\n")
        
        frame_times = []
        frame_count = 0
        color_frames = []
        depth_frames = []
        
        align_to = rs.align(rs.stream.color)
        
        try:
            while frame_count < num_frames:
                start_time = time.time()
                
                # Wait for frames
                frames = self.pipeline.wait_for_frames(timeout_ms=5000)
                
                # Align depth frame to color frame
                aligned_frames = align_to.process(frames)
                
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()
                
                if not color_frame or not depth_frame:
                    print("⚠ Warning: Missing frames, skipping...")
                    continue
                
                # Convert to numpy arrays
                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(depth_frame.get_data())
                
                frame_count += 1
                frame_time = time.time() - start_time
                frame_times.append(frame_time)
                
                if save_images and frame_count == 1:
                    # Save first frame
                    cv2.imwrite("realsense_color_sample.jpg", color_image)
                    # Normalize depth for visualization
                    depth_colormap = cv2.applyColorMap(
                        cv2.convertScaleAbs(depth_image, alpha=0.03),
                        cv2.COLORMAP_JET
                    )
                    cv2.imwrite("realsense_depth_sample.jpg", depth_colormap)
                    print(f"✓ Saved sample images: realsense_color_sample.jpg, realsense_depth_sample.jpg")
                
                if display:
                    # Create aligned depth colormap
                    depth_colormap = cv2.applyColorMap(
                        cv2.convertScaleAbs(depth_image, alpha=0.03),
                        cv2.COLORMAP_JET
                    )
                    
                    # Stack images side by side
                    images = np.hstack((color_image, depth_colormap))
                    
                    # Add text overlay
                    cv2.putText(images, f"Frame: {frame_count}/{num_frames}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(images, f"FPS: {1.0/frame_time:.1f}", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow('RealSense Test (Color | Depth)', images)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nStopped by user (q key)")
                        break
                
                # Store for statistics
                color_frames.append(color_image.shape)
                depth_frames.append(depth_image.shape)
                
                if frame_count % 10 == 0:
                    avg_fps = frame_count / sum(frame_times)
                    print(f"Captured {frame_count}/{num_frames} frames (avg FPS: {avg_fps:.2f})")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        except Exception as e:
            print(f"\n✗ Error during capture: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if display:
                cv2.destroyAllWindows()
        
        # Print statistics
        print(f"\n{'='*70}")
        print("Capture Statistics:")
        print(f"{'='*70}")
        print(f"Total frames captured: {frame_count}")
        
        if frame_times:
            avg_fps = frame_count / sum(frame_times)
            min_fps = 1.0 / max(frame_times)
            max_fps = 1.0 / min(frame_times)
            print(f"Average FPS: {avg_fps:.2f}")
            print(f"Min FPS: {min_fps:.2f}")
            print(f"Max FPS: {max_fps:.2f}")
            print(f"Frame time range: {min(frame_times)*1000:.2f}ms - {max(frame_times)*1000:.2f}ms")
        
        if color_frames:
            print(f"\nColor frames:")
            print(f"  Shape: {color_frames[0]}")
            print(f"  Dtype: uint8")
        
        if depth_frames:
            print(f"\nDepth frames:")
            print(f"  Shape: {depth_frames[0]}")
            print(f"  Dtype: uint16")
            print(f"  Units: millimeters")
        
        print(f"{'='*70}\n")
        
        return True
    
    def get_intrinsics(self):
        """Get camera intrinsics."""
        if not self.pipeline:
            print("✗ Camera not connected.")
            return None
        
        try:
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            
            if color_frame:
                intrinsics = color_frame.profile.as_video_stream_profile().intrinsics
                print("\nCamera Intrinsics:")
                print("="*70)
                print(f"  Focal length: fx={intrinsics.fx:.2f}, fy={intrinsics.fy:.2f}")
                print(f"  Principal point: cx={intrinsics.ppx:.2f}, cy={intrinsics.ppy:.2f}")
                print(f"  Distortion model: {intrinsics.model}")
                print(f"  Distortion coefficients: {intrinsics.coeffs}")
                return intrinsics
        except Exception as e:
            print(f"✗ Failed to get intrinsics: {e}")
        
        return None
    
    def disconnect(self):
        """Disconnect from camera."""
        if self.pipeline:
            self.pipeline.stop()
            print("\n✓ Disconnected from RealSense camera")


def main():
    parser = argparse.ArgumentParser(
        description="Test Intel RealSense camera connection and capture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available cameras
  python test_realsense.py --list
  
  # Test default camera (30 frames, with display)
  python test_realsense.py
  
  # Test specific camera by serial number
  python test_realsense.py --device 825412061234
  
  # Capture 100 frames without display
  python test_realsense.py --num-frames 100 --no-display
  
  # Save sample images
  python test_realsense.py --save-images
  
  # High resolution test
  python test_realsense.py --width 1920 --height 1080
  
Controls:
  - Press 'q' in display window to stop early
  - Ctrl+C to interrupt
        """
    )
    
    parser.add_argument("--list", action="store_true",
                        help="List all available RealSense devices")
    parser.add_argument("--device", type=str,
                        help="Camera serial number (optional, uses first available if not specified)")
    parser.add_argument("--width", type=int, default=640,
                        help="Color stream width (default: 640)")
    parser.add_argument("--height", type=int, default=480,
                        help="Color stream height (default: 480)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Frames per second (default: 30)")
    parser.add_argument("--num-frames", type=int, default=30,
                        help="Number of frames to capture (default: 30)")
    parser.add_argument("--no-display", action="store_true",
                        help="Don't display frames (faster)")
    parser.add_argument("--save-images", action="store_true",
                        help="Save sample color and depth images")
    parser.add_argument("--intrinsics", action="store_true",
                        help="Print camera intrinsics")
    
    args = parser.parse_args()
    
    tester = RealSenseTester(
        device_id=args.device,
        width=args.width,
        height=args.height,
        fps=args.fps
    )
    
    # List devices
    if args.list:
        tester.list_devices()
        return 0
    
    try:
        # Connect
        if not tester.connect():
            return 1
        
        # Get intrinsics if requested
        if args.intrinsics:
            tester.get_intrinsics()
        
        # Test capture
        success = tester.test_capture(
            num_frames=args.num_frames,
            display=not args.no_display,
            save_images=args.save_images
        )
        
        if not success:
            return 1
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        tester.disconnect()
    
    print("✓ Test complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())

