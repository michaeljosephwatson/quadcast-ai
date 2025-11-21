"""Test suite for transcribe.py module"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from io import BytesIO

# Mock external dependencies before importing transcribe
sys.modules['pydub'] = MagicMock()
sys.modules['pydub.AudioSegment'] = MagicMock()
sys.modules['openai'] = MagicMock()

from transcribe import (
    split_audio_2min,
    transcribe_audio
)


class TestSplitAudio2Min:
    """Test suite for split_audio_2min function"""

    @patch('transcribe.AudioSegment.from_file')
    def test_split_audio_creates_chunks(self, mock_from_file):
        """Test that audio is split into multiple chunks"""
        # Arrange
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=600000)  # 10 minutes in ms
        mock_from_file.return_value = mock_audio
        mock_audio.__getitem__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()

        # Act
        chunks = split_audio_2min("test.mp3", chunk_seconds=120)

        # Assert
        assert len(chunks) == 5  # 10 minutes / 2 minutes = 5 chunks
        assert all('index' in chunk for chunk in chunks)
        assert all('buffer' in chunk for chunk in chunks)
        assert all('duration' in chunk for chunk in chunks)

    @patch('transcribe.AudioSegment.from_file')
    def test_split_audio_chunk_structure(self, mock_from_file):
        """Test that each chunk has correct structure"""
        # Arrange
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=240000)  # 4 minutes
        mock_from_file.return_value = mock_audio
        mock_audio.__getitem__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()

        # Act
        chunks = split_audio_2min("test.mp3", chunk_seconds=120)

        # Assert
        for i, chunk in enumerate(chunks):
            assert chunk['index'] == i
            assert isinstance(chunk['buffer'], BytesIO)
            assert chunk['duration'] > 0

    @patch('transcribe.AudioSegment.from_file')
    def test_split_audio_single_chunk(self, mock_from_file):
        """Test audio shorter than chunk duration"""
        # Arrange
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=30000)  # 30 seconds
        mock_from_file.return_value = mock_audio
        mock_audio.__getitem__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()

        # Act
        chunks = split_audio_2min("test.mp3", chunk_seconds=120)

        # Assert
        assert len(chunks) == 1
        assert chunks[0]['index'] == 0

    @patch('transcribe.AudioSegment.from_file')
    def test_split_audio_custom_chunk_size(self, mock_from_file):
        """Test with custom chunk size"""
        # Arrange
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=600000)  # 10 minutes
        mock_from_file.return_value = mock_audio
        mock_audio.__getitem__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()

        # Act
        chunks = split_audio_2min("test.mp3", chunk_seconds=60)

        # Assert
        assert len(chunks) == 10  # 10 minutes / 1 minute = 10 chunks


class TestTranscribeAudio:
    """Test suite for transcribe_audio function"""

    @patch('transcribe.asyncio.run')
    def test_transcribe_audio_calls_async(self, mock_asyncio_run):
        """Test that transcribe_audio calls asyncio.run"""
        # Arrange
        mock_result = {
            'text': 'transcribed',
            'segments': []
        }
        mock_asyncio_run.return_value = mock_result

        # Act
        result = transcribe_audio("test.mp3")

        # Assert
        assert result == mock_result
        mock_asyncio_run.assert_called_once()

    @patch('transcribe.asyncio.run')
    def test_transcribe_audio_returns_dict(self, mock_asyncio_run):
        """Test that function returns correct structure"""
        # Arrange
        mock_result = {
            'text': 'full transcript',
            'segments': [
                {
                    'speaker': 'Speaker 1',
                    'start': 0.0,
                    'end': 10.0,
                    'text': 'hello'
                }
            ]
        }
        mock_asyncio_run.return_value = mock_result

        # Act
        result = transcribe_audio("test.mp3")

        # Assert
        assert 'text' in result
        assert 'segments' in result
        assert isinstance(result['segments'], list)

    @patch('transcribe.asyncio.run')
    def test_transcribe_audio_propagates_exception(self, mock_asyncio_run):
        """Test that exceptions are propagated"""
        # Arrange
        mock_asyncio_run.side_effect = Exception("Transcription error")

        # Act & Assert
        with pytest.raises(Exception, match="Transcription error"):
            transcribe_audio("test.mp3")
