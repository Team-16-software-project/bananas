import pyrealsense2 as rs

bag_file = "C:/Users/Chen/Documents/20250214_151824.bag"
pipeline = rs.pipeline()
config = rs.config()
config.enable_device_from_file(bag_file, repeat_playback=False)
pipeline.start(config)

frame_count = 0
try:
    while True:
        frames = pipeline.wait_for_frames(timeout_ms=5000)
        frame_count += 1
except Exception as e:
    print("Finished processing frames or encountered an error:", e)
finally:
    pipeline.stop()
    print("Total frames in bag file:", frame_count)
