# %%
model_engine_dict = {
    "Text-Davinci-003": "text-davinci-003 (faster)",
    "GPT-4": "gpt-4",
    "GPT-4-32k": "gpt-4-32k (slower)",
}

sample_keys = ["TYK2", "DLBCL", "ProTiler", "atopic dermatitis"]
oa_sample_questions = {
    "On a scale from 0—10, what score would you give the gene BRCA1 for its association with breast cancer?": "BRCA1 breast cancer",
    "What are some key points about TYK2?": "TYK2",
}

# %%
from shiny import App, render, ui, reactive
from dotenv import load_dotenv
import os
import openai
import pyalex
import random
from askalex import answer_question
from openalex import find_abs, get_embed, search_docs, style_dataframe

# %%

load_dotenv()

openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.proxy = os.getenv("OPENAI_PROXY")

pyalex.config.api_key = os.getenv("OPENALEX_API_KEY")
pyalex.config.email = "trang.le@bms.com"

# client = openai.AzureOpenAI(
#     api_key=openai.api_key,
#     api_version=openai.api_version,
#     # azure_endpoint=openai.api_base,
#     base_url=openai.api_base,
# )

if os.getenv("APP_RUN") == "local":
    company_proxy = os.getenv("COMPANY_PROXY")
    os.environ["http_proxy"] = company_proxy
    os.environ["https_proxy"] = company_proxy
    os.environ["ftp_proxy"] = company_proxy
    os.environ["no_proxy"] = os.getenv("COMPANY_NO_PROXY")

app_ui = ui.page_navbar(
    ui.nav(
        "Quick summary",
        ui.div(
            {"style": "width:70%;margin: 0 auto"},
            ui.p("\n"),
            ui.row(
                ui.column(
                    4,
                    ui.p(
                        "Give me a quick summary of",
                        style="margin-top: 6px;",
                    ),
                ),
                ui.column(
                    4,
                    ui.input_text(
                        "oa_quick_key",
                        "",
                        placeholder=random.choice(sample_keys),
                        width="100%",
                    ),
                ),
                ui.column(
                    4,
                    ui.input_action_button(
                        "oa_quick_submit",
                        "Submit",
                    ),
                ),
            ),
            ui.br(),
            ui.output_text("quick_sum"),
            ui.output_ui("refs"),
            ui.output_table("oa_quick_articles_tab"),
        ),
    ),
    ui.nav(
        "Ask your question",
        ui.layout_sidebar(
            ui.panel_sidebar(
                ui.input_text(
                    "oa_keyword",
                    "Keyword(s) to OpenAlex",
                    placeholder="TYK2",
                    width="100%",
                ),
                ui.input_select(
                    "oa_engine",
                    "LLM model",
                    model_engine_dict,
                ),
                ui.input_slider(
                    "n_articles",
                    "Number of articles to index:",
                    min=5,
                    max=30,
                    value=10,
                ),
            ),
            ui.panel_main(
                ui.row(
                    ui.column(
                        5,
                        ui.p("Question:"),
                    ),
                    ui.column(
                        5,
                        ui.input_switch("oa_sample", "Use an example", False),
                    ),
                    ui.column(
                        2,
                        ui.input_action_button(
                            "oa_submit",
                            "Submit",
                            style="margin-top: -6px;margin-bottom: 12px;",
                            width="100%",
                        ),
                    ),
                ),
                ui.output_ui("oa_question"),
                ui.output_text("oa_txt"),
            ),
        ),
        ui.output_table("oa_articles_tab"),
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
    title="🦙 AskAlex",
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
        nonlocal ids
        id = ui.notification_show("Computing embeddings...", duration=None)
        ids.append(id)
        emb = get_embed(abs)
        return emb

    ## OpenAlex tab: Quick summary: oa_

    @reactive.Calc
    @reactive.event(input.oa_quick_submit)
    def oa_quick_question():
        return "Give me a quick summary of " + input.oa_quick_key()

    @reactive.Calc
    @reactive.event(input.oa_quick_submit)
    def oa_quick_articles():
        df = search_docs(
            embedded_abs(find_abs(input.oa_quick_key())),
            oa_quick_question(),
            top_n=10,
        )
        return df

    @output
    @render.text
    @reactive.event(input.oa_quick_submit)
    def quick_sum():
        notif = ui.notification_show("Finding relevant articles...", duration=30)
        df = oa_quick_articles()
        ui.notification_remove(notif)
        if df is None:
            return None
        notif = ui.notification_show("Connecting to OpenAI...", duration=30)
        answer = answer_question(
            question=oa_quick_question(), df=df, engine="T-Cell-Phenotype"
        )
        ui.notification_remove(notif)

        return f"\n{answer}"

    @output
    @render.table
    def oa_quick_articles_tab():
        return style_dataframe(oa_quick_articles()).style.hide(axis="index")

    ## OpenAlex tab: Custom: oa_
    @reactive.Calc
    @reactive.event(input.oa_submit)
    def oa_articles():
        df = search_docs(
            embedded_abs(find_abs(input.oa_keyword())),
            input.oa_question(),
            top_n=input.n_articles(),
        )
        return df

    @output
    @render.table
    def oa_articles_tab():
        return style_dataframe(oa_articles()).style.hide(axis="index")

    @output
    @render.text
    @reactive.event(input.oa_submit)
    def oa_txt():
        nonlocal ids
        if oa_articles() is None:
            return None
        notif = ui.notification_show("Connecting to OpenAI...", duration=30)
        answer = answer_question(
            question=input.oa_question(),
            df=oa_articles(),
            engine=input.oa_engine(),
        )
        ui.notification_remove(notif)

        if ids:
            ui.notification_remove(ids.pop())

        print(f"\n{answer}")
        return f"\n{answer}"

    @reactive.Effect()
    def _():
        if input.oa_sample() and input.oa_question() in oa_sample_questions.keys():
            ui.update_text(
                "oa_keyword",
                value=oa_sample_questions[input.oa_question()],
            )

    @output
    @render.ui
    def oa_question():
        if input.oa_sample():
            oa_sample_folders = list(oa_sample_questions.keys())
            return ui.input_select(
                "oa_question",
                "",
                oa_sample_folders,
                selected=oa_sample_folders[0],
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
