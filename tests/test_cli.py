import os
import unittest
from unittest.mock import patch

from agent_course.cli import ConfigurationError, build_model
from agent_course.mock_model import MockModel
from agent_course.openai_compatible import OpenAICompatibleModel


class BuildModelTests(unittest.TestCase):
    def test_missing_api_configuration_uses_mock_model(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            model = build_model()

        self.assertIsInstance(model, MockModel)

    def test_complete_api_configuration_uses_remote_model(self) -> None:
        environment = {
            "MODEL_BASE_URL": "https://example.test/v1",
            "MODEL_API_KEY": "test-key",
            "MODEL_NAME": "demo-model",
        }
        with patch.dict(os.environ, environment, clear=True):
            model = build_model()

        self.assertIsInstance(model, OpenAICompatibleModel)

    def test_partial_api_configuration_is_rejected(self) -> None:
        with patch.dict(os.environ, {"MODEL_API_KEY": "test-key"}, clear=True):
            with self.assertRaises(ConfigurationError):
                build_model()

    def test_empty_api_configuration_is_rejected(self) -> None:
        environment = {
            "MODEL_BASE_URL": "",
            "MODEL_API_KEY": "",
            "MODEL_NAME": "",
        }
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(ConfigurationError):
                build_model()


if __name__ == "__main__":
    unittest.main()
