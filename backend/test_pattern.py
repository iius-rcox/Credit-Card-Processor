import re

# Sample transaction line from actual WEX PDF
sample_line = '03/03/2025 03/04/2025 N 000425061 OVERHEAD DOOR COMKPEMAH, TX MISC OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS 768.22000 1.00 $768.22 $0.00 $768.22'

print("Testing regex pattern against WEX transaction line:")
print(f"Sample: {sample_line[:100]}...")
print()

# Current pattern
pattern = re.compile(
    r'^(\d{2}/\d{2}/\d{4})\s+'  # Trans Date
    r'(\d{2}/\d{2}/\d{4})\s+'  # Posted Date
    r'([A-Z])\s+'  # Level
    r'(\d+)\s+'  # Transaction #
    r'(.+?)\s+'  # Merchant
    r'([A-Z\s]+),\s*([A-Z]{2})\s+'  # City, State
    r'([A-Z]+)\s+'  # Group
    r'(.+?)\s+'  # Description
    r'[\d,]+\.?\d*\s+'  # PPU/G
    r'[-]?[\d,]+\.?\d*\s+'  # Quantity
    r'\$[-]?[\d,]+\.\d{2}\s+'  # Gross
    r'\$[-]?[\d,]+\.\d{2}\s+'  # Discount
    r'(\$[-]?[\d,]+\.\d{2})$',  # Net Cost
    re.MULTILINE
)

match = pattern.search(sample_line)
if match:
    print("MATCH FOUND!")
    print(f"Trans Date: {match.group(1)}")
    print(f"Posted Date: {match.group(2)}")
    print(f"Level: {match.group(3)}")
    print(f"Trans #: {match.group(4)}")
    print(f"Merchant: {match.group(5)}")
    print(f"City: {match.group(6)}")
    print(f"State: {match.group(7)}")
    print(f"Group: {match.group(8)}")
    print(f"Description: {match.group(9)}")
    print(f"Net Cost: {match.group(10)}")
else:
    print("NO MATCH - Pattern doesn't match the line")
    print("Trying simpler pattern to debug...")

    # Simpler pattern to see what matches
    simple = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})')
    sm = simple.search(sample_line)
    if sm:
        print(f"Dates match: {sm.group(1)}, {sm.group(2)}")
    else:
        print("Even simple date pattern doesn't match")
