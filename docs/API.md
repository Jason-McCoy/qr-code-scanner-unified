# API Reference

## QRScanner

Core scanning engine using OpenCV and pyzbar.

### Initialization

```python
from shared import QRScanner

scanner = QRScanner(camera_index=0)
```

### Methods

#### `start() -> bool`
Start the camera and scanner.

```python
if scanner.start():
    print("Scanner ready")
else:
    print("Failed to start scanner")
```

#### `stop()`
Stop the camera and scanner.

```python
scanner.stop()
```

#### `capture_frame() -> Optional[np.ndarray]`
Capture a single frame from camera.

```python
frame = scanner.capture_frame()
if frame is not None:
    print(f"Frame shape: {frame.shape}")
```

#### `scan_frame(frame: np.ndarray) -> List[ScanResult]`
Scan a single frame for QR codes.

```python
import cv2
from shared import QRScanner

scanner = QRScanner()
image = cv2.imread("image.jpg")
results = scanner.scan_frame(image)

for result in results:
    print(f"Found: {result.data}")
```

#### `scan_continuous(callback=None, duration=None) -> List[ScanResult]`
Continuously scan for QR codes until stopped.

```python
def on_scan(results):
    for result in results:
        print(f"Scanned: {result.data}")

all_results = scanner.scan_continuous(
    callback=on_scan,
    duration=60  # 60 seconds max
)
```

#### `scan_image_file(image_path: str) -> List[ScanResult]`
Scan a QR code from an image file.

```python
results = scanner.scan_image_file("qr_code.png")
for result in results:
    print(result.to_dict())
```

#### `draw_detections(frame, results) -> np.ndarray`
Draw QR code detections on frame.

```python
frame = scanner.capture_frame()
results = scanner.scan_frame(frame)
annotated = scanner.draw_detections(frame, results)

cv2.imshow("Detections", annotated)
```

#### `get_status() -> Dict`
Get current scanner status.

```python
status = scanner.get_status()
print(status)
# Output:
# {
#     'is_running': True,
#     'camera_index': 0,
#     'last_scan_time': '2026-08-29T12:00:00'
# }
```

## ScanResult

Represents a single QR code detection.

### Attributes

```python
result = ScanResult(
    data="https://example.com",
    format="QRCODE",
    timestamp=datetime.now(),
    image_data=None,  # Optional: image bytes
    rect=(x, y, width, height)  # Optional: detection coordinates
)
```

### Methods

#### `to_dict() -> Dict`
Convert to dictionary representation.

```python
result_dict = result.to_dict()
print(result_dict)
# Output:
# {
#     'data': 'https://example.com',
#     'format': 'QRCODE',
#     'timestamp': '2026-08-29T12:00:00.000000',
#     'rect': [100, 100, 50, 50]
# }
```

## DataManager

Handles persistence and retrieval of scan results.

### Initialization

```python
from shared import DataManager

manager = DataManager(db_path="./data/qr_scanner.db")
```

### Methods

#### `save_scan(result, tags=None, notes=None) -> Optional[int]`
Save a scan result to database.

```python
scan_id = manager.save_scan(
    result,
    tags=["github", "project"],
    notes="Important QR code"
)

if scan_id:
    print(f"Saved with ID: {scan_id}")
```

#### `save_scans_batch(results: List[ScanResult]) -> int`
Save multiple scans in batch.

```python
count = manager.save_scans_batch(scan_results)
print(f"Saved {count} scans")
```

#### `get_scan(scan_id: int) -> Optional[Dict]`
Retrieve a specific scan.

```python
scan = manager.get_scan(1)
if scan:
    print(scan['data'])
```

#### `get_all_scans(limit=100, offset=0) -> List[Dict]`
Retrieve all scans with pagination.

```python
# Get first 10 scans
scans = manager.get_all_scans(limit=10, offset=0)

# Get next 10 scans
more_scans = manager.get_all_scans(limit=10, offset=10)

for scan in scans:
    print(f"ID: {scan['id']}, Data: {scan['data']}")
```

#### `search_scans(query: str, limit=50) -> List[Dict]`
Search scans by content.

```python
results = manager.search_scans("github")
for result in results:
    print(result['data'])
```

#### `get_stats() -> Dict`
Get database statistics.

```python
stats = manager.get_stats()
print(stats)
# Output:
# {
#     'total_scans': 42,
#     'formats': ['QRCODE', 'CODE128'],
#     'database_path': './data/qr_scanner.db'
# }
```

#### `export_json(output_path: str, limit=1000) -> bool`
Export scans to JSON file.

```python
if manager.export_json("scans.json"):
    print("Exported successfully")
```

#### `export_csv(output_path: str, limit=1000) -> bool`
Export scans to CSV file.

```python
if manager.export_csv("scans.csv"):
    print("Exported successfully")
```

#### `clear_old_scans(days: int) -> int`
Delete scans older than specified days.

```python
deleted = manager.clear_old_scans(days=30)
print(f"Deleted {deleted} old scans")
```

#### `close()`
Close database connection.

```python
manager.close()
```

## Config

Centralized configuration management.

### Usage

```python
from shared import Config

print(Config.APP_NAME)      # "QR Code Scanner Unified"
print(Config.CAMERA_INDEX)  # 0
print(Config.DB_PATH)       # Path to database
print(Config.AUTO_SAVE)     # True
```

### Common Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | str | "QR Code Scanner Unified" | Application name |
| `APP_VERSION` | str | "1.0.0" | Application version |
| `CAMERA_INDEX` | int | 0 | Camera device index |
| `SCAN_TIMEOUT` | int | 30 | Max scan duration (seconds) |
| `AUTO_SAVE` | bool | True | Auto-save scans |
| `DEBUG_MODE` | bool | False | Enable debug output |
| `DB_PATH` | Path | `./data/qr_scanner.db` | Database location |
| `DATA_DIR` | Path | `./data` | Data directory |

## Usage Examples

### Basic Scanning

```python
from shared import QRScanner, DataManager

scanner = QRScanner()
manager = DataManager()

# Scan for 30 seconds
results = scanner.scan_continuous(duration=30)

# Save all results
for result in results:
    manager.save_scan(result)

manager.close()
```

### Continuous Scanning with Callback

```python
from shared import QRScanner, DataManager

scanner = QRScanner()
manager = DataManager()

def on_scan(results):
    for result in results:
        scan_id = manager.save_scan(result)
        print(f"Saved: {result.data}")

scanner.scan_continuous(callback=on_scan)
manager.close()
```

### Searching and Exporting

```python
from shared import DataManager

manager = DataManager()

# Search for GitHub URLs
results = manager.search_scans("github")
print(f"Found {len(results)} GitHub scans")

# Export to JSON
manager.export_json("github_scans.json")

# Get statistics
stats = manager.get_stats()
print(f"Total scans: {stats['total_scans']}")

manager.close()
```
