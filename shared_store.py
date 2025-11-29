# Shared memory stores for inter-module communication

# Cache for Base64 encoded image data (key: UUID, value: Base64 string)
BASE64_STORE = {}

# Timestamp tracker for URL processing (key: URL, value: timestamp)
url_time = {}