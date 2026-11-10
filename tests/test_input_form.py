from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')

def test_form_preserves_errors_and_resets_session():
    app = AppTest.from_file(APP).run()
    assert not app.exception
    values = ['150', '0.2', '15', '300', '', '4']
    for widget, value in zip(app.text_input, values):
        widget.input(value)
    app.selectbox[0].select('Private well')
    app.button[0].click().run()
    assert len(app.error) == 1 and 'pH' in app.error[0].value
    assert app.text_input[0].value == '150'
    assert not app.success
    app.text_input[2].input('7.2')
    app.button[0].click().run()
    assert not app.exception and len(app.success) == 1
    assert app.session_state['validated_entry'].manganese is None
    assert app.table[0].value.iloc[4]['Entered value'] == 'Not provided'
    app.text_input[1].input('-1')
    app.button[0].click().run()
    assert app.error and not app.table
    app.button[1].click().run()
    assert all(widget.value == '' for widget in app.text_input)
    assert app.selectbox[0].value == 'Select a water source'
    assert not app.table
    assert not app.exception

def test_separate_browser_session_starts_empty():
    app = AppTest.from_file(APP).run()
    assert all(widget.value == '' for widget in app.text_input)
    assert not app.table
