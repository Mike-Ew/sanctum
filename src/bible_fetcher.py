import requests
import re

def parse_scripture_reference(reference):
    """
    Parse scripture reference into book, chapter, and verse
    
    Args:
        reference: Scripture reference like "John 4:36" or "Psalm 118:23"
        
    Returns:
        Dict with book, chapter, verse or None if invalid
    """
    # Handle abbreviations
    book_abbreviations = {
        "Jn": "John",
        "Ps": "Psalms", 
        "Psalm": "Psalms",
        "Mt": "Matthew",
        "Mk": "Mark", 
        "Lk": "Luke",
        "Rom": "Romans",
        "Cor": "Corinthians",
        "Gal": "Galatians",
        "Eph": "Ephesians",
        "Phil": "Philippians",
        "Col": "Colossians",
        "Thess": "Thessalonians",
        "Tim": "Timothy",
        "Heb": "Hebrews",
        "Jas": "James",
        "Pet": "Peter",
        "Rev": "Revelation",
        "Gen": "Genesis",
        "Ex": "Exodus",
        "Lev": "Leviticus",
        "Num": "Numbers",
        "Deut": "Deuteronomy",
        "Josh": "Joshua",
        "Judg": "Judges",
        "Sam": "Samuel",
        "Kgs": "Kings",
        "Chr": "Chronicles",
        "Neh": "Nehemiah",
        "Prov": "Proverbs",
        "Eccl": "Ecclesiastes",
        "Isa": "Isaiah",
        "Jer": "Jeremiah",
        "Lam": "Lamentations",
        "Ezek": "Ezekiel",
        "Dan": "Daniel",
        "Hos": "Hosea",
        "Hab": "Habakkuk"
    }
    
    # Pattern to match scripture references
    # Handles: "John 3:16", "1 John 3:16", "Psalm 23:1-3", etc.
    pattern = r"^(\d?\s*\w+)\s+(\d+):(\d+)(?:-(\d+))?$"
    
    match = re.match(pattern, reference.strip())
    if not match:
        return None
    
    book = match.group(1).strip()
    chapter = match.group(2)
    verse_start = match.group(3)
    verse_end = match.group(4)
    
    # Expand abbreviations
    for abbr, full in book_abbreviations.items():
        if book.lower().startswith(abbr.lower()):
            book = book.lower().replace(abbr.lower(), full, 1)
            break
    
    # Capitalize book name properly
    book = book.title()
    
    return {
        "book": book,
        "chapter": chapter,
        "verse_start": verse_start,
        "verse_end": verse_end,
        "full_reference": f"{book} {chapter}:{verse_start}" + (f"-{verse_end}" if verse_end else "")
    }

def fetch_verse(reference, translation="kjv"):
    """
    Fetch Bible verse text from free Bible API
    
    Args:
        reference: Scripture reference like "John 4:36"
        translation: Bible translation (default: kjv)
        
    Returns:
        Dict with verse text and reference or error message
    """
    try:
        # Parse the reference
        parsed = parse_scripture_reference(reference)
        if not parsed:
            return {
                "error": f"Could not parse reference: {reference}",
                "text": None,
                "reference": reference
            }
        
        # Format for Bible-API.com
        # Example: https://bible-api.com/john+3:16?translation=kjv
        book = parsed["book"].replace(" ", "+")
        chapter = parsed["chapter"]
        verse_start = parsed["verse_start"]
        verse_end = parsed.get("verse_end", "")
        
        if verse_end:
            verse_ref = f"{chapter}:{verse_start}-{verse_end}"
        else:
            verse_ref = f"{chapter}:{verse_start}"
        
        url = f"https://bible-api.com/{book}+{verse_ref}"
        params = {"translation": translation}
        
        # Make request
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract verse text
            verse_text = data.get("text", "").strip()
            
            # Clean up text (remove extra spaces and newlines)
            verse_text = " ".join(verse_text.split())
            
            return {
                "text": verse_text,
                "reference": data.get("reference", reference),
                "translation": translation.upper(),
                "error": None
            }
        else:
            return {
                "error": f"API error: {response.status_code}",
                "text": None,
                "reference": reference
            }
            
    except requests.RequestException as e:
        return {
            "error": f"Network error: {str(e)}",
            "text": None,
            "reference": reference
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "text": None,
            "reference": reference
        }

def fetch_multiple_verses(references, translation="kjv"):
    """
    Fetch multiple Bible verses
    
    Args:
        references: List of scripture references
        translation: Bible translation (default: kjv)
        
    Returns:
        List of verse dictionaries
    """
    results = []
    for ref in references:
        if ref:  # Skip empty references
            result = fetch_verse(ref, translation)
            results.append(result)
    
    return results

# Test function
if __name__ == "__main__":
    # Test verses
    test_refs = [
        "John 4:36",
        "Psalm 118:23",
        "Habakkuk 3:2",
        "Ezekiel 34:25"
    ]
    
    print("Testing Bible API fetcher...")
    for ref in test_refs:
        result = fetch_verse(ref)
        if result["error"]:
            print(f"❌ {ref}: {result['error']}")
        else:
            print(f"✅ {ref}: {result['text'][:100]}...")