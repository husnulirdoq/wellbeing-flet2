import flet as ft
import requests
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "https://husnulirdoq-wellbeing-backend.hf.space")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyCTJ-9XV1DUQKFHPSRs5HYPLg8VW6DfoUM")
FIREBASE_SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_SIGN_UP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
WEB_PORT = int(os.getenv("WEB_PORT", "0")) or None

BG         = "#F0F4FF"
PRIMARY    = "#4F46E5"
PRIMARY_LIGHT = "#EEF2FF"
WHITE      = "#FFFFFF"
TEXT_DARK  = "#1E1B4B"
TEXT_GRAY  = "#6B7280"
TEAL       = "#0D9488"
GREEN      = "#22C55E"
RED        = "#EF4444"
ORANGE     = "#F97316"

def main(page: ft.Page):
    page.title = "WellBeing Tracker"
    page.bgcolor = BG
    page.padding = 0
    page.scroll = ft.ScrollMode.HIDDEN

    session = {"token": None, "username": None}

    # ── API helpers ────────────────────────────────────────
    def api_headers():
        return {"Authorization": f"Bearer {session['token']}"}

    def api_get(path, retries=2):
        for i in range(retries + 1):
            try:
                r = requests.get(f"{API_URL}{path}", headers=api_headers(), timeout=15)
                if r.status_code == 200 and r.text.strip():
                    return r.json()
                return None
            except:
                if i < retries:
                    import time; time.sleep(2)
        return None

    def api_post(path, data, retries=2):
        for i in range(retries + 1):
            try:
                r = requests.post(f"{API_URL}{path}", json=data, headers=api_headers(), timeout=15)
                if r.status_code in (200, 201) and r.text.strip():
                    return r.json()
                return None
            except:
                if i < retries:
                    import time; time.sleep(2)
        return None

    def api_patch(path):
        try:
            r = requests.patch(f"{API_URL}{path}", headers=api_headers(), timeout=15)
            return r.json() if r.status_code == 200 and r.text.strip() else None
        except:
            return None

    def api_delete(path):
        try:
            r = requests.delete(f"{API_URL}{path}", headers=api_headers(), timeout=15)
            return r.status_code == 200
        except:
            return False

    # ── UI helpers ─────────────────────────────────────────
    def card(content, padding=16, margin=ft.Margin(0, 0, 0, 12)):
        return ft.Container(
            content=content, bgcolor=WHITE, border_radius=16,
            padding=padding, margin=margin,
            shadow=ft.BoxShadow(blur_radius=8, color="#1A000000", offset=ft.Offset(0, 2)),
        )

    def filled_btn(text, on_click, bgcolor=PRIMARY, color=WHITE, expand=False):
        return ft.FilledButton(text=text, on_click=on_click, expand=expand,
            style=ft.ButtonStyle(bgcolor=bgcolor, color=color,
                                 shape=ft.RoundedRectangleBorder(radius=8)))

    # ── Drawer navigation ──────────────────────────────────
    def make_drawer():
        items = [
            (ft.Icons.DASHBOARD, "Dashboard"),
            (ft.Icons.BOOK, "Journal"),
            (ft.Icons.CHECK_BOX, "To-Do"),
            (ft.Icons.CHAT, "AI Assistant"),
            (ft.Icons.MONITOR_HEART, "Tracking"),
            (ft.Icons.SHOPPING_BAG, "Shop"),
        ]

        def drawer_item(icon, label):
            return ft.ListTile(
                leading=ft.Icon(icon, color=PRIMARY),
                title=ft.Text(label, color=TEXT_DARK, size=14),
                on_click=lambda e, l=label: (close_drawer(), navigate(l)),
            )

        return ft.NavigationDrawer(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("🌿 WellBeing", size=20, weight=ft.FontWeight.BOLD, color=PRIMARY),
                        ft.Text(session.get("username") or "", size=12, color=TEXT_GRAY),
                    ], spacing=4),
                    padding=ft.Padding(16, 40, 16, 16),
                    bgcolor=PRIMARY_LIGHT,
                ),
                ft.Divider(),
                *[drawer_item(i, l) for i, l in items],
                ft.Divider(),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.LOGOUT, color=RED),
                    title=ft.Text("Logout", color=RED, size=14),
                    on_click=lambda e: do_logout(),
                ),
            ],
        )

    def open_drawer():
        page.drawer = make_drawer()
        page.drawer.open = True
        page.update()

    def close_drawer():
        if page.drawer:
            page.drawer.open = False
            page.update()

    def do_logout():
        session["token"] = None
        session["username"] = None
        close_drawer()
        navigate("Login")

    # ── App bar ────────────────────────────────────────────
    def appbar(title: str):
        return ft.AppBar(
            leading=ft.IconButton(ft.Icons.MENU, on_click=lambda e: open_drawer(),
                                  icon_color=TEXT_DARK),
            title=ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            bgcolor=WHITE,
            elevation=1,
        )

    # ── Page container ─────────────────────────────────────
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

    # ══════════════════════════════════════════════════════
    # LOGIN
    # ══════════════════════════════════════════════════════
    def login_page():
        email_ref = ft.Ref[ft.TextField]()
        pass_ref  = ft.Ref[ft.TextField]()
        uname_ref = ft.Ref[ft.TextField]()
        err_ref   = ft.Ref[ft.Text]()
        mode = {"register": False}

        def do_login(e):
            email = email_ref.current.value or ""
            pwd   = pass_ref.current.value or ""
            if not email or not pwd:
                err_ref.current.value = "Email dan password wajib diisi."
                page.update(); return
            err_ref.current.value = "⏳ Logging in..."
            page.update()
            try:
                r = requests.post(
                    f"{FIREBASE_SIGN_IN_URL}?key={FIREBASE_API_KEY}",
                    json={"email": email, "password": pwd, "returnSecureToken": True},
                    timeout=15)
                if r.status_code != 200:
                    err_ref.current.value = f"❌ {r.json().get('error',{}).get('message','Login gagal.')}"
                    page.update(); return
                id_token = r.json()["idToken"]
                r2 = requests.post(f"{API_URL}/auth/firebase",
                                   json={"id_token": id_token, "email": email}, timeout=20)
                if r2.status_code == 200 and r2.text.strip():
                    d = r2.json()
                    session["token"]    = d["access_token"]
                    session["username"] = d["username"]
                    navigate("Dashboard")
                else:
                    err_ref.current.value = "❌ Server error. Coba lagi."
                    page.update()
            except:
                err_ref.current.value = "❌ Tidak bisa terhubung. Coba lagi."
                page.update()

        def do_register(e):
            email = email_ref.current.value or ""
            pwd   = pass_ref.current.value or ""
            uname = uname_ref.current.value or ""
            if not email or not pwd or not uname:
                err_ref.current.value = "Semua field wajib diisi."
                page.update(); return
            err_ref.current.value = "⏳ Registering..."
            page.update()
            try:
                r = requests.post(
                    f"{FIREBASE_SIGN_UP_URL}?key={FIREBASE_API_KEY}",
                    json={"email": email, "password": pwd, "returnSecureToken": True},
                    timeout=15)
                if r.status_code != 200:
                    err_ref.current.value = f"❌ {r.json().get('error',{}).get('message','Registrasi gagal.')}"
                    page.update(); return
                id_token = r.json()["idToken"]
                r2 = requests.post(f"{API_URL}/auth/firebase",
                                   json={"id_token": id_token, "email": email, "username": uname},
                                   timeout=20)
                if r2.status_code == 200 and r2.text.strip():
                    d = r2.json()
                    session["token"]    = d["access_token"]
                    session["username"] = d["username"]
                    navigate("Dashboard")
                else:
                    err_ref.current.value = "❌ Server error. Coba lagi."
                    page.update()
            except:
                err_ref.current.value = "❌ Tidak bisa terhubung. Coba lagi."
                page.update()

        def toggle_mode(e):
            mode["register"] = not mode["register"]
            uname_ref.current.visible = mode["register"]
            toggle_btn.current.content.value = "Sudah punya akun? Login" if mode["register"] else "Belum punya akun? Daftar"
            action_btn.current.text = "DAFTAR" if mode["register"] else "MASUK"
            page.update()

        toggle_btn = ft.Ref[ft.TextButton]()
        action_btn = ft.Ref[ft.FilledButton]()

        return ft.Container(
            content=ft.Column([
                ft.Container(height=60),
                ft.Text("🌿", size=48, text_align=ft.TextAlign.CENTER),
                ft.Text("WellBeing Tracker", size=22, weight=ft.FontWeight.BOLD,
                        color=TEXT_DARK, text_align=ft.TextAlign.CENTER),
                ft.Text("Track your wellness journey", size=13, color=TEXT_GRAY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=32),
                ft.TextField(ref=uname_ref, label="Username", border_radius=8, visible=False),
                ft.Container(height=4),
                ft.TextField(ref=email_ref, label="Email", border_radius=8,
                             keyboard_type=ft.KeyboardType.EMAIL),
                ft.Container(height=8),
                ft.TextField(ref=pass_ref, label="Password", password=True,
                             can_reveal_password=True, border_radius=8),
                ft.Container(height=4),
                ft.Text(ref=err_ref, value="", color=RED, size=12),
                ft.Container(height=8),
                ft.FilledButton(ref=action_btn, text="MASUK",
                    on_click=lambda e: do_register(e) if mode["register"] else do_login(e),
                    expand=True,
                    style=ft.ButtonStyle(bgcolor=TEAL, color=WHITE,
                                         shape=ft.RoundedRectangleBorder(radius=8),
                                         padding=ft.Padding(0, 14, 0, 14))),
                ft.Container(height=8),
                ft.TextButton(ref=toggle_btn,
                    content=ft.Text("Belum punya akun? Daftar", color=PRIMARY),
                    on_click=toggle_mode),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               spacing=0, scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(24, 0, 24, 24),
            alignment=ft.Alignment(0, 0),
            expand=True, bgcolor=BG,
        )


    # ══════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════
    def dashboard_page():
        summary = api_get("/entries/summary")
        s = summary.get("summary") if summary else None
        journals = api_get("/journal") or []
        todos    = api_get("/todos") or []
        done_todos = [t for t in todos if t.get("done")]
        wellness = int(((s["avg_mood"] + s["avg_energy"] + (10 - s["avg_stress"])) / 30) * 100) if s else 0

        def stat_card(icon, value, label, color):
            return ft.Container(
                content=ft.Column([
                    ft.Text(icon, size=24),
                    ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(label, size=10, color=TEXT_GRAY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                bgcolor=WHITE, border_radius=12, padding=12, expand=True,
                shadow=ft.BoxShadow(blur_radius=6, color="#1A000000", offset=ft.Offset(0, 2)),
            )

        activities = []
        for j in journals[:3]:
            activities.append(("📖", j["title"], j.get("created_at", "")[:10]))
        for t in done_todos[:2]:
            activities.append(("✅", t["title"], "completed"))

        goals = [
            ("Journal entries", min(len(journals)/10, 1.0), PRIMARY),
            ("Tasks completed", min(len(done_todos)/10, 1.0), GREEN),
            ("Wellness score",  wellness/100, ORANGE),
        ]

        return ft.Column([
            appbar("Dashboard"),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Welcome, {session['username']}! 👋",
                            size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Container(height=12),
                    ft.Row([
                        stat_card("📖", len(journals), "Journals", PRIMARY),
                        ft.Container(width=8),
                        stat_card("✅", len(done_todos), "Tasks Done", GREEN),
                        ft.Container(width=8),
                        stat_card("💪", f"{wellness}%", "Wellness", ORANGE),
                        ft.Container(width=8),
                        stat_card("📝", s["total_entries"] if s else 0, "Logs", RED),
                    ]),
                    ft.Container(height=16),
                    card(ft.Column([
                        ft.Text("Recent Activity", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(height=8),
                        *([ft.Row([ft.Text(i, size=16), ft.Column([
                            ft.Text(t, size=13, color=TEXT_DARK),
                            ft.Text(tm, size=11, color=TEXT_GRAY),
                          ], spacing=1, expand=True)], spacing=10)
                          for i, t, tm in activities]
                          if activities else [ft.Text("No activity yet.", color=TEXT_GRAY, size=13)]),
                    ], spacing=10)),
                    card(ft.Column([
                        ft.Text("Today's Goals", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(height=8),
                        *[ft.Column([
                            ft.Row([ft.Text(l, size=13, color=TEXT_DARK, expand=True),
                                    ft.Text(f"{int(p*100)}%", size=12, color=c)]),
                            ft.ProgressBar(value=p, color=c, bgcolor="#E5E7EB", height=6),
                          ], spacing=4) for l, p, c in goals],
                    ], spacing=10)),
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=16, expand=True,
            ),
        ], spacing=0, expand=True)

    # ══════════════════════════════════════════════════════
    # JOURNAL
    # ══════════════════════════════════════════════════════
    def journal_page():
        entries_col = ft.Ref[ft.Column]()
        dlg_ref     = ft.Ref[ft.AlertDialog]()
        new_title   = ft.Ref[ft.TextField]()
        new_body    = ft.Ref[ft.TextField]()
        new_mood    = ft.Ref[ft.Dropdown]()
        mood_icons  = {"happy": "😊", "neutral": "😐", "sad": "😔", "excited": "🤩"}

        def load():
            data = api_get("/journal") or []
            if entries_col.current is None: return
            entries_col.current.controls = [entry_card(e) for e in data] or \
                [ft.Text("No entries yet.", color=TEXT_GRAY)]
            page.update()

        def entry_card(e):
            return card(ft.Column([
                ft.Row([
                    ft.Text(mood_icons.get(e.get("mood","neutral"),"😊"), size=20),
                    ft.Column([
                        ft.Text(e["title"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Text(e.get("created_at","")[:10], size=11, color=TEXT_GRAY),
                    ], spacing=1, expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED,
                                  on_click=lambda ev, eid=e["id"]: (api_delete(f"/journal/{eid}"), load())),
                ], spacing=8),
                ft.Text(e.get("body",""), size=13, color=TEXT_GRAY),
            ], spacing=6))

        def save(e):
            api_post("/journal", {"title": new_title.current.value or "Untitled",
                                   "body": new_body.current.value or "",
                                   "mood": new_mood.current.value or "neutral"})
            dlg_ref.current.open = False
            new_title.current.value = ""
            new_body.current.value = ""
            load()

        dlg = ft.AlertDialog(ref=dlg_ref, title=ft.Text("New Entry"),
            content=ft.Column([
                ft.Dropdown(ref=new_mood, label="Mood", value="neutral",
                            options=[ft.dropdown.Option(k,v) for k,v in mood_icons.items()]),
                ft.TextField(ref=new_title, label="Title"),
                ft.TextField(ref=new_body, label="How was your day?", multiline=True, min_lines=3),
            ], spacing=10, tight=True, width=320),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dlg_ref.current,"open",False) or page.update()),
                ft.FilledButton("Save", on_click=save,
                    style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE)),
            ])
        page.overlay.append(dlg)

        col = ft.Column(ref=entries_col, controls=[ft.Text("Loading...", color=TEXT_GRAY)])

        result = ft.Column([
            appbar("Journal"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Journal", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                        ft.FilledButton("+ New", on_click=lambda e: setattr(dlg_ref.current,"open",True) or page.update(),
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ]),
                    ft.Container(height=12),
                    col,
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=16, expand=True,
            ),
        ], spacing=0, expand=True)

        load()
        return result

    # ══════════════════════════════════════════════════════
    # TO-DO
    # ══════════════════════════════════════════════════════
    def todo_page():
        task_input   = ft.Ref[ft.TextField]()
        priority_ref = ft.Ref[ft.Dropdown]()
        category_ref = ft.Ref[ft.Dropdown]()
        tasks_col    = ft.Ref[ft.Column]()
        priority_colors = {"high": RED, "medium": ORANGE, "low": GREEN}

        def load():
            data = api_get("/todos") or []
            active = [t for t in data if not t.get("done")]
            if tasks_col.current is None: return
            tasks_col.current.controls = [task_row(t) for t in active] or \
                [ft.Text("No tasks yet.", color=TEXT_GRAY)]
            page.update()

        def task_row(task):
            return ft.Row([
                ft.Checkbox(on_change=lambda e, tid=task["id"]: (api_patch(f"/todos/{tid}/done"), load())),
                ft.Column([
                    ft.Text(task["title"], size=13, color=TEXT_DARK),
                    ft.Container(content=ft.Text(task.get("category",""), size=10, color=TEXT_GRAY),
                                 bgcolor="#F3F4F6", border_radius=4, padding=ft.Padding(6,2,6,2)),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.FLAG, color=priority_colors.get(task.get("priority","medium"), ORANGE), size=16),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=TEXT_GRAY,
                              on_click=lambda e, tid=task["id"]: (api_delete(f"/todos/{tid}"), load())),
            ], spacing=6)

        def add_task(e):
            title = task_input.current.value or ""
            if not title.strip(): return
            api_post("/todos", {"title": title,
                                "category": category_ref.current.value or "Wellness",
                                "priority": priority_ref.current.value or "medium"})
            task_input.current.value = ""
            load()

        col = ft.Column(ref=tasks_col, controls=[ft.Text("Loading...", color=TEXT_GRAY)], spacing=10)

        result = ft.Column([
            appbar("To-Do"),
            ft.Container(
                content=ft.Column([
                    card(ft.Column([
                        ft.Text("Add New Task", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(height=6),
                        ft.TextField(ref=task_input, hint_text="What do you need to do?", border_radius=8),
                        ft.Row([
                            ft.Dropdown(ref=priority_ref, value="medium", expand=True,
                                options=[ft.dropdown.Option("high","High"),
                                         ft.dropdown.Option("medium","Medium"),
                                         ft.dropdown.Option("low","Low")]),
                            ft.Dropdown(ref=category_ref, value="Wellness", expand=True,
                                options=[ft.dropdown.Option(c) for c in
                                         ["Wellness","Health","Fitness","Work","Personal"]]),
                        ], spacing=8),
                        ft.FilledButton("+ Add Task", on_click=add_task, expand=True,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ], spacing=8)),
                    card(ft.Column([
                        ft.Text("Active Tasks", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(height=6),
                        col,
                    ], spacing=0)),
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=16, expand=True,
            ),
        ], spacing=0, expand=True)

        load()
        return result


    # ══════════════════════════════════════════════════════
    # AI ASSISTANT
    # ══════════════════════════════════════════════════════
    def ai_assistant_page():
        chat_col  = ft.Ref[ft.Column]()
        input_ref = ft.Ref[ft.TextField]()
        messages  = [{"role": "bot", "text": "Hello! I'm your AI health assistant. How can I help you today?", "time": "now"}]

        def bubble(msg):
            is_bot = msg["role"] == "bot"
            return ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(msg["text"], size=13, color=TEXT_DARK if is_bot else WHITE),
                        ft.Text(msg["time"], size=10, color=TEXT_GRAY if is_bot else "#CBD5E1"),
                    ], spacing=2, tight=True),
                    bgcolor=WHITE if is_bot else PRIMARY,
                    border_radius=12, padding=10,
                    shadow=ft.BoxShadow(blur_radius=4, color="#0A000000"),
                    width=260,
                ),
            ], alignment=ft.MainAxisAlignment.START if is_bot else ft.MainAxisAlignment.END)

        def rebuild():
            if chat_col.current:
                chat_col.current.controls = [bubble(m) for m in messages]
                page.update()

        def send(e):
            text = input_ref.current.value or ""
            if not text.strip(): return
            now = datetime.now().strftime("%I:%M %p")
            messages.append({"role": "user", "text": text, "time": now})
            input_ref.current.value = ""
            rebuild()
            result = api_post("/analyze", {"text": text})
            if result:
                analysis = result.get("analysis", [[]])
                if analysis and isinstance(analysis[0], list):
                    top = max(analysis[0], key=lambda x: x["score"])
                    reply = f"I sense you're feeling {top['label'].lower()}. Would you like some wellness tips?"
                else:
                    reply = "Thanks for sharing! How can I help with your wellness journey?"
            else:
                reply = "I'm here to help! Tell me more about how you're feeling."
            messages.append({"role": "bot", "text": reply, "time": datetime.now().strftime("%I:%M %p")})
            rebuild()

        return ft.Column([
            appbar("AI Assistant"),
            ft.Container(
                content=ft.Column([
                    ft.Text("AI Health Assistant", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text("Get personalized wellness advice", size=12, color=TEXT_GRAY),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Column(ref=chat_col, controls=[bubble(m) for m in messages],
                                          spacing=10, scroll=ft.ScrollMode.AUTO),
                        expand=True, bgcolor=BG, border_radius=12, padding=12,
                    ),
                    ft.Container(height=8),
                    ft.Row([
                        ft.TextField(ref=input_ref, hint_text="Type a message...",
                                     expand=True, border_radius=8, on_submit=send),
                        ft.FilledButton("Send", on_click=send,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ], spacing=8),
                ], expand=True),
                padding=16, expand=True,
            ),
        ], spacing=0, expand=True)

    # ══════════════════════════════════════════════════════
    # TRACKING
    # ══════════════════════════════════════════════════════
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

        def load():
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

        def save(e):
            api_post("/tracking", values)

        def sync_garmin(e):
            result = api_post("/garmin/sync", {})
            if result:
                for k in fields:
                    values[k] = result.get(k, 0)
                update_all()

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
                    ft.Container(content=ft.Text(d["icon"], size=22),
                                 bgcolor=BG, border_radius=10, padding=8),
                    ft.Column([
                        ft.Text(d["label"], size=12, color=TEXT_GRAY),
                        ft.Row([
                            ft.Text(ref=value_refs[key], value=str(values[key]),
                                    size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text(d["unit"], size=12, color=TEXT_GRAY),
                        ], spacing=4),
                    ], spacing=2, expand=True),
                ], spacing=10),
                ft.Row([
                    ft.Text("Progress", size=11, color=TEXT_GRAY, expand=True),
                    ft.Text(f"Target: {d['target']} {d['unit']}", size=11, color=TEXT_GRAY),
                ]),
                ft.ProgressBar(ref=bar_refs[key], value=progress,
                               color=d["color"], bgcolor="#E5E7EB", height=6),
                ft.Container(height=4),
                ft.Row([
                    ft.FilledButton("-", on_click=dec, expand=True,
                        style=ft.ButtonStyle(bgcolor=PRIMARY_LIGHT, color=PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=8))),
                    ft.FilledButton("+", on_click=inc, expand=True,
                        style=ft.ButtonStyle(bgcolor=PRIMARY_LIGHT, color=PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=8))),
                ], spacing=8),
            ], spacing=6))

        result = ft.Column([
            appbar("Tracking"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Mind & Body", size=18, weight=ft.FontWeight.BOLD,
                                color=TEXT_DARK, expand=True),
                        ft.FilledButton("🔄 Garmin", on_click=sync_garmin,
                            style=ft.ButtonStyle(bgcolor="#111827", color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                        ft.Container(width=6),
                        ft.FilledButton("💾 Save", on_click=save,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ]),
                    ft.Container(height=8),
                    *[make_card(k) for k in fields.keys()],
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=16, expand=True,
            ),
        ], spacing=0, expand=True)

        load()
        return result

    # ══════════════════════════════════════════════════════
    # SHOP
    # ══════════════════════════════════════════════════════
    def shop_page():
        cart_count = ft.Ref[ft.Text]()
        cart_items = []

        products = [
            {"name": "Yoga Mat Premium",      "desc": "Non-slip, eco-friendly",        "price": 49.99, "rating": 4.8, "emoji": "🧘"},
            {"name": "Meditation Cushion",     "desc": "Comfortable meditation pillow", "price": 34.99, "rating": 4.6, "emoji": "🌸"},
            {"name": "Resistance Bands",       "desc": "Set of 5 resistance bands",     "price": 24.99, "rating": 4.7, "emoji": "💪"},
            {"name": "Essential Oil Diffuser", "desc": "Ultrasonic aromatherapy",       "price": 39.99, "rating": 4.9, "emoji": "🌺"},
            {"name": "Smart Water Bottle",     "desc": "Temperature tracking",          "price": 29.99, "rating": 4.5, "emoji": "💧"},
            {"name": "Sleep Mask",             "desc": "Blackout sleep mask",           "price": 19.99, "rating": 4.3, "emoji": "😴"},
            {"name": "Fitness Tracker",        "desc": "Heart rate & step counter",     "price": 89.99, "rating": 4.8, "emoji": "⌚"},
            {"name": "Protein Powder",         "desc": "Plant-based protein blend",     "price": 44.99, "rating": 4.6, "emoji": "🥤"},
        ]

        def add_to_cart(e, p):
            cart_items.append(p)
            if cart_count.current:
                cart_count.current.value = str(len(cart_items))
                page.update()

        def checkout(e):
            if not cart_items: return
            total = sum(p["price"] for p in cart_items)
            result = api_post("/payment/checkout", {
                "items": [{"name": p["name"], "price": p["price"], "quantity": 1} for p in cart_items],
                "total": total,
            })
            if result and result.get("redirect_url"):
                page.launch_url(result["redirect_url"])

        def product_card(p):
            return card(ft.Row([
                ft.Text(p["emoji"], size=32),
                ft.Column([
                    ft.Text(p["name"], size=13, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text(p["desc"], size=11, color=TEXT_GRAY),
                    ft.Text(f"⭐ {p['rating']}  ${p['price']}", size=12, color=ORANGE),
                ], spacing=2, expand=True),
                ft.FilledButton("Add", on_click=lambda e, prod=p: add_to_cart(e, prod),
                    style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE,
                                         shape=ft.RoundedRectangleBorder(radius=8),
                                         padding=ft.Padding(10, 6, 10, 6))),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER))

        return ft.Column([
            appbar("Shop"),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Wellness Shop", size=18, weight=ft.FontWeight.BOLD,
                                color=TEXT_DARK, expand=True),
                        ft.FilledButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SHOPPING_CART, color=WHITE, size=16),
                                ft.Text(ref=cart_count, value="0", color=WHITE, size=13),
                            ], spacing=4, tight=True),
                            on_click=checkout,
                            style=ft.ButtonStyle(bgcolor=PRIMARY,
                                                 shape=ft.RoundedRectangleBorder(radius=8))),
                    ]),
                    ft.Container(height=8),
                    *[product_card(p) for p in products],
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                padding=16, expand=True,
            ),
        ], spacing=0, expand=True)

    # ── Start ──────────────────────────────────────────────
    navigate("Login")
    page.add(page_container)

if WEB_PORT:
    ft.app(main, port=WEB_PORT)
else:
    ft.app(main)
