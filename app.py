"""Streamlit UI: Input panel / Output panel / History panel."""
import os

import streamlit as st
from dotenv import load_dotenv

import database
import exporter

load_dotenv()
st.set_page_config(page_title="AI Code Snippet Generator", page_icon="🧩", layout="wide")
st.title("🧩 AI Code Snippet Generator")
st.caption("Requirement → Intent (TensorFlow) → Gemini via LangChain → Agentic validation & repair")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API key", type="password", value=os.getenv("GEMINI_API_KEY", ""),
                            help="Free key: https://aistudio.google.com/apikey")
    model = st.text_input("Gemini model", value=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
    max_repairs = st.slider("Max auto-repair attempts", 0, 3, 2)
    use_tf = st.checkbox("Use TensorFlow intent classifier", value=True)


@st.cache_resource(show_spinner=False)
def get_agent(key: str, model_name: str, repairs: int, tf_on: bool):
    from agent import CodeAgent
    from code_generator import CodeGenerator
    return CodeAgent(CodeGenerator(api_key=key, model=model_name), max_repairs=repairs, use_tensorflow=tf_on)


def show(result, key_prefix="gen"):
    if result.error and not result.snippet:
        st.error(result.error)
    s = result.snippet
    if s:
        icon = {"Passed": "✅", "Passed with Warnings": "⚠️", "Repair Required": "🛠️", "Rejected": "⛔"}
        st.subheader(f"{icon.get(result.validation.state, '')} {result.validation.state}")
        st.code(s.code, language="python")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Category", result.spec.category)
        c2.metric("Complexity", s.complexity or "-")
        c3.metric("Tests passed", f"{result.validation.tests_passed}/{result.validation.tests_total}")
        c4.metric("Time", f"{result.latency_sec}s")
        st.markdown("**Explanation**  \n" + (s.explanation or "-"))
        if result.spec.assumptions:
            st.markdown("**Assumptions**\n" + "\n".join(f"- {a}" for a in result.spec.assumptions))
        v = result.validation
        with st.expander("Validation details"):
            st.write({"syntax_ok": v.syntax_ok, "structure_ok": v.structure_ok,
                      "cyclomatic_complexity": v.cyclomatic, "maintainability_index": v.maintainability,
                      "repair_attempts": result.repair_attempts})
            for label, items in (("Security", v.security_issues), ("Ruff", v.ruff_issues), ("Test failures", v.test_failures)):
                if items:
                    st.markdown(f"**{label}**\n" + "\n".join(f"- {i}" for i in items))
        with st.expander("Agent trace"):
            st.code("\n".join(result.trace))
        d1, d2, d3 = st.columns(3)
        d1.download_button("⬇ snippet.py", exporter.to_python(result), "snippet.py", key=f"{key_prefix}_py")
        d2.download_button("⬇ result.json", exporter.to_json(result), "result.json", key=f"{key_prefix}_json")
        d3.download_button("⬇ test_snippet.py", exporter.to_pytest(result), "test_snippet.py", key=f"{key_prefix}_test")
    for w in result.spec.warnings:
        st.warning(w)


tab_gen, tab_hist = st.tabs(["Generate", "History"])
with tab_gen:
    left, right = st.columns([1, 1.3])
    with left:
        st.subheader("Input")
        req = st.text_area("Natural-language requirement", height=140,
                           placeholder="Create a function to calculate factorial using recursion.")
        cons = st.text_input("Optional constraints (separate with ;)", placeholder="include type hints; no external libraries")
        go = st.button("Generate", type="primary", use_container_width=True)
    with right:
        st.subheader("Output")
        if go:
            if not api_key:
                st.error("Add your Gemini API key in the sidebar or .env file.")
            else:
                with st.spinner("Generating, validating and repairing..."):
                    res = get_agent(api_key, model, max_repairs, use_tf).run(req, constraints=cons)
                if res.snippet:
                    database.save(res)
                st.session_state["last"] = res
        if "last" in st.session_state:
            show(st.session_state["last"], "gen")

with tab_hist:
    rows = database.list_history()
    if not rows:
        st.info("No generations yet.")
    for r in rows:
        with st.expander(f"#{r['id']} · {r['created_at']} · {r['state']} · {r['requirement'][:70]}"):
            full = database.get(r["id"])
            if full:
                show(full, f"hist_{r['id']}")