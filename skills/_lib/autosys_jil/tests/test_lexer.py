from autosys_jil.lexer import tokenize


def test_basic_block():
    blocks = list(tokenize("insert_job: foo\njob_type: CMD\ncommand: echo hi\n"))
    assert len(blocks) == 1
    b = blocks[0]
    assert b.kind == "insert_job" and b.name == "foo"
    assert [(a.key, a.raw) for a in b.attrs] == [("job_type", "CMD"), ("command", "echo hi")]


def test_header_line_second_attribute():
    blocks = list(tokenize("insert_job: foo   job_type: CMD\ncommand: echo hi\n"))
    b = blocks[0]
    assert b.attrs[0].key == "job_type" and b.attrs[0].raw == "CMD"
    assert b.attrs[1].key == "command"


def test_comment_stripped_and_hash_is_not_a_comment():
    text = "insert_job: foo\n/* this is a comment\nspanning lines */\ncommand: echo # not a comment\n"
    blocks = list(tokenize(text))
    b = blocks[0]
    assert b.attrs[0].key == "command"
    assert b.attrs[0].raw == "echo # not a comment"


def test_quoted_value_with_colon():
    blocks = list(tokenize('insert_job: foo\nwatch_file: "C:\\myapps\\EOD.bat"\n'))
    b = blocks[0]
    assert b.attrs[0].raw == "C:\\myapps\\EOD.bat"


def test_line_continuation():
    text = "insert_job: foo\ncommand: echo one \\\ntwo\n"
    blocks = list(tokenize(text))
    b = blocks[0]
    assert b.attrs[0].raw == "echo one two"


def test_unquoted_colon_after_first_is_kept_whole():
    blocks = list(tokenize("insert_job: foo\ncommand: echo a:b\n"))
    assert blocks[0].attrs[0].raw == "echo a:b"


def test_multiple_blocks_in_order():
    text = "insert_job: a\ncommand: 1\ninsert_job: b\ncommand: 2\n"
    blocks = list(tokenize(text))
    assert [b.name for b in blocks] == ["a", "b"]
    assert [b.index for b in blocks] == [0, 1]


def test_unknown_subcommand_kept_not_dropped():
    text = "insert_frobnicate: weird\nsome_attr: 1\n"
    blocks = list(tokenize(text))
    assert len(blocks) == 1
    assert blocks[0].kind == "unknown"
    assert blocks[0].name == "weird"


def test_header_line_number_recorded():
    text = "\n\ninsert_job: foo\ncommand: x\n"
    b = next(tokenize(text))
    assert b.header_line == 3


def test_crlf_and_bom_handled():
    text = "\ufeffinsert_job: foo\r\ncommand: x\r\n"
    blocks = list(tokenize(text))
    assert blocks[0].name == "foo"
    assert blocks[0].attrs[0].raw == "x"
