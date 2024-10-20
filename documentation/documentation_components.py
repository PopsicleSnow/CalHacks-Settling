import reflex as rx
from rxconfig import config
from documentation.documentation_help import State
from chatapp import style

def qa(question: str, answer: str) -> rx.Component:
    return rx.cond(
        question == "",
        rx.box(
            rx.text(answer, style=style.answer_style),
            text_align="left",
        ),
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

def documents() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text(State.current_status),
            rx.container(
                rx.foreach(State.next_steps, 
                    lambda step: rx.text(step)),
            ),
            rx.foreach(State.required_documents,
                lambda doc: rx.text(doc)),
            rx.text(State.additional_info),
        ),
        width="100%",
    )

def documents_formarea() -> rx.Component:
    return rx.vstack(
        docu_chat(),
        rx.hstack(
            rx.input(
                placeholder="Enter your form code here.",
                value=State.form_code,
                style=style.input_style,
                on_change=State.set_form_code,
            ),
            rx.button(
                "Submit",
                on_click=State.answer,
                style=style.button_style,
            ),
            padding="10px",
            width="100%",
        ),
    )

def docu_chat() -> rx.Component:
    return rx.box(
        rx.foreach(
            State.chat_history,
            lambda messages: qa(messages[0], messages[1]),
        )
    )

def docu_chatmodel() -> rx.Component:
    return rx.hstack(
            rx.vstack(
                docu_chat(),
                documents_formarea(),
                align="center",
                margin_top="20vh"
            )
        )

__all__ = ["chatmodel"]