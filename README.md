# Sanctum - Prayer Slides Generator

Generate EasyWorship-ready prayer slides directly from YouTube sermon transcripts.

## Features

- 🎬 Automatic transcript fetching from YouTube videos
- 🙏 Intelligent prayer detection using keywords
- 🧹 Text cleaning (removes timestamps, fillers)
- 📄 Smart chunking into slide-sized segments
- 💾 Export as EasyWorship-compatible .txt file

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Mike-Ew/sanctum.git
cd sanctum

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. **Paste YouTube URL**: Copy the full URL of the sermon video
2. **Click Generate**: The app fetches the transcript and extracts prayers
3. **Download slides.txt**: Save the generated file
4. **Import to EasyWorship**:
   - Open EasyWorship
   - Go to Songs > Import
   - Select the slides.txt file
   - Each paragraph becomes a slide

## How It Works

1. **Transcript Fetching**: Uses `youtube-transcript-api` to pull captions
2. **Prayer Detection**: Identifies prayer sections using keywords like:
   - "let us pray"
   - "Father we thank you"
   - "in Jesus name"
   - "amen"
3. **Text Cleaning**: Removes timestamps, filler words, and formatting issues
4. **Smart Chunking**: Splits text into slide-friendly segments (customizable)
5. **Export**: Formats with blank lines between slides for EasyWorship

## Configuration

Adjust settings in the app:
- **Max characters per slide**: 50-300 (default: 150)
- **Max lines per slide**: 2-6 (default: 4)

## Requirements

- Python 3.8+
- Internet connection for YouTube transcript fetching

## Future Enhancements

- [ ] LLM integration for better prayer detection
- [ ] ProPresenter support
- [ ] Transcript archive system
- [ ] Multi-language support
- [ ] Custom prayer keywords configuration

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.