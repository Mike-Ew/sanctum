# Deployment Instructions for Sanctum Prayer Slides Generator

## Streamlit Cloud Deployment

### 1. Configure Secrets in Streamlit Cloud
After deploying, go to your app settings and add the following secret:

```
OPENAI_API_KEY = "your-actual-openai-api-key-here"
```

### 2. App Configuration
The app uses a purple theme (#7C3AED) configured in `.streamlit/config.toml`

### 3. Key Features
- GPT-5 support with proper API parameters
- Automatic prayer extraction from YouTube sermons
- Timestamp-based prayer detection
- EasyWorship-compatible slide generation
- 8 slides total: 4 prayers + 4 scriptures

### 4. Model Support
- GPT-5 (gpt-5, gpt-5-mini, gpt-5-nano) - No custom temperature, uses max_completion_tokens
- GPT-4 models - Uses temperature=0.1 and max_tokens
- GPT-3.5-turbo models - Uses temperature=0.1 and max_tokens

### 5. Local Development
1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Add your OpenAI API key to the secrets file
3. Run: `streamlit run app.py`

### Important Notes
- Never commit `.streamlit/secrets.toml` to git
- The `.env` file is deprecated; use Streamlit secrets instead
- The app prioritizes st.secrets over environment variables for deployment