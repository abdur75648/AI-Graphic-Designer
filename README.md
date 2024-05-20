# AI Graphic Designer
An AI-powered graphic design tool that generates customized logos based on user input.

**Features:**
- Generates professional and customized logos based on user input
- Leverages OpenAI's API for detailed prompt generation
- Automated interaction with MidJoy's Discord bot using Playwright library
- Dynamic text placement using Fabric.js library

## Setup

### Credentials
1. Set environment variables for the OpenAI API key
    ```bash
    export OPENAI_API_KEY=your_openai_api_key
    ```

2. Set the environment variable for the Discord Email and Password
    ```bash
    export DISCORD_EMAIL=your_discord_email
    export DISCORD_PASSWORD=your_discord_password
    ```

### Installations

```bash
npm install
pip install playwright==1.35.0
playwright install
pip install loguru==0.7.2
```

## Running

```bash
bash run.sh
```
