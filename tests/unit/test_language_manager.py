"""
Unit tests for language manager (src/utils/language_manager.py).
"""

import pytest
import json
from pathlib import Path
from src.utils.language_manager import LanguageManager


class TestLanguageManagerInit:
    """Tests for LanguageManager initialization."""

    def test_default_language_is_english(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        assert lm.current_language == "en"

    def test_translations_loaded(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        assert len(lm.translations) > 0


class TestLanguageManagerSetLanguage:
    """Tests for LanguageManager.set_language method."""

    def test_set_to_chinese(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.set_language("zh")
        assert lm.current_language == "zh"

    def test_set_to_english(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.set_language("zh")
        lm.set_language("en")
        assert lm.current_language == "en"

    def test_invalid_language_ignored(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.set_language("fr")
        assert lm.current_language == "en"

    def test_same_language_no_change(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.set_language("en")
        assert lm.current_language == "en"


class TestLanguageManagerToggle:
    """Tests for LanguageManager.toggle_language method."""

    def test_toggle_en_to_zh(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.toggle_language()
        assert lm.current_language == "zh"

    def test_toggle_zh_to_en(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.set_language("zh")
        lm.toggle_language()
        assert lm.current_language == "en"


class TestLanguageManagerTranslation:
    """Tests for LanguageManager.tr method."""

    def test_simple_translation_en(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        assert lm.tr("toolbar.refresh") == "Refresh"

    def test_simple_translation_zh(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.set_language("zh")
        assert lm.tr("toolbar.refresh") == "刷新"

    def test_translation_with_variable(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        result = lm.tr("dialogs.delete_confirm", count=3)
        assert "3" in result

    def test_missing_key_returns_key(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        assert lm.tr("nonexistent.key") == "nonexistent.key"


class TestLanguageManagerGetName:
    """Tests for LanguageManager.get_language_name method."""

    def test_english_name(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        assert lm.get_language_name() == "English"

    def test_chinese_name(self, mock_i18n_dir, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: mock_i18n_dir.parent)
        lm = LanguageManager()
        lm.i18n_dir = mock_i18n_dir
        lm.load_translations()
        lm.set_language("zh")
        assert lm.get_language_name() == "中文"
