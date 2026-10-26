"""Regression tests for one-command local game shipping."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ai_factory.cli import main


class ShipWorkflowTests(unittest.TestCase):
    def _invoke(self, qa):
        with tempfile.TemporaryDirectory() as root:
            out=io.StringIO()
            with (patch("ai_factory.core.new",return_value={"requirements":[{"prompt":"3D RPG","resolution":"PARTIAL_TEMPLATE_SUPPORT"}]}) as create,
                  patch("ai_factory.core.build",return_value={"status":"IMPLEMENTED"}) as build,
                  patch("ai_factory.core.test",**({"side_effect":qa} if isinstance(qa,Exception) else {"return_value":qa})) as test,
                  contextlib.redirect_stdout(out)):
                code=main(["--workspace",root,"ship","--name","Demo","--prompt","3D RPG"])
                create.assert_called_once()
                build.assert_called_once()
                test.assert_called_once()
            return code,json.loads(out.getvalue())

    def test_ship_success_exposes_review_limits(self):
        code,result=self._invoke({"status":"RUNTIME_CHECKED"})
        self.assertEqual(code,0)
        self.assertEqual(result["status"],"RUNTIME_CHECKED")
        self.assertEqual(result["visual_review"],"PENDING")
        self.assertEqual(result["production_art"],"BLOCKED")
        self.assertTrue(result["zip"].endswith("Demo.zip"))

    def test_missing_engine_does_not_claim_shipped_zip(self):
        code,result=self._invoke(ValueError("BLOCKED: Godot4.2+ unavailable"))
        self.assertEqual(code,0)
        self.assertEqual(result["status"],"BUILT_QA_BLOCKED")
        self.assertNotIn("zip",result)
        self.assertIn("Godot",result["reason"])

if __name__=="__main__":
    unittest.main()
