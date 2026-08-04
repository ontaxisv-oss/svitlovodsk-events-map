import sys
sys.path.insert(0, r'C:\Users\chmak\.gemini\antigravity\scratch\svitlovodsk-events-map')
import parser

test_msgs = [
    'авария на детском мире',
    'пробка на героев',
    'все хорошо на ревдамбе',
    'затор центр',
    'ДТП вул леніна',
    'ревдамба проблема',
]
for msg in test_msgs:
    status = parser.detect_status(msg)
    loc, lat, lng = parser.detect_location(msg)
    print(f'[{status}] "{msg}" -> {loc} ({lat:.4f}, {lng:.4f})')
