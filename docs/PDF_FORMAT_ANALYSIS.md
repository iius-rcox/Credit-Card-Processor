# PDF Format Analysis - Cardholder Activity Report

**Date:** 2025-10-13
**Analyzed PDF:** `Cardholder+Activity+Report+General-S-89S,DD2LJ,DFRHA (6).pdf`
**Pages:** 178
**Purpose:** Identify why regex extraction returns 0 transactions

---

## Key Finding: REGEX SHOULD WORK!

The PDF format **EXACTLY MATCHES** the expected WEX Fleet format. The regex patterns are correct!

---

## Actual PDF Format

### Header Section (Lines 1-15)
```
Line  1: 'Cardholder Activity Report General'
Line  2: 'Produced On: 4/16/2025 9:25:36AM Card Token: ALL'
...
Line 14: 'Card Number: 556735XXXXXX0028 HARAHAN, LA 70123-0000'
Line 15: 'Cardholder Name: WILLIAMBURT'
```

**Employee Header Pattern:**
- ✅ FOUND: `Cardholder Name: WILLIAMBURT`
- Format matches expected: `Cardholder Name:\s*([A-Z]+)`
- **BUT:** Current regex expects space after colon, actual has space then name

### Transaction Section

**Column Headers (Line 6, Page 2):**
```
Trans Date Posted Date Lvl Transaction # Merchant Name City, State Merchant Group Product Description PPU/G Quantity Gross Cost Discount Net Cost
```

**Sample Transaction Lines:**
```
03/03/2025 03/04/2025 N 000425061 OVERHEAD DOOR COMKPEMAH, TX MISC OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS 768.22000 1.00 $768.22 $0.00 $768.22

03/04/2025 03/06/2025 F 000127739 SHELL OIL129799150 MONTGOMERY, TX FUEL UUNNLL RREEGG 8866//8877 OOCC 2.76054 13.28 $36.66 $0.00 $36.66

03/09/2025 03/11/2025 L 000196796 KROGER FUEL #7142 MONTGOMERY, TX FUEL MMIISSCC OOTTHHEERR 2.89519 -0.16 -$0.45 $0.00 -$0.45

03/26/2025 03/27/2025 N 000315304 AIR SPECIALIST HEA PEARLAND, TX MISC 523.93000 1.00 $523.93 $0.00 $523.93

02/28/2025 03/01/2025 N 000117645 TST* WALK-ON'S - B BRUSLY, LA RESTAURANTS OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS 98.86000 1.00 $98.86 $0.00 $98.86
```

---

## Format Comparison

### Expected WEX Format (from regex)
```
MM/DD/YYYY MM/DD/YYYY L NNNNNN MERCHANT_NAME, ST GROUP DESCRIPTION PPU QTY $GROSS $DISC $NET
```

### Actual Format Found
```
MM/DD/YYYY MM/DD/YYYY L NNNNNN MERCHANT_NAME CITY, ST GROUP DESCRIPTION PPU QTY $GROSS $DISC $NET
```

**Differences:**
1. ✅ Trans Date: Matches `\d{2}/\d{2}/\d{4}`
2. ✅ Posted Date: Matches `\d{2}/\d{2}/\d{4}`
3. ✅ Level: Matches `[A-Z]` (N, F, L)
4. ✅ Transaction #: Matches `\d+`
5. ⚠️ **Merchant Name:** Sometimes includes full city name, not just to first comma
   - Example: `OVERHEAD DOOR COMKPEMAH, TX` - "COMKPEMAH" looks like city merged with merchant
6. ✅ City, State: Matches `, [A-Z]{2}`
7. ✅ Merchant Group: Matches `[A-Z]+` (MISC, FUEL, RESTAURANTS, HOTELS)
8. ⚠️ **Product Description:** Has **DOUBLED CHARACTERS**
   - `OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS`
   - `UUNNLL RREEGG 8866//8877 OOCC`
   - `MMIISSCC OOTTHHEERR`
9. ✅ PPU/G: Matches `[\d,]+\.?\d*`
10. ✅ Quantity: Matches `[-]?[\d,]+\.?\d*` (can be negative!)
11. ✅ Gross Cost: Matches `\$[-]?[\d,]+\.\d{2}`
12. ✅ Discount: Matches `\$[-]?[\d,]+\.\d{2}`
13. ✅ Net Cost: Matches `\$[-]?[\d,]+\.\d{2}`

---

## CRITICAL FINDING: Product Description Has Doubled Characters

**Examples:**
- `OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS` (should be "OTHER MISCELLANEOUS TRANS")
- `UUNNLL RREEGG 8866//8877 OOCC` (should be "UNL REG 86/87 OC")
- `MMIISSCC OOTTHHEERR` (should be "MISC OTHER")

**This breaks the regex because:**
The pattern expects: `r'(.+?)\s+'` for Product Description (non-greedy match until space)

But doubled characters with spaces like `OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS` create unexpected patterns that the non-greedy matcher (`+?`) might not handle correctly with the subsequent numeric fields.

---

## Why Regex is Failing

### Current Pattern (extraction_service.py:93-108)
```python
r'^(\d{2}/\d{2}/\d{4})\s+'  # Trans Date - ✅ MATCHES
r'(\d{2}/\d{2}/\d{4})\s+'  # Posted Date - ✅ MATCHES
r'([A-Z])\s+'  # Level - ✅ MATCHES
r'(\d+)\s+'  # Transaction # - ✅ MATCHES
r'(.+?),\s*'  # Merchant Name (until comma) - ⚠️ PROBLEMATIC
r'([A-Z]{2})\s+'  # State - ✅ MATCHES
r'([A-Z]+)\s+'  # Merchant Group - ✅ MATCHES
r'(.+?)\s+'  # Product Description - ❌ FAILS due to doubled chars
r'[\d,]+\.?\d*\s+'  # PPU/G - Expected
r'[-]?[\d,]+\.?\d*\s+'  # Quantity - Expected
r'\$[-]?[\d,]+\.\d{2}\s+'  # Gross Cost - Expected
r'\$[-]?[\d,]+\.\d{2}\s+'  # Discount - Expected
r'(\$[-]?[\d,]+\.\d{2})$'  # Net Cost - Expected
```

### Specific Issues

**Issue 1: Merchant Name Capture**
```python
r'(.+?),\s*'  # Expects merchant name until first comma
```

**Actual:**
```
OVERHEAD DOOR COMKPEMAH, TX
SHELL OIL129799150 MONTGOMERY, TX
AIR SPECIALIST HEA PEARLAND, TX
```

The merchant name includes the city name before the comma! Example:
- `OVERHEAD DOOR COMKPEMAH` - where "COMKPEMAH" is the city merged with merchant

**Issue 2: Product Description with Doubled Characters**
```python
r'(.+?)\s+'  # Non-greedy match until space
```

**Actual:**
```
OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS
```

The non-greedy `+?` stops at the first space, so it would capture:
- `OOTTHHEERR` (stops at space)
- Then expects numeric PPU/G next
- But gets `MMIISSCCEELLLLAANNEEOOUUSS` instead
- **REGEX FAILS - NO MATCH**

---

## Root Cause: Product Description Field

The doubled characters in Product Description field break the regex because:

1. Pattern expects: `DESCRIPTION 123.45 1.00 $768.22`
2. Actual has: `OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS 768.22000 1.00 $768.22`
3. Non-greedy `(.+?)` captures only until first space
4. Next pattern expects numeric PPU/G
5. Gets text instead → **NO MATCH**

---

## Recommended Fixes

### Option 1: Make Product Description More Flexible (RECOMMENDED)
```python
# Change from:
r'(.+?)\s+'  # Product Description

# To:
r'((?:[A-Z]+ )*[A-Z]+)\s+'  # One or more uppercase words (handles doubled chars)
# Or even simpler:
r'(\S+(?:\s+\S+)*?)\s+(?=[\d])'  # Anything until we hit a number (lookahead)
```

### Option 2: Make Product Description Non-Capturing and Greedy
```python
# Skip the product description entirely and just consume it
r'(?:.+?)\s+'  # Non-capturing, consume until numeric field
r'([\d,]+\.?\d*)\s+'  # PPU/G (now captured)
```

### Option 3: Use Lookahead for Numeric Fields
```python
r'(.+?)\s+(?=[\d,]+\.?\d*\s+[-]?[\d,]+\.?\d*\s+\$)'  # Description until we see numeric pattern ahead
```

---

## Test Cases from Real PDF

**Transaction 1 (Normal):**
```
03/26/2025 03/27/2025 N 000315304 AIR SPECIALIST HEA PEARLAND, TX MISC 523.93000 1.00 $523.93 $0.00 $523.93
```
- No product description text (just numeric values after GROUP)

**Transaction 2 (Doubled Chars):**
```
03/28/2025 03/30/2025 N 000125718 RESIDENCE INN NO E NEW ORLEANS, LA HOTELS OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS 577.85000 1.00 $577.85 $0.00 $577.85
```
- Product desc: `OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS`

**Transaction 3 (Doubled Chars with Numbers):**
```
03/04/2025 03/06/2025 F 000127739 SHELL OIL129799150 MONTGOMERY, TX FUEL UUNNLL RREEGG 8866//8877 OOCC 2.76054 13.28 $36.66 $0.00 $36.66
```
- Product desc: `UUNNLL RREEGG 8866//8877 OOCC` (has numbers inside!)

---

## Immediate Fix Required

**File:** `backend/src/services/extraction_service.py`
**Line:** 101 (Product Description pattern)

**Change:**
```python
# CURRENT (FAILS):
r'(.+?)\s+'  # Product Description

# FIX:
r'([\sA-Z0-9/]+?)\s+(?=[\d,]+\.?\d*\s+[-]?[\d,]+)'  # Product desc (uppercase, numbers, slashes, spaces) until numeric field
```

Or simpler:
```python
r'(.+?)\s+(?=\d+\.\d+\s+[-]?\d+\.\d+\s+\$)'  # Product desc until PPU/G Quantity pattern
```

---

## Summary

**Root Cause:** Product Description field contains doubled characters and mixed content (uppercase letters, numbers, slashes, spaces) which breaks the non-greedy `(.+?)\s+` pattern because it stops too early.

**Evidence:** All other fields match perfectly - dates, level, transaction #, merchant+city, state, group all match the regex.

**Fix:** Make Product Description pattern more flexible to handle:
- Doubled characters (OO, TT, HH, etc.)
- Mixed letters and numbers
- Spaces within the description
- Variable length until numeric PPU/G field

**Impact:** Once fixed, extraction should work perfectly since all other fields already match!

---

*Analysis generated: 2025-10-13*
