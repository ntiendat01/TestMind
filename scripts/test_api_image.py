"""Run inside the built API image with networking disabled."""

import importlib.metadata
import unittest
from pathlib import Path


class APIImageTests(unittest.TestCase):
    def test_torch_runs_on_cpu_without_cuda_dependencies(self) -> None:
        import torch

        self.assertTrue(torch.__version__.endswith("+cpu"))
        self.assertIsNone(torch.version.cuda)
        self.assertEqual(
            (torch.tensor([[1.0, 2.0]]) @ torch.tensor([[3.0], [4.0]])).item(), 11
        )
        names = {
            dist.metadata["Name"].lower() for dist in importlib.metadata.distributions()
        }
        self.assertFalse(
            any(name.startswith(("nvidia-", "cuda-", "triton")) for name in names)
        )

    def test_embedding_library_and_api_import_without_network(self) -> None:
        from app.main import app
        from sentence_transformers import SentenceTransformer

        self.assertTrue(callable(SentenceTransformer))
        self.assertIn("/v1/eval/review/packet", app.openapi()["paths"])

    def test_download_cache_and_environment_files_are_not_baked_into_image(
        self,
    ) -> None:
        self.assertFalse(Path("/srv/.env").exists())
        self.assertEqual(list(Path("/root/.cache/uv").glob("**/*")), [])


if __name__ == "__main__":
    unittest.main()
