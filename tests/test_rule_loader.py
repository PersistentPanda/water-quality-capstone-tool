"""Rule loader contract checks. Production CSVs are never edited."""
import csv
from pathlib import Path
import shutil

import pytest

from wqtool.rule_loader import LOAD_ERROR_MESSAGE, RuleLoadError, load_rules

FIXTURES = Path(__file__).parent / 'fixtures' / 'rule_loader'


@pytest.fixture
def files(tmp_path):
    for name in ('parameters.csv', 'recommendations.csv'):
        shutil.copyfile(FIXTURES / name, tmp_path / name)
    return tmp_path / 'parameters.csv', tmp_path / 'recommendations.csv'


def edit(path, change):
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        header, rows = reader.fieldnames, list(reader)
    change(header, rows)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def fails(files):
    with pytest.raises(RuleLoadError) as captured:
        load_rules(*files)
    assert str(captured.value) == LOAD_ERROR_MESSAGE
    assert captured.value.detail


def test_loads_uploaded_contract_and_preserves_files(files):
    before = [path.read_bytes() for path in files]
    ruleset = load_rules(*files)
    assert list(ruleset.thresholds) == ['hardness', 'iron', 'ph', 'tds', 'manganese']
    assert [rule.rule_id for rule in ruleset.rules] == [f'R{i:02}' for i in range(1, 13)]
    hardness = ruleset.thresholds['hardness']
    assert hardness.unit == 'gpg (grains per gallon)'
    assert (hardness.green_max, hardness.yellow_max) == (3.5, 7)
    assert hardness.reference_high is None
    assert hardness.required is True
    assert ruleset.thresholds['manganese'].required is False
    assert ruleset.explanations['ph'].below_text
    assert ruleset.rules[0].comparisons[0].boundary == 'yellow_max'
    assert [(c.operator, c.boundary) for c in ruleset.rules[1].comparisons] == [
        ('>', 'green_max'), ('<=', 'yellow_max')]
    assert ruleset.rules[10].condition_kind == 'water_source'
    assert ruleset.rules[10].source_value == 'Private well'
    assert ruleset.rules[11].condition_kind == 'all_green'
    assert [path.read_bytes() for path in files] == before


@pytest.mark.parametrize('index', [0, 1])
def test_missing_file(files, index):
    files[index].unlink()
    fails(files)


@pytest.mark.parametrize('index', [0, 1])
def test_required_column(files, index):
    def remove(header, rows):
        name = header.pop()
        for row in rows:
            row.pop(name)
    edit(files[index], remove)
    fails(files)


@pytest.mark.parametrize('index', [0, 1])
def test_duplicate_identifier(files, index):
    edit(files[index], lambda header, rows: rows.append(rows[0].copy()))
    fails(files)


def test_unknown_parameter_reference(files):
    edit(files[1], lambda header, rows: rows[0].update(parameter_id='unknown'))
    fails(files)


def test_referenced_optional_boundary_is_required(files):
    edit(files[1], lambda header, rows: rows[0].update(condition='value > reference_high'))
    fails(files)


@pytest.mark.parametrize('value', ['', 'abc', 'NaN', 'Infinity', '-Infinity', '1e9999', '1e-9999'])
def test_unusable_numeric_boundary(files, value):
    edit(files[0], lambda header, rows: rows[0].update(green_max=value))
    fails(files)


@pytest.mark.parametrize('condition', [
    'value != yellow_max', 'value == yellow_max', 'value > 7',
    'value > nonexistent', 'value > yellow_max OR value < green_max',
    'value > yellow_max AND', 'value > yellow_max trailing',
    '__import__("os").system("echo unexpected")',
    'all_green', 'water_source == Private well', '',
])
def test_unsupported_or_mismatched_condition(files, condition):
    edit(files[1], lambda header, rows: rows[0].update(condition=condition))
    fails(files)


@pytest.mark.parametrize('index,parameter,condition', [
    (10, 'all', 'water_source == Private well'),
    (10, 'water_source', 'water_source == Public supply'),
    (11, 'water_source', 'all_green'),
    (11, 'all', 'value > green_max'),
])
def test_special_condition_scope(files, index, parameter, condition):
    edit(files[1], lambda header, rows: rows[index].update(
        parameter_id=parameter, condition=condition))
    fails(files)


@pytest.mark.parametrize('index', [0, 1])
def test_empty_file(files, index):
    files[index].write_text('')
    fails(files)


@pytest.mark.parametrize('index', [0, 1])
def test_header_only(files, index):
    edit(files[index], lambda header, rows: rows.clear())
    fails(files)


@pytest.mark.parametrize('index', [0, 1])
def test_duplicate_header(files, index):
    data = files[index].read_text().splitlines()
    data[0] += ',' + data[0].split(',')[0]
    files[index].write_text('\n'.join(data))
    fails(files)


@pytest.mark.parametrize('index', [0, 1])
def test_wrong_row_width(files, index):
    with files[index].open('a') as stream:
        stream.write('\nunquoted,extra,row\n')
    fails(files)


def test_invalid_utf8(files):
    files[0].write_bytes(b'\xff\xfe')
    fails(files)


def test_malformed_quoted_csv(files):
    with files[1].open('a') as stream:
        stream.write('\n"unterminated')
    fails(files)


@pytest.mark.parametrize('updates', [
    {'green_max': '-1'}, {'green_max': '8'}, {'required': 'yes'},
    {'display_name': ''}, {'unit': ''}, {'reference_source': ''},
    {'what_it_measures': ''}, {'within_text': ''}, {'above_text': ''},
    {'parameter_id': ''}, {'parameter_id': 'unexpected'},
    {'reference_low': '9', 'reference_high': '8'},
])
def test_invalid_parameter_row(files, updates):
    edit(files[0], lambda header, rows: rows[0].update(updates))
    fails(files)


@pytest.mark.parametrize('updates', [
    {'low_red_below': ''}, {'low_yellow_below': ''},
    {'low_red_below': '7.1'}, {'low_yellow_below': '8.1'},
    {'reference_low': ''}, {'reference_high': '15'}, {'below_text': ''},
])
def test_invalid_ph_configuration(files, updates):
    edit(files[0], lambda header, rows: rows[2].update(updates))
    fails(files)


def test_missing_measurement_row(files):
    edit(files[0], lambda header, rows: rows.pop())
    fails(files)


@pytest.mark.parametrize('column', ['rule_id', 'suggestion_text', 'reason_text'])
def test_blank_rule_fields(files, column):
    edit(files[1], lambda header, rows: rows[0].update({column: ''}))
    fails(files)


def test_csv_only_changes_are_loaded_on_next_call(files):
    original = load_rules(*files)
    edit(files[0], lambda header, rows: rows[1].update(yellow_max='0.50', display_name='Iron revised'))
    edit(files[1], lambda header, rows: rows[0].update(suggestion_text='Revised suggestion'))
    updated = load_rules(*files)
    assert original.thresholds['iron'].yellow_max == 0.30
    assert updated.thresholds['iron'].yellow_max == 0.50
    assert updated.thresholds['iron'].reference_high == 0.30
    assert updated.thresholds['iron'].display_name == 'Iron revised'
    assert updated.rules[0].suggestion_text == 'Revised suggestion'


def test_bom_blank_lines_and_extra_columns(files):
    for path in files:
        def add(header, rows):
            header.append('review_note')
            for row in rows:
                row['review_note'] = 'retained only in the file'
        edit(path, add)
        path.write_text('\ufeff' + path.read_text() + '\n\n', encoding='utf-8')
    assert len(load_rules(*files).rules) == 12


def add_very_high(path, value):
    def change(header, rows):
        header.append('very_high_above')
        for row in rows:
            row['very_high_above'] = value if row['parameter_id'] == 'hardness' else ''
    edit(path, change)


def test_greater_equal_condition(files):
    edit(files[1], lambda header, rows: rows.append(dict(
        rule_id='R13', parameter_id='ph',
        condition='value >= reference_low AND value < low_yellow_below',
        suggestion_text='Monitor pH.', reason_text='Low yellow pH.')))
    rule = load_rules(*files).rules[-1]
    assert rule.condition_kind == 'numeric'
    assert [(c.operator, c.boundary) for c in rule.comparisons] == [
        ('>=', 'reference_low'), ('<', 'low_yellow_below')]


@pytest.mark.parametrize('value', ['', '7', '10.5'])
def test_optional_very_high_column(files, value):
    add_very_high(files[0], value)
    thresholds = load_rules(*files).thresholds
    assert thresholds['hardness'].very_high_above == (float(value) if value else None)
    assert thresholds['ph'].very_high_above is None


def test_very_high_column_can_be_absent(files):
    assert load_rules(*files).thresholds['hardness'].very_high_above is None


@pytest.mark.parametrize('value', ['6.9', '-1', 'abc', 'NaN', 'Infinity', '-Infinity', '1e9999', '1e-9999'])
def test_invalid_very_high_value(files, value):
    add_very_high(files[0], value)
    fails(files)


def test_rule_can_reference_very_high(files):
    add_very_high(files[0], '10.5')
    edit(files[1], lambda header, rows: rows[0].update(condition='value > very_high_above'))
    ruleset = load_rules(*files)
    assert ruleset.rules[0].comparisons[0].boundary == 'very_high_above'
    assert ruleset.thresholds['hardness'].very_high_above == 10.5


@pytest.mark.parametrize('include_column', [True, False])
def test_reference_to_missing_very_high_fails(files, include_column):
    if include_column:
        add_very_high(files[0], '')
    edit(files[1], lambda header, rows: rows[0].update(condition='value >= very_high_above'))
    fails(files)


def test_ge_and_very_high_together_with_special_rules(files):
    add_very_high(files[0], '10.5')
    edit(files[1], lambda header, rows: rows.append(dict(
        rule_id='R13', parameter_id='ph', condition='value >= reference_low AND value < low_yellow_below',
        suggestion_text='Monitor pH.', reason_text='Low yellow pH.')))
    result = load_rules(*files)
    assert result.thresholds['hardness'].very_high_above == 10.5
    assert result.rules[10].condition_kind == 'water_source'
    assert result.rules[11].condition_kind == 'all_green'
    assert result.rules[12].comparisons[0].operator == '>='
