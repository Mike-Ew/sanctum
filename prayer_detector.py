"""
Enhanced Prayer Detection Module
Supports both regex-based and OpenAI-based detection
"""

import re
from typing import List, Dict, Optional
import os

class PrayerDetector:
    def __init__(self, method="regex", openai_key=None):
        """
        Initialize prayer detector
        
        Args:
            method: "regex" or "openai"
            openai_key: OpenAI API key if using AI method
        """
        self.method = method
        self.openai_key = openai_key
        
        # Enhanced prayer patterns based on actual examples
        self.prayer_starters = [
            r'Father\s+(?:we\s+)?(?:thank|praise|ask|pray|silence|gather|bless|let)',
            r'Lord\s+(?:we\s+)?(?:thank|praise|ask|pray|come)',
            r'Dear\s+(?:God|Lord|Father)',
            r'Heavenly\s+Father',
            r'Let\s+us\s+pray',
            r'Prayer\s+Point\s*:',
            r'Personal\s+Supplication',
            r'In\s+Jesus\s+name',
            r'We\s+(?:thank|praise|worship)\s+you',
        ]
        
        # Scripture reference patterns
        self.scripture_patterns = [
            r'(?:First|Second|Third|1st|2nd|3rd|I|II|III)?\s*[A-Z][a-z]+\s+(?:chapter\s+)?\d+[\s:]+(?:verse\s+)?\d+',
            r'[A-Z][a-z]+\s+\d+:\d+',  # Simple format: Genesis 1:1
            r'Scripture\s*:\s*"?[^"]+\d+.*?"?',  # Scripture: "..."
        ]
        
        # Common biblical books for validation
        self.biblical_books = {
            'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
            'Joshua', 'Judges', 'Ruth', 'Samuel', 'Kings', 'Chronicles',
            'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Psalms', 'Proverbs',
            'Ecclesiastes', 'Song', 'Isaiah', 'Jeremiah', 'Lamentations',
            'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah',
            'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai',
            'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John',
            'Acts', 'Romans', 'Corinthians', 'Galatians', 'Ephesians',
            'Philippians', 'Colossians', 'Thessalonians', 'Timothy',
            'Titus', 'Philemon', 'Hebrews', 'James', 'Peter', 'John',
            'Jude', 'Revelation', 'Revelations'
        }
    
    def detect_prayers_regex(self, text: str) -> List[Dict]:
        """
        Detect prayers using regex patterns
        
        Returns list of dictionaries with:
        - type: "prayer" or "scripture"
        - content: the extracted text
        - start_pos: starting position in text
        """
        results = []
        
        # Normalize text for better matching
        text_normalized = re.sub(r'\s+', ' ', text)
        
        # Find prayer points
        for pattern in self.prayer_starters:
            matches = re.finditer(pattern, text_normalized, re.IGNORECASE)
            for match in matches:
                # Extract the full prayer (up to next prayer or scripture)
                start = match.start()
                
                # Find end of prayer (next prayer starter, scripture, or paragraph end)
                end_patterns = self.prayer_starters + self.scripture_patterns + [r'\n\n', r'Prayer\s+\d+:', r'Amen']
                
                end = len(text_normalized)
                for end_pattern in end_patterns:
                    next_match = re.search(end_pattern, text_normalized[start + len(match.group()):], re.IGNORECASE)
                    if next_match:
                        potential_end = start + len(match.group()) + next_match.start()
                        if potential_end < end and potential_end > start:
                            end = potential_end
                            break
                
                prayer_text = text_normalized[start:end].strip()
                
                # Only add if substantial content
                if len(prayer_text) > 20:
                    results.append({
                        'type': 'prayer',
                        'content': prayer_text,
                        'start_pos': start
                    })
        
        # Find scripture references
        for pattern in self.scripture_patterns:
            matches = re.finditer(pattern, text_normalized, re.IGNORECASE)
            for match in matches:
                scripture_text = match.group()
                
                # Validate it contains a biblical book
                has_book = any(book.lower() in scripture_text.lower() for book in self.biblical_books)
                
                if has_book or 'Scripture:' in scripture_text:
                    # Try to get the full verse if it continues
                    start = match.start()
                    end = match.end()
                    
                    # Look for quoted scripture after reference
                    quote_match = re.search(r'"([^"]+)"', text_normalized[end:end+500])
                    if quote_match:
                        scripture_text += ' "' + quote_match.group(1) + '"'
                    
                    results.append({
                        'type': 'scripture',
                        'content': scripture_text,
                        'start_pos': start
                    })
        
        # Sort by position to maintain order
        results.sort(key=lambda x: x['start_pos'])
        
        # Group prayers with their scriptures
        grouped = []
        current_prayer = None
        
        for item in results:
            if item['type'] == 'prayer':
                if current_prayer:
                    grouped.append(current_prayer)
                current_prayer = {
                    'prayer': item['content'],
                    'scripture': None
                }
            elif item['type'] == 'scripture' and current_prayer:
                current_prayer['scripture'] = item['content']
        
        if current_prayer:
            grouped.append(current_prayer)
        
        return grouped
    
    def detect_prayers_openai(self, text: str) -> List[Dict]:
        """
        Detect prayers using OpenAI API
        
        Returns list of dictionaries with prayer and scripture pairs
        """
        if not self.openai_key:
            raise ValueError("OpenAI API key required for AI detection")
        
        try:
            import openai
            openai.api_key = self.openai_key
            
            prompt = """
            Extract all prayer points and their associated scripture references from this text.
            Return as JSON array with format:
            [{"prayer": "prayer text", "scripture": "scripture reference and/or verse"}]
            
            Text:
            {text}
            """.format(text=text[:4000])  # Limit to avoid token limits
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a prayer extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            import json
            prayers = json.loads(response.choices[0].message.content)
            return prayers
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to regex
            return self.detect_prayers_regex(text)
    
    def detect(self, text: str) -> List[Dict]:
        """
        Main detection method - uses configured approach
        """
        if self.method == "openai":
            return self.detect_prayers_openai(text)
        return self.detect_prayers_regex(text)
    
    def format_for_slides(self, prayers: List[Dict], max_chars=150) -> str:
        """
        Format detected prayers for EasyWorship slides
        """
        slides = []
        
        for item in prayers:
            # Add prayer slides
            if item.get('prayer'):
                prayer_text = self.clean_text(item['prayer'])
                chunks = self.chunk_text(prayer_text, max_chars)
                slides.extend(chunks)
            
            # Add scripture slide if present
            if item.get('scripture'):
                scripture_text = self.clean_text(item['scripture'])
                slides.append(f"📖 {scripture_text}")
        
        return '\n\n'.join(slides)
    
    def clean_text(self, text: str) -> str:
        """Clean text for slides"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove timestamps
        text = re.sub(r'\[\d+:\d+\]', '', text)
        # Remove filler words
        fillers = ['um', 'uh', 'ah', 'er']
        for filler in fillers:
            text = re.sub(r'\b' + filler + r'\b', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def chunk_text(self, text: str, max_chars: int) -> List[str]:
        """Split text into slide-sized chunks"""
        words = text.split()
        chunks = []
        current = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > max_chars and current:
                chunks.append(' '.join(current))
                current = [word]
                current_length = word_length
            else:
                current.append(word)
                current_length += word_length
        
        if current:
            chunks.append(' '.join(current))
        
        return chunks


# Test function
def test_detection():
    sample_text = """
    Prayer 2:
    Prayer Point: "Father thank you for the only invasion of great multitudes into our services last Sunday and for granting each worshipper supernatural breakthroughs by your word."
    Scripture: "Psalm 115 verse1 not unto us O Lord not unto us but unto thy name give glory for thy mercy and for thy truth's sake."
    
    Prayer 3:
    Prayer Point: "Father by the blood of Jesus, let every contact made in our outreaches all through the remaining days of operation by all means surrender to Christ and be compelled to settle down in this church."
    Scripture: "Zechariah chapter 9 verse 11 as for thee also by the blood of thy covenant I have set forth thy prisoner prisoners out of the pit wherein is no water."
    """
    
    detector = PrayerDetector(method="regex")
    prayers = detector.detect(sample_text)
    
    print("Detected Prayers:")
    for i, prayer in enumerate(prayers, 1):
        print(f"\n{i}. Prayer: {prayer.get('prayer', 'N/A')[:100]}...")
        if prayer.get('scripture'):
            print(f"   Scripture: {prayer.get('scripture', 'N/A')[:100]}...")
    
    # Format for slides
    slides = detector.format_for_slides(prayers)
    print("\n\nFormatted Slides:")
    print(slides)


if __name__ == "__main__":
    test_detection()