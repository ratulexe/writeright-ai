import os

import streamlit as st
from dotenv import load_dotenv


# ---------------------------------------------------------
# Application configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="WriteRight AI",
    page_icon="✍️",
    layout="wide",
)


# ---------------------------------------------------------
# Load Gemini API key
# ---------------------------------------------------------

load_dotenv()


def get_streamlit_secret(name: str) -> str:
    """Read a Streamlit secret when available without breaking local runs."""

    try:
        value = st.secrets.get(name, "")
    except (FileNotFoundError, KeyError, AttributeError):
        return ""

    return str(value).strip()


gemini_api_key = (
    get_streamlit_secret("GEMINI_API_KEY")
    or os.getenv("GEMINI_API_KEY", "").strip()
)
google_api_key = (
    get_streamlit_secret("GOOGLE_API_KEY")
    or os.getenv("GOOGLE_API_KEY", "").strip()
)
api_key = gemini_api_key or google_api_key

if api_key:
    # The SDK prefers GOOGLE_API_KEY when both variables exist. Normalize to
    # one key so it cannot accidentally choose a stale system environment key.
    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ.pop("GEMINI_API_KEY", None)

from google import genai


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

default_state = {
    "user_text": "",
    "original_text": "",
    "improved_text": "",
    "corrections": "",
    "result_tone": "",
    "result_improvement_type": "",
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value


def clear_all() -> None:
    """Clear the input and generated result."""

    st.session_state.user_text = ""
    st.session_state.original_text = ""
    st.session_state.improved_text = ""
    st.session_state.corrections = ""
    st.session_state.result_tone = ""
    st.session_state.result_improvement_type = ""


def parse_gemini_response(result: str) -> tuple[str, str]:
    """Separate the improved text and corrections."""

    cleaned_result = result.strip()

    if "CORRECTIONS:" in cleaned_result:
        improved_part, corrections_part = cleaned_result.split(
            "CORRECTIONS:",
            maxsplit=1,
        )
    else:
        improved_part = cleaned_result
        corrections_part = (
            "- Grammar, spelling and sentence structure were reviewed."
        )

    improved_text = improved_part.replace(
        "IMPROVED TEXT:",
        "",
        1,
    ).strip()

    corrections = corrections_part.strip()

    return improved_text, corrections


# ---------------------------------------------------------
# Custom styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Libertinus+Serif:ital,wght@0,400;0,600;0,700;1,400;1,600;1,700&display=swap'
    );

    :root {
        --bg: #f6f8fb;
        --surface: #ffffff;
        --surface-soft: #eef6ff;
        --text: #172033;
        --muted: #5f6b7a;
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --accent: #0f9f7a;
        --border: #d8e0ea;
        --shadow: 0 14px 34px rgba(23, 32, 51, 0.09);
    }

    html,
    body,
    .stApp,
    .stApp input,
    .stApp textarea,
    .stApp button {
        font-family: "Libertinus Serif", Georgia, serif !important;
    }

    .stCodeBlock,
    .stCodeBlock *,
    pre,
    code {
        font-family: "Libertinus Serif", Georgia, serif !important;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
        font-size: 18px;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu,
    footer {
        visibility: hidden;
    }

    .block-container {
        max-width: 1050px;
        padding-top: 2rem;
        padding-bottom: 2.5rem;
    }

    .stApp p,
    .stApp label,
    .stApp textarea,
    .stApp input,
    .stApp button,
    .stCodeBlock code,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {
        font-size: 1.08rem !important;
        line-height: 1.55;
    }

    .stApp h1 {
        color: var(--text);
        font-size: 2.75rem;
        line-height: 1;
    }

    .stApp h2,
    .stApp h3 {
        color: var(--text);
        font-size: 1.6rem;
    }

    .hero {
        background: linear-gradient(135deg, #ffffff 0%, #eef6ff 100%);
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: var(--shadow);
        color: var(--text);
        margin-bottom: 1.4rem;
        overflow: hidden;
        padding: 1.6rem 1.8rem;
        position: relative;
    }

    .hero:after {
        background: var(--accent);
        border-radius: 999px;
        content: "";
        height: 0.72rem;
        position: absolute;
        right: 1.8rem;
        top: 1.8rem;
        width: 0.72rem;
    }

    .hero h1 {
        color: var(--text) !important;
        font-size: 3rem !important;
        font-weight: 700;
        margin: 0 0 0.4rem;
        position: relative;
        z-index: 1;
    }

    .hero p {
        color: var(--muted) !important;
        font-size: 1.18rem !important;
        line-height: 1.45;
        margin: 0;
        max-width: 44rem;
        position: relative;
        z-index: 1;
    }

    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stTextInput"] input {
        background: var(--surface) !important;
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 8px 22px rgba(23, 32, 51, 0.06);
        color: var(--text) !important;
    }

    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
    }

    [data-testid="stTextArea"] textarea::placeholder {
        color: #9aa6b2 !important;
        opacity: 1;
    }

    [data-baseweb="select"],
    [data-baseweb="select"] > div,
    [data-baseweb="select"] div,
    [data-baseweb="select"] span {
        background-color: var(--surface) !important;
        color: var(--text) !important;
    }

    [data-testid="stWidgetLabel"] label,
    [data-testid="stMarkdownContainer"] p,
    .stCaptionContainer {
        color: var(--muted);
    }

    .stButton button,
    .stDownloadButton button {
        background: var(--surface) !important;
        border-radius: 8px;
        border: 1px solid var(--border);
        box-shadow: 0 10px 22px rgba(23, 32, 51, 0.08);
        color: var(--text) !important;
        min-height: 3rem;
    }

    .stButton button *,
    .stDownloadButton button * {
        color: inherit !important;
    }

    .stButton button[kind="primary"] {
        background: var(--primary) !important;
        border-color: var(--primary);
        color: #ffffff !important;
        font-weight: 700;
    }

    .stButton button[kind="primary"]:hover {
        background: var(--primary-dark) !important;
        border-color: var(--primary-dark);
        color: #ffffff !important;
    }

    .stButton button[kind="secondary"]:hover {
        background: var(--surface-soft) !important;
        border-color: var(--primary);
        color: var(--text) !important;
    }

    .stDownloadButton button {
        background: var(--surface) !important;
        border-color: var(--accent);
        color: var(--text) !important;
        font-weight: 700;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface);
        border-color: var(--border);
        border-radius: 8px;
        box-shadow: 0 12px 28px rgba(23, 32, 51, 0.07);
    }

    .stCodeBlock pre {
        background: var(--surface) !important;
        border: 1px solid var(--border);
        border-left: 5px solid var(--accent);
        border-radius: 8px;
        box-shadow: 0 12px 28px rgba(23, 32, 51, 0.07);
        color: var(--text);
    }

    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
    }

    hr {
        border-color: var(--border);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <section class="hero">
        <h1>WriteRight AI</h1>
        <p>
            Refine rough drafts into clear, polished writing with a tone
            that matches the moment.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Input section
# ---------------------------------------------------------

user_text = st.text_area(
    "Enter or paste your text",
    height=220,
    placeholder=(
        "Example: I am writing this mail because i want know "
        "about the internship."
    ),
    key="user_text",
)

selection_column1, selection_column2 = st.columns(2)

with selection_column1:
    improvement_type = st.selectbox(
        "Select improvement type",
        [
            "Grammar and spelling",
            "Improve clarity",
            "Rewrite professionally",
            "Simplify the text",
            "Shorten the text",
        ],
    )

with selection_column2:
    tone = st.selectbox(
        "Select writing tone",
        [
            "Professional",
            "Formal",
            "Friendly",
            "Academic",
            "Casual",
            "Polite",
        ],
    )


# ---------------------------------------------------------
# Action buttons
# ---------------------------------------------------------

check_column, clear_column = st.columns(2)

with check_column:
    check_button = st.button(
        "Check Grammar",
        type="primary",
        use_container_width=True,
    )

with clear_column:
    st.button(
        "Clear All",
        use_container_width=True,
        on_click=clear_all,
    )


# ---------------------------------------------------------
# Generate improved text
# ---------------------------------------------------------

if check_button:
    if not user_text.strip():
        st.warning("Please enter some text before checking.")

    elif len(user_text.strip()) < 3:
        st.warning("Please enter a longer sentence or paragraph.")

    elif not api_key:
        st.error(
            "Gemini API key was not found. "
            "Add GEMINI_API_KEY in Streamlit Cloud secrets, or to your "
            "local .env file when running locally."
        )

    else:
        # Clear the previous result before generating a new one.
        st.session_state.original_text = ""
        st.session_state.improved_text = ""
        st.session_state.corrections = ""

        try:
            client = genai.Client(api_key=api_key)

            prompt = f"""
You are an expert grammar and writing assistant.

Improve the user's text according to these settings:

Improvement type: {improvement_type}
Writing tone: {tone}

Instructions:

1. Correct grammar, spelling, punctuation and capitalization.
2. Preserve the original meaning.
3. Follow the selected improvement type.
4. Use the selected writing tone.
5. Do not add unrelated information.
6. Do not include quotation marks around the improved text.
7. Explain only the most important corrections.
8. Return the result using exactly this format:

IMPROVED TEXT:
Write the complete improved text here.

CORRECTIONS:
- Explain the first important correction.
- Explain the second important correction.
- Explain the third important correction.

USER TEXT:
{user_text}
"""

            with st.spinner("Checking and improving your text..."):
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                )

            if not response.text:
                st.error(
                    "Gemini returned an empty response. Please try again."
                )

            else:
                improved_text, corrections = parse_gemini_response(
                    response.text
                )

                if not improved_text:
                    st.error(
                        "The improved text could not be generated. "
                        "Please try again."
                    )

                else:
                    st.session_state.original_text = user_text
                    st.session_state.improved_text = improved_text
                    st.session_state.corrections = corrections
                    st.session_state.result_tone = tone
                    st.session_state.result_improvement_type = (
                        improvement_type
                    )

        except Exception as error:
            st.error(
                "Unable to connect to Gemini. Check your API key "
                "and internet connection."
            )

            with st.expander("Technical details"):
                st.code(str(error), language=None)


# ---------------------------------------------------------
# Display generated result
# ---------------------------------------------------------

if st.session_state.improved_text:
    st.divider()

    original_column, improved_column = st.columns(2)

    with original_column:
        st.subheader("Original Text")

        st.container(
            border=True,
        ).write(st.session_state.original_text)

    with improved_column:
        st.subheader("Improved Text")

        # st.code provides a clipboard icon in the top-right corner.
        st.code(
            st.session_state.improved_text,
            language=None,
            wrap_lines=True,
        )

        st.download_button(
            label="Download Corrected Text",
            data=st.session_state.improved_text,
            file_name="writeright_corrected_text.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.subheader("Important Corrections")
    st.markdown(st.session_state.corrections)

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Original words",
            len(st.session_state.original_text.split()),
        )

    with metric2:
        st.metric(
            "Improved words",
            len(st.session_state.improved_text.split()),
        )

    with metric3:
        st.metric(
            "Selected tone",
            st.session_state.result_tone,
        )

    st.caption(
        "Improvement type: "
        f"{st.session_state.result_improvement_type}"
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()

st.caption(
    "WriteRight AI may occasionally make mistakes. "
    "Review important academic or professional content before using it."
)
