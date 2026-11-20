from typing import Optional

import flet as ft


@ft.control("HealthConnect")
class HealthConnect(ft.LayoutControl):
    request_id: str
    on_result: Optional[ft.EventHandler[ft.Event]] = None
