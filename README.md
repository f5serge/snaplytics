# 📸 Spanlytics

Spanlytics is a desktop application that allows users to capture screen areas, extract numerical data from images, and generate instant statistical summaries.

## Features

- 🖼️ Screen area capture functionality
- 🔢 Optical Character Recognition (OCR) for number extraction
- 📊 Real-time statistical analysis
- 📋 Copy results to clipboard
- 💾 Save captured data for later use

## How It Works

1. Select the screen area containing numbers
2. Spanlytics automatically captures and processes the image
3. Numbers are extracted using OpenAI API
4. View instant statistical summary (sum, average, etc.)

## Installation

```bash
# Clone the repository
git clone https://github.com/f5serge/snaplytics.git

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

## Requirements

- Python 3.8+
- OpenAI API key
- Additional dependencies listed in `requirements.txt`

## Tech Stack

- Python
- PyQt6 (GUI Framework)
- OpenAI API (OCR and AI)
- OpenCV (Image Processing)
- NumPy (Numerical Operations)

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
