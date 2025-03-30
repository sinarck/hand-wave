import cv2
import numpy as np
import mss
import time
import json
import asyncio
import websockets
import threading
import re
from ultralytics import YOLO
import os

# Global variables
latest_translation = None
processing_active = True
connected_clients = set()
last_detection_time = 0
detection_cooldown = 0.5  # Seconds between detections for performance

# Load YOLO model
model_path = "/Users/charon/Builds/sign-language-detection/runs/detect/train3/weights/best.pt"
try:
    model = YOLO(model_path)
    print(f"[INFO] YOLO model loaded from {model_path}")
except Exception as e:
    print(f"[ERROR] Failed to load YOLO model: {e}")
    model = None

# Instagram stream area coordinates
monitor = {
    "top": 70,
    "left": 260,
    "width": 480,
    "height": 780
}


# Fixed WebSocket server handler
async def handle_client(websocket):
    global connected_clients
    try:
        connected_clients.add(websocket)
        print(f"Mobile app connected! Total clients: {len(connected_clients)}")
        await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosed:
        print("Mobile app disconnected")
    finally:
        connected_clients.remove(websocket)


# Broadcast translations to all connected clients
async def broadcast_translations():
    global latest_translation, connected_clients
    previous_translation = None

    while processing_active:
        if latest_translation and latest_translation != previous_translation:
            if connected_clients:
                message = json.dumps({
                    "type": "translation",
                    "text": latest_translation,
                    "timestamp": time.time()
                })

                await asyncio.gather(
                    *[client.send(message) for client in connected_clients],
                    return_exceptions=True
                )
                print(f"Sent translation to mobile app: {latest_translation}")
                previous_translation = latest_translation
        await asyncio.sleep(0.1)


# Start WebSocket server
async def start_server():
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("WebSocket server started on port 8765")
        print("Connect your Expo app using your computer's IP address")
        broadcast_task = asyncio.create_task(broadcast_translations())
        await asyncio.Future()


# Run WebSocket server in a separate thread
def run_websocket_server():
    asyncio.run(start_server())


# Helper function to split camel case text
def split_camel_case(text):
    # Use regex to insert spaces between camel case words
    # This pattern looks for a lowercase letter followed by an uppercase letter
    # and inserts a space between them
    return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)


# ASL detection using YOLO model
def detect_asl(frame):
    global last_detection_time, model

    if model is None:
        return None

    current_time = time.time()
    if current_time - last_detection_time < detection_cooldown:
        return None

    last_detection_time = current_time

    try:
        # Run YOLO inference
        results = model(frame)

        detected_signs = []
        confidences = []

        for result in results:
            boxes = result.boxes

            if len(boxes) == 0:
                continue

            # Get class indices and confidence scores
            class_indices = boxes.cls.cpu().numpy()
            confidence_scores = boxes.conf.cpu().numpy()

            for idx, conf in zip(class_indices, confidence_scores):
                class_idx = int(idx)
                sign = model.names[class_idx]
                detected_signs.append(sign)
                confidences.append(conf)

        if detected_signs:
            best_idx = np.argmax(confidences)
            best_sign = detected_signs[best_idx]
            confidence = confidences[best_idx]

            # Split camel case text for better readability
            readable_sign = split_camel_case(best_sign)

            return f"{readable_sign} ({confidence:.2f})"

        return None

    except Exception as e:
        print(f"Error during ASL detection: {e}")
        return None


# Main function for screen capture and processing
def main():
    global latest_translation, processing_active

    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found: {model_path}")
        return

    # Start WebSocket server thread
    server_thread = threading.Thread(target=run_websocket_server, daemon=True)
    server_thread.start()

    # Initialize screen capture
    sct = mss.mss()

    print("[INFO] Starting screen capture. Press 'q' to quit.")

    frame_count = 0
    start_time = time.time()
    fps_display_time = start_time
    detection_count = 0
    current_fps = 0

    cv2.namedWindow("ASL Translator", cv2.WINDOW_NORMAL)

    try:
        while processing_active:
            # Capture the screen
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # ASL detection
            translation = detect_asl(frame)
            if translation:
                latest_translation = translation
                detection_count += 1
                print(f"Detected ASL: {translation}")

            # Create display frame
            display_frame = frame.copy()

            # Add semi-transparent overlay at the bottom for better readability
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (0, display_frame.shape[0] - 120),
                          (display_frame.shape[1], display_frame.shape[0]),
                          (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)

            # Add translation info with better styling
            if latest_translation:
                # Extract sign and confidence from the format "SIGN (0.XX)"
                parts = latest_translation.split('(')
                sign = parts[0].strip()
                conf_str = parts[1].replace(')', '') if len(parts) > 1 else "?.??"
                conf_val = float(conf_str)

                # Color coding based on confidence
                if conf_val >= 0.75:
                    color = (0, 255, 0)  # Green for high confidence
                elif conf_val >= 0.5:
                    color = (0, 255, 255)  # Yellow for medium confidence
                else:
                    color = (0, 0, 255)  # Red for low confidence

                # Draw background for sign text
                title_text = "DETECTED SIGN:"
                cv2.putText(display_frame, title_text,
                            (20, display_frame.shape[0] - 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

                # Draw the sign in large font
                cv2.putText(display_frame, sign,
                            (20, display_frame.shape[0] - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

                # Show confidence
                conf_text = f"Confidence: {conf_str}"
                cv2.putText(display_frame, conf_text,
                            (250, display_frame.shape[0] - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Show FPS and stats in top-left corner
            cv2.putText(display_frame, f"FPS: {current_fps:.1f}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Detections: {detection_count}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Add instruction text
            cv2.putText(display_frame, "Press 'q' to quit",
                        (display_frame.shape[1] - 180, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow("ASL Translator", display_frame)

            # Update performance metrics
            frame_count += 1
            current_time = time.time()
            if current_time - fps_display_time >= 1.0:
                elapsed = current_time - start_time
                current_fps = frame_count / elapsed
                print(f"[INFO] FPS: {current_fps:.1f}, Detections: {detection_count}")
                fps_display_time = current_time

            # Process key presses
            key = cv2.waitKey(5) & 0xFF
            if key == ord('q'):
                print("[INFO] Quitting...")
                break

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        # Cleanup
        cv2.destroyAllWindows()
        processing_active = False
        print(f"[INFO] Screen capture completed. Duration: {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()
