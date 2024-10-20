import reflex as rx
from rxconfig import config
from jobs.job_scraper import State
from chatapp import style

def jobs() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.foreach (
                State.job_results,
                lambda job: rx.text(job),
            ),
            width="100%",
        )
    )

