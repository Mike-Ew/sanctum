# Prayer Slides Generator

A lightweight web app to generate EasyWorship-ready prayer slides from YouTube sermon transcripts.

## Features

- 🎥 **YouTube Integration**: Automatically fetches transcripts from YouTube videos
- 🙏 **Smart Prayer Detection**: Identifies prayer sections using keywords
- 🧹 **Text Cleaning**: Removes timestamps, fillers, and cleans formatting
- 📊 **Intelligent Chunking**: Splits text into slide-sized segments
- 📥 **EasyWorship Ready**: Outputs formatted `.txt` file for direct import

## Quick Start

### Installation

1. Clone or download this project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## How to Use

1. **Paste YouTube URL**: Enter the link to a sermon or service video
2. **Adjust Settings**: 
   - Max characters per slide (100-400)
   - Max lines per slide (2-6)
3. **Generate**: Click "Generate Prayer Slides"
4. **Preview**: Review the extracted and formatted slides
5. **Download**: Save the `prayer_slides.txt` file
6. **Import to EasyWorship**: Each paragraph becomes a slide

## Prayer Detection Keywords

The app looks for these keywords to identify prayer sections:
- "Let us pray" / "Let's pray"
- "Father we" / "Lord we"
- "Dear God" / "Dear Lord"
- "Heavenly Father"
- "We pray" / "We thank you"
- "In Jesus name"
- "Amen"

## Requirements

- Python 3.7+
- Internet connection (for YouTube access)
- YouTube videos must have captions/transcripts available

## Troubleshooting

**No transcript found:**
- Ensure the video has captions enabled
- Check if the video is public/not age-restricted

**No prayers detected:**
- The sermon may not contain explicit prayer sections
- Try a different video with clear prayer moments

## Future Enhancements

- [ ] AI-powered prayer detection for better accuracy
- [ ] ProPresenter integration
- [ ] Multi-language support
- [ ] Batch processing for multiple videos
- [ ] Custom keyword configuration

## License

MIT License - Feel free to use and modify for your church needs!