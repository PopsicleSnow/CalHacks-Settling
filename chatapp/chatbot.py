import reflex as rx
from rxconfig import config
from chatapp.state import State
from chatapp import style

def qa(question: str, answer: str) -> rx.Component:
    return rx.cond(
        question == "",
        rx.box(
            rx.text(answer, style=style.answer_style),
            text_align="left",
        ),
        rx.cond(
            answer == "",
            rx.box(rx.text(question, style=style.question_style), text_align="right"),
            rx.box(
                rx.box(
                    rx.text(question, style=style.question_style),
                    text_align="right",
                ),
                rx.box(
                    rx.text(answer, style=style.answer_style),
                    text_align="left",
                ),
                margin_y="1em",
            )
        )
    )
    
    

def chat() -> rx.Component:
    return rx.box(
        rx.foreach(
            State.chat_history,
            lambda messages: qa(messages[0], messages[1]),
        )
    )

def reset_button():
    return rx.button(
        "Reset/Update Profile",
        on_click=State.reset_chat,
        color_scheme="orange",
        style=style.button_style
    )

def action_bar() -> rx.Component:
    return rx.hstack(
        rx.input(
            value=State.question,
            placeholder="Answer the question above.",
            on_change=State.set_question,
            style=style.input_style,
        ),
        rx.button(
            "Respond",
            on_click=State.answer,
            style=style.button_style,
        ),
        reset_button()
    )

def chatmodel() -> rx.Component:
    return rx.center(
        rx.vstack(
            chat(),
            action_bar(),
            align="center",
            margin_top="20vh"
        )
    )

__all__ = ["chatmodel"]

