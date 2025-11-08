# Chef AI - YouTube Transcript Training

Train a specialized AI assistant on chef YouTube channel transcripts to create an intelligent culinary advisor.

## Overview

This project provides a complete pipeline for:
- Processing YouTube transcript data from chef channels
- Fine-tuning language models on culinary content
- Deploying an interactive chef AI assistant

## Project Structure

```
.
├── data/
│   ├── raw/
│   │   └── transcripts/         # Place your raw transcript files here
│   └── processed/
│       ├── cleaned/             # Cleaned and processed transcripts
│       ├── embeddings/          # Generated embeddings
│       └── fine_tuning/         # Data formatted for fine-tuning
├── src/
│   ├── data_processing/         # Transcript processing modules
│   ├── training/                # Model training modules
│   └── inference/               # Inference and chat interface
├── models/
│   ├── checkpoints/             # Training checkpoints
│   └── final/                   # Final trained models
├── notebooks/                   # Jupyter notebooks for exploration
├── config/                      # Configuration files
├── tests/                       # Unit tests
└── scripts/                     # Utility scripts
```

## Getting Started

### 1. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Transcript Data

Place your transcript files in `data/raw/transcripts/`. Supported formats:
- `.txt` files
- `.md` (Markdown) files
- `.json` files

You can organize transcripts by channel:
```
data/raw/transcripts/
├── channel_name_1/
│   ├── video1.txt
│   └── video2.txt
└── channel_name_2/
    ├── video1.txt
    └── video2.txt
```

**Importing from Obsidian:**

If you have transcripts in an Obsidian vault, use the import script:

```bash
python scripts/import_obsidian.py /path/to/your/obsidian/vault --subfolder "chef-transcripts"
```

This will:
- Extract content from Obsidian markdown files
- Remove Obsidian-specific syntax (wiki links, tags)
- Preserve metadata from frontmatter
- Save clean transcripts to `data/raw/transcripts/`

### 3. Process Transcripts

```bash
# Run the transcript processor
python src/data_processing/transcript_processor.py
```

This will:
- Load all transcript files
- Clean and normalize text
- Extract metadata
- Save processed data to `data/processed/cleaned/processed_transcripts.jsonl`

### 4. Train the Model

```bash
# Run the training pipeline
python src/training/fine_tuner.py
```

Configure training parameters in `config/training_config.yaml` or modify the `TrainingConfig` dataclass.

### 5. Use the Chef AI Assistant

```bash
# Start interactive chat
python src/inference/chef_assistant.py
```

## Configuration

Edit `config/training_config.yaml` to customize:
- Model selection (GPT-2, GPT-J, LLaMA, etc.)
- Training hyperparameters
- Data processing options
- Output paths

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Features

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run tests: `pytest`
4. Submit pull request

## Scripts

### Import from Obsidian
```bash
python scripts/import_obsidian.py <vault_path> [--subfolder <folder>] [--pattern "**/*.md"]
```

### Download YouTube Transcripts
```bash
# Single video
python scripts/download_transcripts.py --video-id <VIDEO_ID>

# Entire channel
python scripts/download_transcripts.py --channel-id <CHANNEL_ID> [--max-videos 100]
```

## Roadmap

- [ ] Add support for automatic YouTube transcript download
- [ ] Implement recipe extraction from transcripts
- [ ] Add vector database for semantic search
- [ ] Create web interface for the assistant
- [ ] Support for multiple languages
- [ ] Integration with cooking APIs

## Dependencies

Key dependencies:
- `transformers` - Hugging Face transformers library
- `torch` - PyTorch for model training
- `datasets` - Dataset processing
- `tokenizers` - Fast tokenization
- `accelerate` - Distributed training support

See `requirements.txt` for complete list.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Troubleshooting

### Common Issues

**Out of Memory during training:**
- Reduce `batch_size` in training config
- Reduce `max_length` for sequences
- Use gradient accumulation

**Transcripts not being found:**
- Check file format (.txt, .md, .json)
- Verify files are in `data/raw/transcripts/`
- Check file encoding (should be UTF-8)

**Obsidian import issues:**
- Ensure vault path is correct
- Check file permissions
- Verify subfolder exists if specified

## Acknowledgments

Built for training on culinary knowledge from YouTube chef channels.
