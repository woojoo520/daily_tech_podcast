# Audio Generation Service

This project provides a fast service to generate audio from text using a specified API. It allows users to send text via a POST request, generates audio files, saves them locally, and uploads them to a GitHub repository.

## Project Structure

```
audio-gen-service
├── src
│   ├── main.py          # Entry point of the application
│   ├── api.py           # API routes and request handling
│   ├── audio_generator.py # Audio generation logic
│   ├── github_uploader.py # Uploads audio files to GitHub
│   └── config.py        # Configuration settings
├── requirements.txt      # Project dependencies
├── .gitignore            # Files to ignore in Git
└── README.md             # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd audio-gen-service
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your API endpoint and GitHub repository details in `src/config.py`.

## Usage

To run the service, execute the following command:
```
python src/main.py
```

You can send a POST request to the API endpoint to generate audio from text. The expected JSON format is:
```json
{
  "text": "Your text here"
}
```

## API Endpoint

- **POST /generate-audio**: Generates audio from the provided text.

## Uploading to GitHub

After generating audio files, they will be automatically uploaded to the specified GitHub repository using the provided token in the configuration.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.