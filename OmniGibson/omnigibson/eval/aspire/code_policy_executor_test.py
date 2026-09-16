from __future__ import annotations

from omnigibson.eval.aspire.code_policy_executor import AspireCodePolicyExecutor, extract_code_blocks


def test_extract_and_persistent_blocks() -> None:
    source = """# Code block 1\nvalue = 3\n# Code block 2\nRESULT = value + 4\n"""
    assert extract_code_blocks(source) == ["value = 3", "RESULT = value + 4"]
    executor = AspireCodePolicyExecutor({})
    result = executor.run_source(source)
    assert [item.ok for item in result] == [True, True]
    assert result[-1].result == 7


def test_failed_block_stops_replay() -> None:
    executor = AspireCodePolicyExecutor({})
    result = executor.run_source("# Code block 1\nraise RuntimeError('boom')\n# Code block 2\nRESULT = 1")
    assert len(result) == 1
    assert not result[0].ok
    assert "RuntimeError" in result[0].stderr


def test_preamble_is_executed_before_first_block() -> None:
    executor = AspireCodePolicyExecutor({})
    blocks = executor.run_source("import math\n# Code block 1\nRESULT = math.sqrt(9)")
    assert blocks[0].ok
    assert blocks[0].result == 3
