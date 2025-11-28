"""
Reference ID Manager
Handles reference ID generation and validation for loan entries.
"""

import re
from DatabaseManager import DatabaseManager

# ===== CUSTOMIZABLE VARIABLES (Lines 10-15) =====
# Format pattern: {reference_id}-{year_suffix}{sequence}
YEAR_DIGITS = 2  # Use 2 digits for year (25 for 2025)
SEQUENCE_PADDING = 2  # Pad sequence with zeros (01, 02, etc.)
SEPARATOR = "-"  # Separator between reference ID and suffix
USE_FULL_YEAR = False  # If True, uses 2025 instead of 25
# ================================================


def generate_next_reference_id(base_reference_id):
    """
    Generates the next reference ID with year and sequence suffix.
    
    Args:
        base_reference_id (str): The base reference ID entered by user (e.g., "xyz")
    
    Returns:
        str: Full reference ID with suffix (e.g., "xyz-2501")
    
    Line: 19-74
    """
    from datetime import datetime
    
    # Get current year
    current_year = datetime.now().year
    if USE_FULL_YEAR:
        year_suffix = str(current_year)
    else:
        year_suffix = str(current_year)[-YEAR_DIGITS:]
    
    # Query database for existing reference IDs with this base
    db = DatabaseManager.get_connection()
    cursor = db.cursor()
    
    # Pattern to match: base_reference_id-{year_suffix}{sequence}
    pattern = f"{base_reference_id}{SEPARATOR}{year_suffix}%"
    
    cursor.execute("""
        SELECT reference_id FROM loans 
        WHERE reference_id LIKE ?
        ORDER BY reference_id DESC
    """, (pattern,))
    
    existing_ids = cursor.fetchall()
    
    # Filter valid IDs using validator and extract sequences
    valid_sequences = []
    for (ref_id,) in existing_ids:
        if is_valid_new_pattern(ref_id, base_reference_id):
            # Extract sequence number from the end
            suffix = ref_id.split(SEPARATOR)[-1]
            if len(suffix) > len(year_suffix):
                sequence_str = suffix[len(year_suffix):]
                try:
                    valid_sequences.append(int(sequence_str))
                except ValueError:
                    continue
    
    # Determine next sequence number
    if valid_sequences:
        next_sequence = max(valid_sequences) + 1
    else:
        next_sequence = 1
    
    # Format with padding
    sequence_str = str(next_sequence).zfill(SEQUENCE_PADDING)
    
    # Construct full reference ID
    full_reference_id = f"{base_reference_id}{SEPARATOR}{year_suffix}{sequence_str}"
    
    return full_reference_id


def is_valid_new_pattern(reference_id, base_reference_id=None):
    """
    Validates if a reference ID follows the new pattern.
    
    Pattern: {base}{SEPARATOR}{year_digits}{sequence_digits}
    Example: "xyz-2501" where xyz is base, 25 is year, 01 is sequence
    
    Args:
        reference_id (str): The reference ID to validate
        base_reference_id (str, optional): Expected base reference ID
    
    Returns:
        bool: True if valid, False otherwise
    
    Line: 78-130
    """
    if not reference_id or not isinstance(reference_id, str):
        return False
    
    # Check if separator exists
    if SEPARATOR not in reference_id:
        return False
    
    parts = reference_id.split(SEPARATOR)
    
    # Should have exactly 2 parts (base and suffix)
    if len(parts) != 2:
        return False
    
    base, suffix = parts
    
    # If base_reference_id is provided, check if it matches
    if base_reference_id and base != base_reference_id:
        return False
    
    # Validate suffix format
    # Should be: year_digits + sequence_digits
    year_length = 4 if USE_FULL_YEAR else YEAR_DIGITS
    expected_min_length = year_length + 1  # At least 1 digit for sequence
    
    if len(suffix) < expected_min_length:
        return False
    
    # Check if suffix contains only digits
    if not suffix.isdigit():
        return False
    
    # Extract year part
    year_part = suffix[:year_length]
    
    # Validate year (should be reasonable)
    try:
        year_value = int(year_part)
        from datetime import datetime
        current_year = datetime.now().year
        if USE_FULL_YEAR:
            if year_value < 2000 or year_value > current_year + 10:
                return False
        else:
            current_year_short = int(str(current_year)[-YEAR_DIGITS:])
            if year_value > current_year_short + 10:
                return False
    except ValueError:
        return False
    
    return True


def get_all_legacy_reference_ids():
    """
    Retrieves all reference IDs from database that don't follow the new pattern.
    These are considered legacy entries.
    
    Returns:
        list: List of legacy reference IDs
    
    Line: 134-150
    """
    db = DatabaseManager.get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT DISTINCT reference_id FROM loans")
    all_ids = cursor.fetchall()
    
    legacy_ids = []
    for (ref_id,) in all_ids:
        if not is_valid_new_pattern(ref_id):
            legacy_ids.append(ref_id)
    
    return legacy_ids
