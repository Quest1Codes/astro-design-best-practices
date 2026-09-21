import pytest

from autosys_jil.conditions import ConditionParseError, parse, try_parse


def test_single_status():
    ast = parse("success(job_a)")
    assert ast.shape == "single"
    assert ast.referenced_job_names == ["job_a"]
    assert ast.functions_used == ["success"]


def test_short_form_functions():
    for short, long_ in [("s", "success"), ("f", "failure"), ("d", "done"),
                         ("n", "notrunning"), ("t", "terminated")]:
        ast = parse(f"{short}(job_a)")
        assert ast.functions_used == [long_]


def test_and_only():
    ast = parse("success(a) AND success(b)")
    assert ast.shape == "and_only"
    assert ast.clause_count == 2


def test_or_present():
    ast = parse("success(a) OR success(b)")
    assert ast.shape == "or_present"
    assert ast.has_or


def test_nested_parentheses_and_case_insensitive_boolean_ops():
    ast = parse("(success(a) and success(b)) or failure(c)")
    assert ast.shape == "nested"
    assert ast.depth >= 2


def test_lookback_hhmm():
    ast = parse("failure(JobA,00.30) AND success(JobC^XYZ,01.30)")
    assert set(ast.lookbacks) == {"00.30", "01.30"}
    assert ast.cross_instance_refs == ["JobC^XYZ"]


def test_exitcode_function_pdf_example():
    ast = parse("exitcode(my_job2,12)=4")
    node = ast.leaves[0]
    assert node.op == "=" and node.value == 4 and node.lookback == "12"


def test_value_function_pdf_example():
    ast = parse("VALUE(TODAY)=Friday")
    node = ast.leaves[0]
    assert node.global_name == "TODAY" and node.op == "=" and node.literal == "Friday"


def test_cross_instance_job_ref():
    ast = parse("success(job_a^PRD)")
    ref = ast.leaves[0].ref
    assert ref.job == "job_a" and ref.instance == "PRD"
    assert ast.cross_instance_refs == ["job_a^PRD"]


@pytest.mark.parametrize("op", ["=", "!=", "<", ">", "<=", ">="])
def test_all_operators(op):
    ast = parse(f"exitcode(job_a){op}0")
    assert ast.leaves[0].op == op


def test_mixed_case_function_name_rejected():
    with pytest.raises(ConditionParseError):
        parse("Success(job_a)")


def test_all_upper_and_all_lower_both_legal():
    parse("SUCCESS(job_a)")
    parse("success(job_a)")


def test_empty_condition_is_error():
    with pytest.raises(ConditionParseError):
        parse("")


def test_try_parse_returns_error_not_raise():
    ast, err = try_parse("success(")
    assert ast is None and err is not None


def test_canonical_to_string_round_trip():
    ast = parse("s(a) AND f(b)")
    canonical = ast.to_string()
    reparsed = parse(canonical)
    assert reparsed.to_string() == canonical


def test_job_name_with_escaped_colon():
    ast = parse(r"success(job\:with\:colons)")
    assert ast.referenced_job_names == ["job:with:colons"]


def test_deep_nesting_depth_and_clause_count():
    ast = parse("(success(a) OR (success(b) AND success(c))) AND success(d)")
    assert ast.clause_count == 4
    assert ast.depth == 3
