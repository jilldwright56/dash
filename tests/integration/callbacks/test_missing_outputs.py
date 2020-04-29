import pytest

import dash_html_components as html
# import dash_core_components as dcc
import dash
from dash.dependencies import Input, Output, ALL


@pytest.mark.parametrize("with_simple", (True,))
def test_cbmo001_all_output(with_simple, dash_duo):
    app = dash.Dash(__name__)

    app.layout = html.Div(children=[
        html.Button("items", id="items"),
        html.Button("values", id="values"),
        html.Div(id="content"),
        html.Div("Output init", id="output"),
    ])

    @app.callback(Output("content", "children"), [Input("items", "n_clicks")])
    def content(n1):
        return [html.Div(id={"i": i}) for i in range((n1 or 0) % 4)]

    # these two variants have identical results, but the internal behavior
    # is different when you combine the callbacks.
    if with_simple:
        @app.callback(
            [Output({"i": ALL}, "children"), Output("output", "children")],
            [Input("values", "n_clicks")]
        )
        def content_and_output(n2):
            # this variant *does* get called with empty ALL, because of the
            # second Output
            n1 = len(dash.callback_context.outputs_list[0])
            print(n1, n2)
            content = [n2 or 0] * n1
            return content, sum(content)

    else:
        @app.callback(Output({"i": ALL}, "children"), [Input("values", "n_clicks")])
        def content_inner(n2):
            # this variant does NOT get called with empty ALL
            # the second callback handles outputting 0 in that case.
            # if it were to be called throw an error so we'll see it in get_logs
            n1 = len(dash.callback_context.outputs_list)
            if not n1:
                raise ValueError("should not be called with no outputs!")
            return [n2 or 0] * n1

        @app.callback(Output("output", "children"), [Input({"i": ALL}, "children")])
        def out2(contents):
            return sum(contents)

    dash_duo.start_server(app)

    dash_duo.wait_for_text_to_equal("#content", "")
    dash_duo.wait_for_text_to_equal("#output", "0")

    actions = [
        ["#values", "", "0"],
        ["#items", "1", "1"],
        ["#values", "2", "2"],
        ["#items", "2\n2", "4"],
        ["#values", "3\n3", "6"],
        ["#items", "3\n3\n3", "9"],
        ["#values", "4\n4\n4", "12"],
        ["#items", "", "0"],
        ["#values", "", "0"],
        ["#items", "5", "5"]
    ]
    for selector, content, output in actions:
        dash_duo.find_element(selector).click()
        dash_duo.wait_for_text_to_equal("#content", content)
        dash_duo.wait_for_text_to_equal("#output", output)

    assert not dash_duo.get_logs()
