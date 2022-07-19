/// @description Request NeuroPlayPro every second

get = http_get("http://127.0.0.1:2336/bci"); // Make a http-request

alarm_set(0, room_speed) // Rearm the alarm