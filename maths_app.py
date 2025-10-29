import random
import time
from typing import List, Tuple, Dict, Any, Optional
import streamlit as st

# -----------------------------
# Helpers
# -----------------------------
def generate_question(ops: List[str], lo: int, hi: int) -> Dict[str, Any]:
    a = random.randint(lo, hi)
    b = random.randint(lo, hi)
    op = random.choice(ops)

    if op in ("/", "*"):
        b = random.randint(max(1, lo), max(1, min(10, hi)))

    if op == "+":
        ans = a + b
        display = f"{a} + {b}"
    elif op == "-":
        ans = a - b
        display = f"{a} - {b}"
    elif op == "*":
        ans = a * b
        display = f"{a} × {b}"
    else:
        ans = round(a / b, 2)
        display = f"{a} ÷ {b} (round to 2 decimals)"
    return {"a": a, "b": b, "op": op, "text": display, "answer": ans}


def generate_quiz(n_questions: int, ops: List[str], lo: int, hi: int) -> List[Dict[str, Any]]:
    return [generate_question(ops, lo, hi) for _ in range(n_questions)]


def check_answer(user_val: str, correct: Any, op: str) -> Tuple[bool, Optional[float]]:
    try:
        val = float(user_val)
        if op == "/":
            return (abs(val - float(correct)) < 1e-2, val)
        else:
            return (val == float(correct), val)
    except Exception:
        return (False, None)


# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="Maths Quiz", page_icon="🧮", layout="centered")

if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "started_at" not in st.session_state:
    st.session_state.started_at = None
if "finished" not in st.session_state:
    st.session_state.finished = False
if "responses" not in st.session_state:
    st.session_state.responses = []

st.title("🧮 Maths Quiz")
st.caption("Hone your mental maths skills with these questions.")

with st.sidebar:
    st.header("Settings")
    n_questions = st.number_input("Number of questions", min_value=1, max_value=100, value=10, step=1)
    lo, hi = st.slider("Number range", min_value=0, max_value=500, value=(1, 100), step=1)
    cols = st.columns(2)
    with cols[0]:
        op_add = st.checkbox("Addition (+)", value=True)
        op_mul = st.checkbox("Multiplication (×)", value=True)
    with cols[1]:
        op_sub = st.checkbox("Subtraction (-)", value=True)
        op_div = st.checkbox("Division (÷)", value=True)

    selected_ops = [op for op, enabled in zip(["+", "-", "*", "/"], [op_add, op_sub, op_mul, op_div]) if enabled]
    if not selected_ops:
        st.warning("Pick at least one operation to start.", icon="⚠️")

    st.markdown("---")
    timing = st.toggle("Enable timer", value=True, help="Track total time for the quiz.")
    start_btn = st.button("Start new quiz", type="primary", use_container_width=True)


def reset_quiz():
    st.session_state.quiz = generate_quiz(n_questions, selected_ops, lo, hi)
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.responses = []
    st.session_state.finished = False
    st.session_state.started_at = time.time() if timing else None


if start_btn and selected_ops:
    reset_quiz()

if st.session_state.quiz and not st.session_state.finished:
    q = st.session_state.quiz[st.session_state.idx]
    st.subheader(f"Question {st.session_state.idx + 1} of {len(st.session_state.quiz)}")
    st.info(q["text"])

    key_input = f"answer_{st.session_state.idx}"
    ans = st.text_input("Your answer", key=key_input, placeholder="Type a number...")

    cols = st.columns([1, 1, 1])
    with cols[0]:
        submit = st.button("Submit")
    with cols[1]:
        skip = st.button("Skip")
    with cols[2]:
        end_now = st.button("End quiz")

    feedback_spot = st.empty()

    if submit:
        correct = q["answer"]
        ok, parsed = check_answer(ans, correct, q["op"])
        st.session_state.responses.append({
            "question": q["text"],
            "your_answer": ans,
            "correct_answer": correct,
            "is_correct": ok,
        })
        if ok:
            st.session_state.score += 1
            feedback_spot.success("Correct! ✅")
        else:
            feedback_spot.error(f"Not quite. Correct answer is **{correct}**.")

        if st.session_state.idx + 1 < len(st.session_state.quiz):
            st.session_state.idx += 1
            st.rerun()
        else:
            st.session_state.finished = True
            st.rerun()

    if skip:
        st.session_state.responses.append({
            "question": q["text"],
            "your_answer": "",
            "correct_answer": q["answer"],
            "is_correct": False,
        })
        if st.session_state.idx + 1 < len(st.session_state.quiz):
            st.session_state.idx += 1
            st.rerun()
        else:
            st.session_state.finished = True
            st.rerun()

    if end_now:
        st.session_state.finished = True
        st.rerun()

elif st.session_state.finished and st.session_state.quiz:
    st.success("Quiz finished!")
    n = len(st.session_state.quiz)
    score = st.session_state.score

    duration = None
    if st.session_state.started_at is not None:
        duration = round(time.time() - st.session_state.started_at, 2)

    cols = st.columns(3)
    cols[0].metric("Score", f"{score} / {n}")
    if duration is not None:
        cols[1].metric("Time taken", f"{duration} s")
        if n > 0:
            cols[2].metric("Avg time / Q", f"{round(duration / n, 2)} s")
    else:
        cols[1].metric("Time taken", "—")
        cols[2].metric("Avg time / Q", "—")

    import pandas as pd
    st.markdown("### Review")
    df = pd.DataFrame(st.session_state.responses)
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download results (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="maths_quiz_results.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.button("Start again", on_click=lambda: reset_quiz(), type="primary")

else:
    st.info("Configure your quiz in the left sidebar and click **Start new quiz**.")
