import flet as ft
import requests
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://backend:8000")

BG = "#F0F4FF"
PRIMARY = "#4F46E5"
PRIMARY_LIGHT = "#EEF2FF"
WHITE = "#FFFFFF"
TEXT_DARK = "#1E1B4B"
TEXT_GRAY = "#6B7280"
TEAL = "#0D9488"
GREEN = "#22C55E"
RED = "#EF4444"
ORANGE = "#F97316"

def main(page: ft.Page):
    page.title = "WellBeing Tracker"
    page.bgcolor = BG
    page.padding = 0
    page.scroll = ft.ScrollMode.HIDDEN

    session = {"token": None, "username": None}

    def api_headers():
        return {"Authorization": f"Bearer {session['token']}"}

    def api_get(path):
        try:
            r = requests.get(f"{API_URL}{path}", headers=api_headers(), timeout=10)
            if r.status_code == 200 and r.text.strip():
                return r.json()
            return None
        except:
            return None

    def api_post(path, data):
        try:
            r = requests.post(f"{API_URL}{path}", json=data, headers=api_headers(), timeout=10)
            if r.status_code in (200, 201) and r.text.strip():
                return r.json()
            return None
        except:
            return None

    def api_patch(path):
        try:
            r = requests.patch(f"{API_URL}{path}", headers=api_headers(), timeout=10)
            if r.status_code == 200 and r.text.strip():
                return r.json()
            return None
        except:
            return None

    def api_delete(path):
        try:
            r = requests.delete(f"{API_URL}{path}", headers=api_headers(), timeout=10)
            return r.status_code == 200
        except:
            return False

    def card(content, padding=20, margin=0):
        return ft.Container(
            content=content, bgcolor=WHITE, border_radius=16,
            padding=padding, margin=margin,
            shadow=ft.BoxShadow(blur_radius=8, color="#1A000000", offset=ft.Offset(0, 2)),
        )

    def filled_btn(text, on_click, bgcolor=PRIMARY, color=WHITE, width=None):
        return ft.FilledButton(text=text, on_click=on_click, width=width,
            style=ft.ButtonStyle(bgcolor=bgcolor, color=color,
                                 shape=ft.RoundedRectangleBorder(radius=8)))

    def navbar(active: str):
        items = [("🏠", "Dashboard"), ("📖", "Journal"), ("✅", "To-Do"),
                 ("💬", "AI Assistant"), ("📊", "Tracking"), ("🛍️", "Shop")]

        def nav_btn(icon, label):
            is_active = label == active
            return ft.FilledButton(
                content=ft.Row([ft.Text(icon, size=14),
                                 ft.Text(label, size=12, weight=ft.FontWeight.W_500)],
                                spacing=4, tight=True),
                on_click=lambda e, l=label: navigate(l),
                style=ft.ButtonStyle(
                    bgcolor=PRIMARY_LIGHT if is_active else "transparent",
                    color=PRIMARY if is_active else TEXT_DARK,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.Padding(12, 6, 12, 6),
                ),
            )

        def do_logout(e):
            session["token"] = None
            session["username"] = None
            navigate("Login")

        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Text("〜", size=20, color=PRIMARY, weight=ft.FontWeight.BOLD),
                    ft.Text("WellBeing Tracker", size=15, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ], spacing=6),
                ft.Row([
                    *[nav_btn(i, l) for i, l in items],
                    ft.FilledButton("Logout", on_click=do_logout,
                        style=ft.ButtonStyle(bgcolor=RED, color=WHITE,
                                             shape=ft.RoundedRectangleBorder(radius=8),
                                             padding=ft.Padding(12, 6, 12, 6))),
                ], spacing=2),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=WHITE, padding=ft.Padding(24, 12, 24, 12),
            shadow=ft.BoxShadow(blur_radius=4, color="#0A000000", offset=ft.Offset(0, 1)),
        )

    # ── LOGIN / REGISTER ───────────────────────────────────
    def login_page():
        email_ref = ft.Ref[ft.TextField]()
        pass_ref  = ft.Ref[ft.TextField]()
        uname_ref = ft.Ref[ft.TextField]()
        err_ref   = ft.Ref[ft.Text]()
        is_register = ft.Ref[ft.Text]()
        mode = {"register": False}

        def do_login(e):
            email = email_ref.current.value or ""
            pwd   = pass_ref.current.value or ""
            if not email or not pwd:
                err_ref.current.value = "Email dan password wajib diisi."
                page.update(); return
            try:
                r = requests.post(f"{API_URL}/auth/login",
                                  data={"username": email, "password": pwd}, timeout=10)
                if r.status_code == 200 and r.text.strip():
                    data = r.json()
                    session["token"]    = data["access_token"]
                    session["username"] = data["username"]
                    navigate("Dashboard")
                else:
                    err_ref.current.value = "Email atau password salah."
                    page.update()
            except Exception as ex:
                err_ref.current.value = f"Error: {ex}"
                page.update()

        def do_register(e):
            email = email_ref.current.value or ""
            pwd   = pass_ref.current.value or ""
            uname = uname_ref.current.value or ""
            if not email or not pwd or not uname:
                err_ref.current.value = "Semua field wajib diisi."
                page.update(); return
            try:
                r = requests.post(f"{API_URL}/auth/register",
                                  json={"email": email, "password": pwd, "username": uname}, timeout=10)
                if r.status_code == 200 and r.text.strip():
                    data = r.json()
                    session["token"]    = data["access_token"]
                    session["username"] = data["username"]
                    navigate("Dashboard")
                else:
                    detail = r.json().get("detail", "Registrasi gagal.") if r.text.strip() else "Registrasi gagal."
                    err_ref.current.value = detail
                    page.update()
            except Exception as ex:
                err_ref.current.value = f"Error: {ex}"
                page.update()

        def toggle_mode(e):
            mode["register"] = not mode["register"]
            uname_ref.current.visible = mode["register"]
            is_register.current.content.value = "Sudah punya akun? Login" if mode["register"] else "Belum punya akun? Daftar"
            page.update()

        return ft.Container(
            content=ft.Column([
                ft.Container(height=80),
                ft.Text("WELLBEING LOGIN", size=24, weight=ft.FontWeight.BOLD,
                        color=TEXT_DARK, text_align=ft.TextAlign.CENTER),
                ft.Container(height=40),
                ft.TextField(ref=uname_ref, label="Username", border_radius=8, visible=False),
                ft.Container(height=8),
                ft.TextField(ref=email_ref, label="Email", border_radius=8,
                             keyboard_type=ft.KeyboardType.EMAIL),
                ft.Container(height=12),
                ft.TextField(ref=pass_ref, label="Password", password=True,
                             can_reveal_password=True, border_radius=8),
                ft.Container(height=8),
                ft.Text(ref=err_ref, value="", color=RED, size=12),
                ft.Container(height=8),
                ft.FilledButton("MASUK", on_click=lambda e: do_register(e) if mode["register"] else do_login(e),
                    width=200,
                    style=ft.ButtonStyle(bgcolor=TEAL, color=WHITE,
                                         shape=ft.RoundedRectangleBorder(radius=8),
                                         padding=ft.Padding(0, 14, 0, 14))),
                ft.Container(height=12),
                ft.TextButton(ref=is_register, content=ft.Text("Belum punya akun? Daftar", color=PRIMARY), on_click=toggle_mode),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, width=460),
            alignment=ft.Alignment(0, 0), expand=True, bgcolor=BG,
        )


    # ── DASHBOARD ──────────────────────────────────────────
    def dashboard_page():
        summary_ref = ft.Ref[ft.Column]()

        def stat_card(icon, value, label, color):
            return card(ft.Column([
                ft.Text(icon, size=26),
                ft.Text(str(value), size=26, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=11, color=TEXT_GRAY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4), padding=20)

        # Load real data
        summary = api_get("/entries/summary")
        s = summary.get("summary") if summary else None
        journals = api_get("/journal") or []
        todos    = api_get("/todos") or []
        done_todos = [t for t in todos if t.get("done")]

        wellness_score = 0
        if s:
            wellness_score = int(((s["avg_mood"] + s["avg_energy"] + (10 - s["avg_stress"])) / 30) * 100)

        activities = []
        for j in journals[:3]:
            dt = j.get("created_at", "")[:10]
            activities.append(("📖", j["title"], dt))
        for t in done_todos[:2]:
            activities.append(("✅", t["title"], "completed"))

        goals = [
            ("Journal entries", min(len(journals) / 10, 1.0), PRIMARY),
            ("Tasks completed", min(len(done_todos) / 10, 1.0), GREEN),
            ("Wellness score", wellness_score / 100, ORANGE),
        ]

        def activity_row(icon, text, time):
            return ft.Row([
                ft.Text(icon, size=18),
                ft.Column([
                    ft.Text(text, size=13, color=TEXT_DARK),
                    ft.Text(time, size=11, color=TEXT_GRAY),
                ], spacing=1, expand=True),
            ], spacing=10)

        def goal_row(label, progress, color):
            return ft.Column([
                ft.Row([
                    ft.Text(label, size=13, color=TEXT_DARK, expand=True),
                    ft.Text(f"{int(progress*100)}%", size=12, color=color),
                ]),
                ft.ProgressBar(value=progress, color=color, bgcolor="#E5E7EB", height=6),
            ], spacing=5)

        return ft.Column([
            navbar("Dashboard"),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Welcome Back, {session['username']}! 👋",
                            size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Container(height=16),
                    ft.Row([
                        stat_card("📖", len(journals), "Journal Entries", PRIMARY),
                        stat_card("✅", len(done_todos), "Tasks Completed", GREEN),
                        stat_card("💪", f"{wellness_score}%", "Wellness Score", ORANGE),
                        stat_card("📝", s["total_entries"] if s else 0, "Wellbeing Logs", RED),
                    ], spacing=16),
                    ft.Container(height=20),
                    ft.Row([
                        card(ft.Column([
                            ft.Text("Recent Activity", size=15, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Container(height=10),
                            *([activity_row(i, t, tm) for i, t, tm in activities] if activities else [ft.Text("No activity yet.", size=13, color=TEXT_GRAY)]),
                        ], spacing=10), padding=20),
                        card(ft.Column([
                            ft.Text("Today's Goals", size=15, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Container(height=10),
                            *[goal_row(l, p, c) for l, p, c in goals],
                        ], spacing=12), padding=20),
                    ], spacing=16, expand=True),
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=24, expand=True,
            ),
        ], spacing=0, expand=True)

    # ── JOURNAL ────────────────────────────────────────────
    def journal_page():
        entries_col = ft.Ref[ft.Column]()
        dlg_ref     = ft.Ref[ft.AlertDialog]()
        new_title   = ft.Ref[ft.TextField]()
        new_body    = ft.Ref[ft.TextField]()
        new_mood    = ft.Ref[ft.Dropdown]()

        mood_icons = {"happy": "😊", "neutral": "😐", "sad": "😔", "excited": "🤩"}

        def load_entries():
            data = api_get("/journal") or []
            if entries_col.current is None:
                return
            entries_col.current.controls = [entry_card(e) for e in data] or \
                [ft.Text("No journal entries yet.", color=TEXT_GRAY)]
            page.update()

        def entry_card(e):
            dt = e.get("created_at", "")[:10]
            return card(ft.Column([
                ft.Row([
                    ft.Text(mood_icons.get(e.get("mood", "neutral"), "😊"), size=20),
                    ft.Column([
                        ft.Text(e["title"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, size=11, color=TEXT_GRAY),
                                ft.Text(dt, size=11, color=TEXT_GRAY)], spacing=3),
                    ], spacing=2, expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED,
                                  on_click=lambda ev, eid=e["id"]: delete_entry(eid)),
                ], spacing=10),
                ft.Container(height=6),
                ft.Text(e.get("body", ""), size=13, color=TEXT_GRAY),
            ]), margin=ft.Margin(0, 0, 0, 12))

        def delete_entry(eid):
            api_delete(f"/journal/{eid}")
            load_entries()

        def save_entry(e):
            api_post("/journal", {
                "title": new_title.current.value or "Untitled",
                "body":  new_body.current.value or "",
                "mood":  new_mood.current.value or "neutral",
            })
            dlg_ref.current.open = False
            new_title.current.value = ""
            new_body.current.value = ""
            load_entries()

        dlg = ft.AlertDialog(
            ref=dlg_ref, title=ft.Text("New Journal Entry"),
            content=ft.Column([
                ft.Dropdown(ref=new_mood, label="Mood", value="neutral", width=200,
                            options=[ft.dropdown.Option(k, v) for k, v in mood_icons.items()]),
                ft.TextField(ref=new_title, label="Title"),
                ft.TextField(ref=new_body, label="How was your day?", multiline=True, min_lines=3),
            ], spacing=12, tight=True, width=400),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dlg_ref.current, "open", False) or page.update()),
                ft.FilledButton("Save", on_click=save_entry,
                                style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE)),
            ],
        )
        page.overlay.append(dlg)

        col = ft.Column(ref=entries_col, controls=[ft.Text("Loading...", color=TEXT_GRAY)])

        def open_dlg(e):
            dlg_ref.current.open = True
            page.update()

        result = ft.Column([
            navbar("Journal"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Journal", size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                        ft.FilledButton("+ New Entry", on_click=open_dlg,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ]),
                    ft.Container(height=16),
                    col,
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=24, expand=True,
            ),
        ], spacing=0, expand=True)

        load_entries()
        return result


    # ── TO-DO ──────────────────────────────────────────────
    def todo_page():
        task_input   = ft.Ref[ft.TextField]()
        priority_ref = ft.Ref[ft.Dropdown]()
        category_ref = ft.Ref[ft.Dropdown]()
        tasks_col    = ft.Ref[ft.Column]()
        priority_colors = {"high": RED, "medium": ORANGE, "low": GREEN}

        def load_tasks():
            data = api_get("/todos") or []
            active = [t for t in data if not t.get("done")]
            if tasks_col.current is None:
                return
            tasks_col.current.controls = [task_row(t) for t in active] or \
                [ft.Text("No tasks yet.", color=TEXT_GRAY)]
            page.update()

        def task_row(task):
            def complete(e, tid=task["id"]):
                api_patch(f"/todos/{tid}/done")
                load_tasks()

            def remove(e, tid=task["id"]):
                api_delete(f"/todos/{tid}")
                load_tasks()

            return ft.Row([
                ft.Checkbox(on_change=complete),
                ft.Column([
                    ft.Text(task["title"], size=13, color=TEXT_DARK),
                    ft.Container(
                        content=ft.Text(task.get("category", ""), size=10, color=TEXT_GRAY),
                        bgcolor="#F3F4F6", border_radius=4, padding=ft.Padding(6, 2, 6, 2),
                    ),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.FLAG, color=priority_colors.get(task.get("priority", "medium"), ORANGE), size=16),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=TEXT_GRAY, on_click=remove),
            ], spacing=8)

        def add_task(e):
            title = task_input.current.value or ""
            if not title.strip():
                return
            api_post("/todos", {
                "title":    title,
                "category": category_ref.current.value or "Wellness",
                "priority": priority_ref.current.value or "medium",
            })
            task_input.current.value = ""
            load_tasks()

        col = ft.Column(ref=tasks_col, controls=[ft.Text("Loading...", color=TEXT_GRAY)], spacing=12)

        result = ft.Column([
            navbar("To-Do"),
            ft.Container(
                content=ft.Column([
                    ft.Text("To-Do List", size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Container(height=16),
                    card(ft.Column([
                        ft.Text("Add New Task", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(height=8),
                        ft.Row([
                            ft.TextField(ref=task_input, hint_text="What do you need to do?",
                                         expand=True, border_radius=8),
                            ft.FilledButton("+ Add", on_click=add_task,
                                style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                     shape=ft.RoundedRectangleBorder(radius=8))),
                        ], spacing=8),
                        ft.Row([
                            ft.Dropdown(ref=priority_ref, value="medium", width=160,
                                options=[ft.dropdown.Option("high", "High Priority"),
                                         ft.dropdown.Option("medium", "Medium Priority"),
                                         ft.dropdown.Option("low", "Low Priority")]),
                            ft.Dropdown(ref=category_ref, value="Wellness", width=140,
                                options=[ft.dropdown.Option(c) for c in
                                         ["Wellness", "Health", "Fitness", "Work", "Personal"]]),
                        ], spacing=8),
                    ], spacing=8)),
                    ft.Container(height=16),
                    card(ft.Column([
                        ft.Text("Active Tasks", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(height=8),
                        col,
                    ])),
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=24, expand=True,
            ),
        ], spacing=0, expand=True)

        load_tasks()
        return result

    # ── AI ASSISTANT ───────────────────────────────────────
    def ai_assistant_page():
        chat_col  = ft.Ref[ft.Column]()
        input_ref = ft.Ref[ft.TextField]()
        messages  = [{"role": "bot", "text": "Hello! I'm your AI health assistant. I can help you with wellness advice, nutrition tips, exercise recommendations, and general health questions. How can I assist you today?", "time": "now"}]

        def msg_bubble(msg):
            is_bot = msg["role"] == "bot"
            return ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(msg["text"], size=13, color=TEXT_DARK if is_bot else WHITE),
                        ft.Text(msg["time"], size=10, color=TEXT_GRAY if is_bot else "#CBD5E1"),
                    ], spacing=3, tight=True),
                    bgcolor=WHITE if is_bot else PRIMARY,
                    border_radius=12, padding=12,
                    shadow=ft.BoxShadow(blur_radius=4, color="#0A000000"),
                    width=420,
                ),
            ], alignment=ft.MainAxisAlignment.START if is_bot else ft.MainAxisAlignment.END)

        def rebuild_chat():
            if chat_col.current:
                chat_col.current.controls = [msg_bubble(m) for m in messages]
                page.update()

        def send_msg(e):
            text = input_ref.current.value or ""
            if not text.strip():
                return
            now = datetime.now().strftime("%I:%M %p")
            messages.append({"role": "user", "text": text, "time": now})
            input_ref.current.value = ""
            rebuild_chat()
            result = api_post("/analyze", {"text": text})
            if result:
                analysis = result.get("analysis", [[]])
                if analysis and isinstance(analysis[0], list):
                    top = max(analysis[0], key=lambda x: x["score"])
                    reply = f"I sense you're feeling {top['label'].lower()}. Remember, taking care of your wellbeing is important. Would you like some tips?"
                else:
                    reply = "Thanks for sharing! How can I help you further with your wellness journey?"
            else:
                reply = "I'm here to help! Could you tell me more about how you're feeling?"
            messages.append({"role": "bot", "text": reply, "time": datetime.now().strftime("%I:%M %p")})
            rebuild_chat()

        return ft.Column([
            navbar("AI Assistant"),
            ft.Container(
                content=ft.Column([
                    ft.Text("AI Health Assistant", size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text("Get personalized wellness advice and health tips", size=13, color=TEXT_GRAY),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Column(ref=chat_col, controls=[msg_bubble(m) for m in messages],
                                          spacing=12, scroll=ft.ScrollMode.AUTO),
                        expand=True, bgcolor=BG, border_radius=12, padding=16,
                    ),
                    ft.Container(height=12),
                    ft.Row([
                        ft.TextField(ref=input_ref, hint_text="Type your message...",
                                     expand=True, border_radius=8, on_submit=send_msg),
                        ft.FilledButton("Send", on_click=send_msg,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ], spacing=8),
                ], expand=True),
                padding=24, expand=True,
            ),
        ], spacing=0, expand=True)


    # ── TRACKING ───────────────────────────────────────────
    def tracking_page():
        fields = {
            "sleep":      {"label": "Sleep",      "unit": "hours",   "target": 8,  "icon": "🌙", "color": PRIMARY},
            "exercise":   {"label": "Exercise",   "unit": "minutes", "target": 45, "icon": "🏃", "color": GREEN},
            "water":      {"label": "Water",       "unit": "glasses", "target": 8,  "icon": "💧", "color": "#06B6D4"},
            "heart_rate": {"label": "Heart Rate", "unit": "bpm",     "target": 70, "icon": "❤️", "color": RED},
            "meditation": {"label": "Meditation", "unit": "minutes", "target": 20, "icon": "🧘", "color": "#A855F7"},
        }
        values = {k: 0 for k in fields}
        value_refs = {k: ft.Ref[ft.Text]() for k in fields}
        bar_refs   = {k: ft.Ref[ft.ProgressBar]() for k in fields}

        def load_today():
            data = api_get("/tracking/today") or {}
            for k in fields:
                values[k] = data.get(k, 0)
            update_all()

        def update_all():
            for k in fields:
                if value_refs[k].current:
                    value_refs[k].current.value = str(values[k])
                if bar_refs[k].current:
                    bar_refs[k].current.value = min(values[k] / fields[k]["target"], 1.0)
            page.update()

        def save_tracking(e):
            api_post("/tracking", values)

        def sync_garmin(e):
            result = api_post("/garmin/sync", {})
            if result:
                for k in fields:
                    values[k] = result.get(k, 0)
                update_all()
            else:
                pass  # silently fail if Garmin not configured

        def make_card(key):
            d = fields[key]
            progress = min(values[key] / d["target"], 1.0)

            def dec(e, k=key):
                values[k] = max(0, values[k] - 1)
                update_all()

            def inc(e, k=key):
                values[k] += 1
                update_all()

            return card(ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(d["icon"], size=20),
                                 bgcolor=BG, border_radius=10, padding=8),
                    ft.Column([
                        ft.Text(d["label"], size=12, color=TEXT_GRAY),
                        ft.Row([
                            ft.Text(ref=value_refs[key], value=str(values[key]),
                                    size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text(d["unit"], size=12, color=TEXT_GRAY),
                        ], spacing=4),
                    ], spacing=2),
                ], spacing=10),
                ft.Container(height=8),
                ft.Row([
                    ft.Text("Progress", size=11, color=TEXT_GRAY, expand=True),
                    ft.Text(f"Target: {d['target']} {d['unit']}", size=11, color=TEXT_GRAY),
                ]),
                ft.ProgressBar(ref=bar_refs[key], value=progress,
                               color=d["color"], bgcolor="#E5E7EB", height=6),
                ft.Container(height=8),
                ft.Row([
                    ft.FilledButton("-", on_click=dec, expand=True,
                        style=ft.ButtonStyle(bgcolor=PRIMARY_LIGHT, color=PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=8))),
                    ft.FilledButton("+", on_click=inc, expand=True,
                        style=ft.ButtonStyle(bgcolor=PRIMARY_LIGHT, color=PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=8))),
                ], spacing=8),
            ], spacing=4))

        keys = list(fields.keys())
        result = ft.Column([
            navbar("Tracking"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Mind & Body Tracking", size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                        ft.FilledButton("� Sync Garmin", on_click=lambda e: sync_garmin(e),
                            style=ft.ButtonStyle(bgcolor="#000000", color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                        ft.Container(width=8),
                        ft.FilledButton("�💾 Save Today", on_click=save_tracking,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ]),
                    ft.Container(height=16),
                    ft.Row([make_card(k) for k in keys[:3]], spacing=16),
                    ft.Container(height=16),
                    ft.Row([make_card(k) for k in keys[3:]], spacing=16),
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=24, expand=True,
            ),
        ], spacing=0, expand=True)

        load_today()
        return result

    # ── SHOP ───────────────────────────────────────────────
    def shop_page():
        cart_count = ft.Ref[ft.Text]()
        cart_items = []

        products = [
            {"name": "Yoga Mat Premium",      "desc": "Non-slip, eco-friendly yoga mat",   "price": 49.99, "rating": 4.8, "emoji": "🧘"},
            {"name": "Meditation Cushion",     "desc": "Comfortable meditation pillow",     "price": 34.99, "rating": 4.6, "emoji": "🌸"},
            {"name": "Resistance Bands Set",   "desc": "Set of 5 resistance bands",         "price": 24.99, "rating": 4.7, "emoji": "💪"},
            {"name": "Essential Oil Diffuser", "desc": "Ultrasonic aromatherapy diffuser",  "price": 39.99, "rating": 4.9, "emoji": "🌺"},
            {"name": "Smart Water Bottle",     "desc": "Temperature tracking bottle",       "price": 29.99, "rating": 4.5, "emoji": "💧"},
            {"name": "Sleep Mask Premium",     "desc": "Blackout sleep mask",               "price": 19.99, "rating": 4.3, "emoji": "😴"},
            {"name": "Fitness Tracker",        "desc": "Heart rate & step counter",         "price": 89.99, "rating": 4.8, "emoji": "⌚"},
            {"name": "Protein Powder",         "desc": "Plant-based protein blend",         "price": 44.99, "rating": 4.6, "emoji": "🥤"},
        ]

        def add_to_cart(e, product):
            cart_items.append(product)
            if cart_count.current:
                cart_count.current.value = str(len(cart_items))
                page.update()

        def checkout(e):
            if not cart_items:
                return
            total = sum(p["price"] for p in cart_items)
            result = api_post("/payment/checkout", {
                "items": [{"name": p["name"], "price": p["price"], "quantity": 1} for p in cart_items],
                "total": total,
            })
            if result and result.get("redirect_url"):
                page.launch_url(result["redirect_url"])

        def product_card(p):
            return card(ft.Column([
                ft.Text(p["emoji"], size=36, text_align=ft.TextAlign.CENTER),
                ft.Text(p["name"], size=13, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.Text(p["desc"], size=11, color=TEXT_GRAY),
                ft.Text(f"⭐ {p['rating']}", size=11, color=ORANGE),
                ft.Row([
                    ft.Text(f"${p['price']}", size=15, weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                    ft.FilledButton("+ Add", on_click=lambda e, prod=p: add_to_cart(e, prod),
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                             shape=ft.RoundedRectangleBorder(radius=6),
                                             padding=ft.Padding(10, 6, 10, 6))),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=6), padding=16)

        categories = ["All", "Fitness", "Wellness", "Health", "Technology", "Nutrition"]

        return ft.Column([
            navbar("Shop"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Wellness Shop", size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                        ft.FilledButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SHOPPING_CART, color=WHITE, size=16),
                                ft.Text("Cart", color=WHITE, size=13),
                                ft.Container(
                                    content=ft.Text(ref=cart_count, value="0", size=11, color=PRIMARY),
                                    bgcolor=WHITE, border_radius=10, padding=ft.Padding(6, 2, 6, 2),
                                ),
                            ], spacing=6, tight=True),
                            on_click=checkout,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, shape=ft.RoundedRectangleBorder(radius=8)),
                        ),
                    ]),
                    ft.Container(height=12),
                    ft.Row([
                        ft.FilledButton(c, style=ft.ButtonStyle(
                            bgcolor=PRIMARY if c == "All" else WHITE,
                            color=WHITE if c == "All" else TEXT_DARK,
                            shape=ft.RoundedRectangleBorder(radius=20),
                            side=ft.BorderSide(1, "#E5E7EB"),
                        )) for c in categories
                    ], spacing=8, wrap=True),
                    ft.Container(height=16),
                    ft.GridView(controls=[product_card(p) for p in products],
                                runs_count=4, max_extent=260, spacing=16, run_spacing=16, expand=True),
                ], expand=True),
                padding=24, expand=True,
            ),
        ], spacing=0, expand=True)

    # ── ROUTER ─────────────────────────────────────────────
    page_container = ft.Container(expand=True)

    def navigate(dest: str):
        if dest != "Login" and not session["token"]:
            dest = "Login"
        pages = {
            "Login":        login_page,
            "Dashboard":    dashboard_page,
            "Journal":      journal_page,
            "To-Do":        todo_page,
            "AI Assistant": ai_assistant_page,
            "Tracking":     tracking_page,
            "Shop":         shop_page,
        }
        page_container.content = pages.get(dest, login_page)()
        page.update()

    navigate("Login")
    page.add(page_container)

ft.app(main, port=8080)
