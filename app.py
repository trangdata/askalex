# %%
from shiny import App, render, ui, reactive
from shiny.types import NavSetArg
from typing import List
import os
from askalex import answer_question, get_keywords, show_cost
from openalex import find_abs, get_embed, search_docs, style_dataframe

# %%
sample_keys = ["TYK2", "DLBCL", "ProTiler"]
model_engine_dict = {
    "gpt-4-32k": "gpt-4-32k (slower)",
    "gpt-4": "gpt-4",
    "gpt-35-turbo-16k": "gpt-35-turbo-16k",
    "gpt-35-turbo": "gpt-35-turbo (faster)",
}

oa_sample_questions = [
    # "On a scale from 0—10, what score would you give the gene BRCA1 for its association with breast cancer?",
    # "What are some key points about TYK2?",
    # "How do current clinical guidelines address the use of anticoagulants in patients with atrial fibrillation?",
    # "How does the effectiveness of traditional chemotherapy compare to targeted therapies in the treatment of leukemia?",
    # "What are the key differences between the molecular mechanisms of apoptosis and necrosis?",
    "How does tau malfunction in Alzheimer's?",
    "What is BRCA2's role in breast cancer?",
    "What is hydroxychloroquine's efficacy in rheumatoid arthritis?",
    "How reliable is CRP as an inflammation marker?",
    "How does the Mediterranean diet reduce heart disease risk?",
    "What is mTOR's role in aging?",
]

if os.getenv("APP_RUN") == "local":
    bms_proxy = "http://proxy-server.bms.com:8080/"
    os.environ["http_proxy"] = bms_proxy
    os.environ["https_proxy"] = bms_proxy
    os.environ["ftp_proxy"] = bms_proxy
    os.environ["no_proxy"] = ".celgene.com,.bms.com"


def nav_controls(prefix: str) -> List[NavSetArg]:
    return [
        ui.nav(
            "",
            ui.div(
                {"style": "width:70%;margin: 0 auto"},
                ui.layout_sidebar(
                    ui.panel_sidebar(
                        ui.input_select(
                            "oa_engine",
                            "LLM model",
                            model_engine_dict,
                        ),
                        ui.input_slider(
                            "n_articles",
                            "Number of articles to index:",
                            min=3,
                            max=20,
                            value=6,
                        ),
                        ui.p("Estimated cost:"),
                        ui.output_text("oa_cost"),
                    ),
                    ui.panel_main(
                        ui.input_switch("oa_sample", "Use an example", False),
                        ui.output_ui("oa_question"),
                        ui.input_action_button("oa_submit", "Submit"),
                        ui.output_text("oa_txt"),
                    ),
                ),
                ui.output_table("oa_articles_tab"),
            ),
        ),
        ui.nav_spacer(),
        ui.nav_menu(
            "Other links",
            ui.nav_control(
                ui.a(
                    "Source code",
                    href="https://github.com/trangdata/askalex",
                    target="_blank",
                ),
            ),
            align="right",
        ),
    ]


app_ui = ui.page_navbar(
    *nav_controls("Ask a question"),
    title="🦙  AskAlex",
    inverse=True,
    id="navbar_id",
)


def server(input, output, session):
    ids: list[str] = []

    @output
    @render.ui
    @reactive.event(
        input.oa_quick_submit,
        input.oa_submit,
        input.ps_submit,
    )
    def refs():
        return ui.h4("References")

    def embedded_abs(abs):
        if abs is None:
            return None
        nonlocal ids
        id = ui.notification_show("Computing embeddings...", duration=None)
        ids.append(id)
        emb = get_embed(abs)
        return emb

    ## OpenAlex tab: Custom: oa_
    @reactive.Calc
    @reactive.event(input.oa_submit)
    def oa_articles():
        df = search_docs(
            embedded_abs(find_abs(get_keywords(input.oa_question()))),
            input.oa_question(),
            top_n=input.n_articles(),
        )
        return df

    @output
    @render.table
    def oa_articles_tab():
        if oa_articles() is None:
            return None
        return style_dataframe(oa_articles()).style.hide(axis="index")

    result = reactive.Value()

    @reactive.Effect
    @reactive.event(input.oa_submit)
    def _():
        nonlocal ids
        if oa_articles() is None:
            return None
        notif = ui.notification_show("Connecting to OpenAI...", duration=30)
        answer = answer_question(
            question=input.oa_question(),
            df=oa_articles(),
            model=input.oa_engine(),
        )
        ui.notification_remove(notif)

        if ids:
            ui.notification_remove(ids.pop())

        result.set(answer)

    @output
    @render.text
    def oa_txt():
        res = result.get()
        if res is not None:
            return f"\n{res[0]}"

    @output
    @render.text
    def oa_cost():
        res = result.get()
        if res is not None:
            return show_cost(res[1][0])

    @output
    @render.ui
    def oa_question():
        if input.oa_sample():
            return ui.input_select(
                "oa_question",
                "",
                oa_sample_questions,
                selected=oa_sample_questions[0],
                width="100%",
            )

        return (
            ui.input_text(
                "oa_question",
                "",
                placeholder="What are some key points about TYK2?",
                width="100%",
            ),
        )


app = App(app_ui, server, debug=True)
