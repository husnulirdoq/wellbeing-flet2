import flet as ft
import requests
import os
from datetime import datetime

API_URL          = os.getenv("API_URL", "https://husnulirdoq-wellbeing-backend.hf.space")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyCTJ-9XV1DUQKFHPSRs5HYPLg8VW6DfoUM")
FB_SIGNIN        = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FB_SIGNUP        = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
WEB_PORT         = int(os.getenv("WEB_PORT", "0")) or None

BG      = "#F0F4FF"
PRIMARY = "#4F46E5"
PL      = "#EEF2FF"
WHITE   = "#FFFFFF"
DARK    = "#1E1B4B"
GRAY    = "#6B7280"
TEAL    = "#0D9488"
GREEN   = "#22C55E"
RED     = "#EF4444"
ORANGE  = "#F97316"

def main(page: ft.Page):
    page.title   = "WellBeing"
    page.bgcolor = BG
    page.padding = 0
    page.scroll  = None

    session = {"token": None, "username": None}

    # ── API ────────────────────────────────────────────────
    def hdrs():
        return {"Authorization": f"Bearer {session['token']}"}

    def api_get(path):
        try:
            r = requests.get(f"{API_URL}{path}", headers=hdrs(), timeout=15)
            return r.json() if r.ok and r.text.strip() else None
        except: return None

    def api_post(path, data):
        try:
            r = requests.post(f"{API_URL}{path}", json=data, headers=hdrs(), timeout=15)
            return r.json() if r.ok and r.text.strip() else None
        except: return None

    def api_patch(path):
        try:
            r = requests.patch(f"{API_URL}{path}", headers=hdrs(), timeout=15)
            return r.ok
        except: return False

    def api_delete(path):
        try:
            r = requests.delete(f"{API_URL}{path}", headers=hdrs(), timeout=15)
            return r.ok
        except: return False

    # ── Helpers ────────────────────────────────────────────
    def card(content, mb=12):
        return ft.Container(
            content=content, bgcolor=WHITE, border_radius=16,
            padding=16, margin=ft.Margin(0, 0, 0, mb),
            shadow=ft.BoxShadow(blur_radius=8, color="#15000000", offset=ft.Offset(0, 2)),
        )

    def mbtn(label, on_click, bg=PRIMARY, fg=WHITE, expand=False):
        return ft.Button(
            content=ft.Text(label, color=fg, size=14, weight=ft.FontWeight.W_500),
            on_click=on_click, expand=expand,
            style=ft.ButtonStyle(
                bgcolor=bg, color=fg,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(16, 12, 16, 12),
            ),
        )

    # ── Content area ───────────────────────────────────────
    content_area = ft.Container(expand=True)

    def show_page(widget):
        content_area.content = widget
        page.update()

    # ══════════════════════════════════════════════════════
    # LOGIN PAGE (no bottom nav)
    # ══════════════════════════════════════════════════════
    def build_login():
        r_email = ft.Ref[ft.TextField]()
        r_pass  = ft.Ref[ft.TextField]()
        r_uname = ft.Ref[ft.TextField]()
        r_err   = ft.Ref[ft.Text]()
        r_label = ft.Ref[ft.Text]()
        r_link  = ft.Ref[ft.Text]()
        mode    = {"reg": False}

        def do_login(e):
            email = r_email.current.value or "" if r_email.current else ""
            pwd   = r_pass.current.value or "" if r_pass.current else ""
            def set_err(msg):
                if r_err.current: r_err.current.value = msg; page.update()
            if not email or not pwd:
                set_err("Email dan password wajib diisi."); return
            set_err("⏳ Logging in...")
            try:
                r = requests.post(f"{FB_SIGNIN}?key={FIREBASE_API_KEY}",
                    json={"email": email, "password": pwd, "returnSecureToken": True}, timeout=15)
                if not r.ok:
                    set_err(f"❌ {r.json().get('error',{}).get('message','Login gagal.')}"); return
                tok = r.json()["idToken"]
                r2 = requests.post(f"{API_URL}/auth/firebase",
                    json={"id_token": tok, "email": email}, timeout=20)
                if r2.ok and r2.text.strip():
                    d = r2.json()
                    session["token"]    = d["access_token"]
                    session["username"] = d["username"]
                    go_main()
                else:
                    set_err("❌ Server error. Coba lagi.")
            except:
                set_err("❌ Tidak bisa terhubung.")

        def do_register(e):
            email = r_email.current.value or "" if r_email.current else ""
            pwd   = r_pass.current.value or "" if r_pass.current else ""
            uname = r_uname.current.value or "" if r_uname.current else ""
            def set_err(msg):
                if r_err.current: r_err.current.value = msg; page.update()
            if not email or not pwd or not uname:
                set_err("Semua field wajib diisi."); return
            set_err("⏳ Registering...")
            try:
                r = requests.post(f"{FB_SIGNUP}?key={FIREBASE_API_KEY}",
                    json={"email": email, "password": pwd, "returnSecureToken": True}, timeout=15)
                if not r.ok:
                    set_err(f"❌ {r.json().get('error',{}).get('message','Gagal.')}"); return
                tok = r.json()["idToken"]
                r2 = requests.post(f"{API_URL}/auth/firebase",
                    json={"id_token": tok, "email": email, "username": uname}, timeout=20)
                if r2.ok and r2.text.strip():
                    d = r2.json()
                    session["token"]    = d["access_token"]
                    session["username"] = d["username"]
                    go_main()
                else:
                    set_err("❌ Server error. Coba lagi.")
            except:
                set_err("❌ Tidak bisa terhubung.")

        def toggle(e):
            mode["reg"] = not mode["reg"]
            r_uname.current.visible = mode["reg"]
            r_label.current.value   = "DAFTAR" if mode["reg"] else "MASUK"
            r_link.current.value    = "Sudah punya akun? Login" if mode["reg"] else "Belum punya akun? Daftar"
            page.update()

        return ft.Container(
            expand=True, bgcolor=WHITE,
            padding=ft.Padding(28, 0, 28, 28),
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Container(height=64),
                    ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[
                        ft.Image(src="/assets/logo.png", width=110, height=110),
                    ]),
                    ft.Container(height=12),
                    ft.Text("WellBeing Tracker", size=22,
                            weight=ft.FontWeight.BOLD, color=DARK,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("Track your wellness journey", size=13,
                            color=GRAY, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=32),
                    ft.TextField(ref=r_uname, label="Username",
                                 border_radius=10, visible=False),
                    ft.Container(height=4),
                    ft.TextField(ref=r_email, label="Email",
                                 keyboard_type=ft.KeyboardType.EMAIL,
                                 border_radius=10),
                    ft.Container(height=8),
                    ft.TextField(ref=r_pass, label="Password",
                                 password=True, can_reveal_password=True,
                                 border_radius=10),
                    ft.Container(height=4),
                    ft.Text(ref=r_err, value="", color=RED, size=12),
                    ft.Container(height=8),
                    ft.Button(
                        content=ft.Text(ref=r_label, value="MASUK",
                                        color=WHITE, size=15,
                                        weight=ft.FontWeight.BOLD),
                        on_click=lambda e: do_register(e) if mode["reg"] else do_login(e),
                        expand=True,
                        style=ft.ButtonStyle(
                            bgcolor=TEAL, color=WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.Padding(0, 16, 0, 16),
                        ),
                    ),
                    ft.Container(height=8),
                    ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[
                        ft.TextButton(
                            content=ft.Text(ref=r_link,
                                            value="Belum punya akun? Daftar",
                                            color=PRIMARY),
                            on_click=toggle,
                        ),
                    ]),
                ],
            ),
        )


    # ══════════════════════════════════════════════════════
    # MAIN APP with Bottom NavigationBar
    # ══════════════════════════════════════════════════════
    def go_main():
        page.clean()

        # Pages
        def pg_dashboard():
            r_content = ft.Ref[ft.Column]()

            def build_content(summary, journals, todos):
                s        = (summary or {}).get("summary")
                done     = [t for t in todos if t.get("done")]
                wellness = int(((s["avg_mood"]+s["avg_energy"]+(10-s["avg_stress"]))/30)*100) if s else 0

                def stat(icon, val, lbl, color):
                    return ft.Container(
                        expand=True, bgcolor=WHITE, border_radius=14, padding=12,
                        shadow=ft.BoxShadow(blur_radius=6, color="#12000000", offset=ft.Offset(0,2)),
                        content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[
                            ft.Text(icon, size=22),
                            ft.Text(str(val), size=20, weight=ft.FontWeight.BOLD, color=color),
                            ft.Text(lbl, size=10, color=GRAY),
                        ]),
                    )

                acts = (
                    [ft.Row(spacing=10, controls=[
                        ft.Text(i, size=16),
                        ft.Column(spacing=1, expand=True, controls=[
                            ft.Text(t, size=13, color=DARK),
                            ft.Text(tm, size=11, color=GRAY),
                        ]),
                    ]) for i,t,tm in
                    [("📖",j["title"],j.get("created_at","")[:10]) for j in journals[:3]] +
                    [("✅",t["title"],"done") for t in done[:2]]]
                    or [ft.Text("No activity yet.", color=GRAY, size=13)]
                )

                goals = [
                    ("Journals",  min(len(journals)/10,1.0), PRIMARY),
                    ("Tasks done",min(len(done)/10,1.0),     GREEN),
                    ("Wellness",  wellness/100,               ORANGE),
                ]

                if r_content.current:
                    r_content.current.controls = [
                        ft.Text(f"Hi, {session['username']}! 👋",
                                size=18, weight=ft.FontWeight.BOLD, color=DARK),
                        ft.Container(height=12),
                        ft.Row(spacing=8, controls=[
                            stat("📖", len(journals), "Journals", PRIMARY),
                            stat("✅", len(done),     "Tasks",    GREEN),
                            stat("💪", f"{wellness}%","Wellness", ORANGE),
                            stat("📝", s["total_entries"] if s else 0, "Logs", RED),
                        ]),
                        ft.Container(height=12),
                        card(ft.Column(spacing=10, controls=[
                            ft.Text("Recent Activity", size=14, weight=ft.FontWeight.BOLD, color=DARK),
                            *acts,
                        ])),
                        card(ft.Column(spacing=10, controls=[
                            ft.Text("Today's Goals", size=14, weight=ft.FontWeight.BOLD, color=DARK),
                            *[ft.Column(spacing=4, controls=[
                                ft.Row(controls=[
                                    ft.Text(l, size=13, color=DARK, expand=True),
                                    ft.Text(f"{int(p*100)}%", size=12, color=c),
                                ]),
                                ft.ProgressBar(value=p, color=c, bgcolor="#E5E7EB", height=6),
                            ]) for l,p,c in goals],
                        ])),
                    ]
                    page.update()

            def load():
                import threading
                summary  = api_get("/entries/summary")
                journals = api_get("/journal") or []
                todos    = api_get("/todos") or []
                build_content(summary, journals, todos)

            import threading
            threading.Thread(target=load, daemon=True).start()

            return ft.Container(expand=True, padding=16,
                content=ft.Column(ref=r_content, scroll=ft.ScrollMode.AUTO, expand=True,
                    controls=[
                        ft.Text(f"Hi, {session['username']}! 👋",
                                size=18, weight=ft.FontWeight.BOLD, color=DARK),
                        ft.Container(height=20),
                        ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[
                            ft.ProgressRing(width=32, height=32, color=PRIMARY),
                            ft.Container(width=12),
                            ft.Text("Loading...", color=GRAY, size=13),
                        ]),
                    ]),
            )

        def pg_journal():
            col     = ft.Ref[ft.Column]()
            dlg     = ft.Ref[ft.AlertDialog]()
            r_title = ft.Ref[ft.TextField]()
            r_body  = ft.Ref[ft.TextField]()
            r_mood  = ft.Ref[ft.Dropdown]()
            moods   = {"happy":"😊","neutral":"😐","sad":"😔","excited":"🤩"}
            local_entries = []

            def render():
                if col.current is None: return
                col.current.controls = [entry(e) for e in local_entries] or \
                    [ft.Text("No entries yet.", color=GRAY)]
                page.update()

            def load():
                data = api_get("/journal") or []
                local_entries.clear()
                local_entries.extend(data)
                render()

            def entry(e):
                is_temp = e.get("_temp", False)
                return card(ft.Column(spacing=6, controls=[
                    ft.Row(spacing=8, controls=[
                        ft.Text(moods.get(e.get("mood","neutral"),"😊"), size=20),
                        ft.Column(spacing=1, expand=True, controls=[
                            ft.Text(e["title"], size=14, weight=ft.FontWeight.BOLD,
                                    color=GRAY if is_temp else DARK),
                            ft.Text("Saving..." if is_temp else e.get("created_at","")[:10],
                                    size=11, color=GRAY),
                        ]),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED,
                            on_click=lambda ev, eid=e.get("id"): (
                                api_delete(f"/journal/{eid}") if eid else None,
                                local_entries.remove(e) if e in local_entries else None,
                                render(),
                            ) if not is_temp else None),
                    ]),
                    ft.Text(e.get("body",""), size=13, color=GRAY),
                ]))

            def save(e):
                title = r_title.current.value or "Untitled"
                body  = r_body.current.value or ""
                mood  = r_mood.current.value or "neutral"
                # Close dialog immediately
                dlg.current.open = False
                r_title.current.value = ""
                r_body.current.value  = ""
                # Optimistic — add temp entry instantly
                temp = {"title": title, "body": body, "mood": mood,
                        "created_at": datetime.now().isoformat(), "_temp": True, "id": None}
                local_entries.insert(0, temp)
                render()
                # Send to API in background
                import threading
                def do_save():
                    result = api_post("/journal", {"title": title, "body": body, "mood": mood})
                    if temp in local_entries:
                        local_entries.remove(temp)
                    if result:
                        local_entries.insert(0, result)
                    render()
                threading.Thread(target=do_save, daemon=True).start()

            dialog = ft.AlertDialog(
                ref=dlg, title=ft.Text("New Entry"),
                content=ft.Column(tight=True, width=300, spacing=10, controls=[
                    ft.Dropdown(ref=r_mood, label="Mood", value="neutral",
                        options=[ft.dropdown.Option(k,v) for k,v in moods.items()]),
                    ft.TextField(ref=r_title, label="Title"),
                    ft.TextField(ref=r_body, label="How was your day?",
                                 multiline=True, min_lines=3),
                ]),
                actions=[
                    ft.TextButton(content=ft.Text("Cancel", color=GRAY),
                        on_click=lambda e: setattr(dlg.current,"open",False) or page.update()),
                    ft.Button(content=ft.Text("Save", color=WHITE), on_click=save,
                        style=ft.ButtonStyle(bgcolor=PRIMARY,
                                             shape=ft.RoundedRectangleBorder(radius=8))),
                ],
            )
            page.overlay.append(dialog)

            entries_col = ft.Column(ref=col, controls=[ft.Text("Loading...", color=GRAY)])
            import threading
            threading.Thread(target=load, daemon=True).start()

            return ft.Container(expand=True, padding=16,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, controls=[
                    ft.Row(controls=[
                        ft.Text("Journal", size=18, weight=ft.FontWeight.BOLD, color=DARK, expand=True),
                        ft.Button(content=ft.Text("+ New", color=WHITE, size=13),
                            on_click=lambda e: setattr(dlg.current,"open",True) or page.update(),
                            style=ft.ButtonStyle(bgcolor=PRIMARY,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding(12,8,12,8))),
                    ]),
                    ft.Container(height=12),
                    entries_col,
                ]),
            )

        def pg_todo():
            col     = ft.Ref[ft.Column]()
            r_input = ft.Ref[ft.TextField]()
            r_prio  = ft.Ref[ft.Dropdown]()
            r_cat   = ft.Ref[ft.Dropdown]()
            pcolors = {"high":RED,"medium":ORANGE,"low":GREEN}

            def load():
                data   = api_get("/todos") or []
                active = [t for t in data if not t.get("done")]
                if col.current is None: return
                col.current.controls = [task_row(t) for t in active] or \
                    [ft.Text("No tasks yet.", color=GRAY)]
                page.update()

            def task_row(t):
                is_temp = t.get("_temp", False)
                return ft.Row(spacing=6, controls=[
                    ft.Checkbox(on_change=lambda e, tid=t.get("id"): (
                        api_patch(f"/todos/{tid}/done") if tid else None,
                        load()) if not is_temp else None),
                    ft.Column(spacing=2, expand=True, controls=[
                        ft.Text(t["title"], size=13, color=GRAY if is_temp else DARK),
                        ft.Container(content=ft.Text(
                            "Saving..." if is_temp else t.get("category",""),
                            size=10, color=GRAY),
                            bgcolor="#F3F4F6", border_radius=4, padding=ft.Padding(6,2,6,2)),
                    ]),
                    ft.Icon(ft.Icons.FLAG, color=pcolors.get(t.get("priority","medium"),ORANGE), size=16),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=GRAY,
                        on_click=lambda e, tid=t.get("id"): (
                            api_delete(f"/todos/{tid}") if tid else None,
                            load()) if not is_temp else None),
                ])

            local_tasks = []

            def render_tasks():
                if col.current is None: return
                col.current.controls = [task_row(t) for t in local_tasks if not t.get("done")] or \
                    [ft.Text("No tasks yet.", color=GRAY)]
                page.update()

            def load():
                data = api_get("/todos") or []
                local_tasks.clear()
                local_tasks.extend(data)
                render_tasks()

            def add(e):
                title = r_input.current.value or ""
                if not title.strip(): return
                cat  = r_cat.current.value or "Wellness"
                prio = r_prio.current.value or "medium"
                r_input.current.value = ""
                # Optimistic
                temp = {"title": title, "category": cat, "priority": prio,
                        "done": False, "_temp": True, "id": None}
                local_tasks.insert(0, temp)
                render_tasks()
                # Background save
                import threading
                def do_add():
                    result = api_post("/todos", {"title": title, "category": cat, "priority": prio})
                    if temp in local_tasks:
                        local_tasks.remove(temp)
                    if result:
                        local_tasks.insert(0, result)
                    render_tasks()
                threading.Thread(target=do_add, daemon=True).start()

            tasks_col = ft.Column(ref=col, spacing=10, controls=[ft.Text("Loading...", color=GRAY)])
            import threading
            threading.Thread(target=load, daemon=True).start()

            return ft.Container(expand=True, padding=16,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, controls=[
                    ft.Text("To-Do List", size=18, weight=ft.FontWeight.BOLD, color=DARK),
                    ft.Container(height=12),
                    card(ft.Column(spacing=8, controls=[
                        ft.Text("Add Task", size=14, weight=ft.FontWeight.BOLD, color=DARK),
                        ft.TextField(ref=r_input, hint_text="What do you need to do?", border_radius=10),
                        ft.Row(spacing=8, controls=[
                            ft.Dropdown(ref=r_prio, value="medium", expand=True,
                                options=[ft.dropdown.Option("high","High"),
                                         ft.dropdown.Option("medium","Medium"),
                                         ft.dropdown.Option("low","Low")]),
                            ft.Dropdown(ref=r_cat, value="Wellness", expand=True,
                                options=[ft.dropdown.Option(c) for c in
                                         ["Wellness","Health","Fitness","Work","Personal"]]),
                        ]),
                        ft.Button(content=ft.Text("+ Add Task", color=WHITE, size=14),
                            on_click=add, expand=True,
                            style=ft.ButtonStyle(bgcolor=PRIMARY,
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=ft.Padding(0,12,0,12))),
                    ])),
                    card(ft.Column(spacing=0, controls=[
                        ft.Text("Active Tasks", size=14, weight=ft.FontWeight.BOLD, color=DARK),
                        ft.Container(height=8),
                        tasks_col,
                    ])),
                ]),
            )

        def pg_tracking():
            fields = {
                "sleep":      {"label":"Sleep",     "unit":"hours",  "target":8, "icon":"🌙","color":PRIMARY},
                "exercise":   {"label":"Exercise",  "unit":"minutes","target":45,"icon":"🏃","color":GREEN},
                "water":      {"label":"Water",     "unit":"glasses","target":8, "icon":"💧","color":"#06B6D4"},
                "heart_rate": {"label":"Heart Rate","unit":"bpm",    "target":70,"icon":"❤️","color":RED},
                "meditation": {"label":"Meditation","unit":"minutes","target":20,"icon":"🧘","color":"#A855F7"},
            }
            vals   = {k:0 for k in fields}
            r_vals = {k:ft.Ref[ft.Text]() for k in fields}
            r_bars = {k:ft.Ref[ft.ProgressBar]() for k in fields}

            def load():
                data = api_get("/tracking/today") or {}
                for k in fields: vals[k] = data.get(k, 0)
                update_all()

            def update_all():
                for k in fields:
                    if r_vals[k].current: r_vals[k].current.value = str(vals[k])
                    if r_bars[k].current: r_bars[k].current.value = min(vals[k]/fields[k]["target"],1.0)
                page.update()

            def make_card(key):
                d = fields[key]
                def dec(e, k=key): vals[k] = max(0, vals[k]-1); update_all()
                def inc(e, k=key): vals[k] += 1; update_all()
                return card(ft.Column(spacing=6, controls=[
                    ft.Row(spacing=10, controls=[
                        ft.Container(content=ft.Text(d["icon"],size=20), bgcolor=BG, border_radius=10, padding=8),
                        ft.Column(spacing=2, expand=True, controls=[
                            ft.Text(d["label"], size=12, color=GRAY),
                            ft.Row(spacing=4, controls=[
                                ft.Text(ref=r_vals[key], value="0", size=20, weight=ft.FontWeight.BOLD, color=DARK),
                                ft.Text(d["unit"], size=12, color=GRAY),
                            ]),
                        ]),
                    ]),
                    ft.Row(controls=[
                        ft.Text("Progress", size=11, color=GRAY, expand=True),
                        ft.Text(f"Target: {d['target']} {d['unit']}", size=11, color=GRAY),
                    ]),
                    ft.ProgressBar(ref=r_bars[key], value=0, color=d["color"], bgcolor="#E5E7EB", height=6),
                    ft.Row(spacing=8, controls=[
                        ft.Button(content=ft.Text("-", color=PRIMARY, size=18), on_click=dec, expand=True,
                            style=ft.ButtonStyle(bgcolor=PL, shape=ft.RoundedRectangleBorder(radius=10))),
                        ft.Button(content=ft.Text("+", color=PRIMARY, size=18), on_click=inc, expand=True,
                            style=ft.ButtonStyle(bgcolor=PL, shape=ft.RoundedRectangleBorder(radius=10))),
                    ]),
                ]))

            cards = [make_card(k) for k in fields]
            import threading
            threading.Thread(target=load, daemon=True).start()

            return ft.Container(expand=True, padding=16,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, controls=[
                    ft.Row(controls=[
                        ft.Text("Mind & Body", size=18, weight=ft.FontWeight.BOLD, color=DARK, expand=True),
                        ft.Button(content=ft.Text("🔄 Garmin", color=WHITE, size=12),
                            on_click=lambda e: (api_post("/garmin/sync",{}) and load()),
                            style=ft.ButtonStyle(bgcolor="#111827", shape=ft.RoundedRectangleBorder(radius=8),
                                                 padding=ft.Padding(10,6,10,6))),
                        ft.Container(width=6),
                        ft.Button(content=ft.Text("💾 Save", color=WHITE, size=12),
                            on_click=lambda e: api_post("/tracking", vals),
                            style=ft.ButtonStyle(bgcolor=PRIMARY, shape=ft.RoundedRectangleBorder(radius=8),
                                                 padding=ft.Padding(10,6,10,6))),
                    ]),
                    ft.Container(height=8),
                    *cards,
                ]),
            )

        def pg_more():
            """More page: AI Assistant + Shop + Logout"""
            col   = ft.Ref[ft.Column]()
            r_inp = ft.Ref[ft.TextField]()
            msgs  = [{"role":"bot","text":"Hello! I'm your AI health assistant. How can I help?","time":"now"}]
            cart  = []
            r_cart = ft.Ref[ft.Text]()

            products = [
                {"name":"Yoga Mat",    "desc":"Non-slip mat",      "price":49.99,"emoji":"🧘"},
                {"name":"Meditation Cushion","desc":"Comfy pillow","price":34.99,"emoji":"🌸"},
                {"name":"Resistance Bands","desc":"Set of 5",      "price":24.99,"emoji":"💪"},
                {"name":"Oil Diffuser","desc":"Aromatherapy",       "price":39.99,"emoji":"🌺"},
                {"name":"Water Bottle","desc":"Smart bottle",       "price":29.99,"emoji":"💧"},
                {"name":"Sleep Mask",  "desc":"Blackout mask",      "price":19.99,"emoji":"😴"},
            ]

            def bubble(m):
                is_bot = m["role"] == "bot"
                return ft.Row(
                    alignment=ft.MainAxisAlignment.START if is_bot else ft.MainAxisAlignment.END,
                    controls=[ft.Container(
                        bgcolor=WHITE if is_bot else PRIMARY, border_radius=12, padding=10,
                        width=220,
                        content=ft.Column(spacing=2, tight=True, controls=[
                            ft.Text(m["text"], size=13, color=DARK if is_bot else WHITE),
                            ft.Text(m["time"], size=10, color=GRAY if is_bot else "#CBD5E1"),
                        ]),
                    )],
                )

            def rebuild_chat():
                if col.current:
                    col.current.controls = [bubble(m) for m in msgs]
                    page.update()

            def send(e):
                txt = r_inp.current.value or ""
                if not txt.strip(): return
                now = datetime.now().strftime("%I:%M %p")
                msgs.append({"role":"user","text":txt,"time":now})
                r_inp.current.value = ""
                rebuild_chat()
                res = api_post("/analyze", {"text": txt})
                if res:
                    analysis = res.get("analysis", [[]])
                    if analysis and isinstance(analysis[0], list):
                        top = max(analysis[0], key=lambda x: x["score"])
                        reply = f"I sense you're feeling {top['label'].lower()}. Would you like wellness tips?"
                    else:
                        reply = "Thanks for sharing! How can I help?"
                else:
                    reply = "I'm here to help! Tell me more."
                msgs.append({"role":"bot","text":reply,"time":datetime.now().strftime("%I:%M %p")})
                rebuild_chat()

            def add_cart(e, p):
                cart.append(p)
                if r_cart.current:
                    r_cart.current.value = f"🛒 {len(cart)}"
                    page.update()

            def checkout(e):
                if not cart: return
                total = sum(p["price"] for p in cart)
                res = api_post("/payment/checkout", {
                    "items": [{"name":p["name"],"price":p["price"],"quantity":1} for p in cart],
                    "total": total,
                })
                if res and res.get("redirect_url"):
                    page.launch_url(res["redirect_url"])

            def do_logout(e):
                session["token"] = None
                session["username"] = None
                page.clean()
                page.add(build_login())

            return ft.Container(expand=True, padding=16,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, controls=[
                    # AI Chat
                    ft.Text("AI Health Assistant", size=16, weight=ft.FontWeight.BOLD, color=DARK),
                    ft.Container(height=8),
                    ft.Container(height=280, bgcolor=BG, border_radius=12, padding=10,
                        content=ft.Column(ref=col, spacing=8, scroll=ft.ScrollMode.AUTO,
                                          controls=[bubble(m) for m in msgs])),
                    ft.Row(spacing=8, controls=[
                        ft.TextField(ref=r_inp, hint_text="Type a message...",
                                     expand=True, border_radius=10, on_submit=send),
                        ft.Button(content=ft.Text("Send", color=WHITE, size=13), on_click=send,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, shape=ft.RoundedRectangleBorder(radius=10))),
                    ]),
                    ft.Divider(height=24),
                    # Shop coming soon
                    card(ft.Column(spacing=8, controls=[
                        ft.Row(spacing=10, controls=[
                            ft.Text("🛍️", size=28),
                            ft.Column(spacing=2, expand=True, controls=[
                                ft.Text("Wellness Shop", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                ft.Text("Coming soon — payment gateway in progress.", size=12, color=GRAY),
                            ]),
                        ]),
                    ])),
                    ft.Container(height=16),
                ]),
            )

        # Pages list
        pages = [pg_dashboard, pg_journal, pg_todo, pg_tracking, pg_more]
        current_idx = ft.Ref[ft.NavigationBar]()

        def on_nav(e):
            idx = e.control.selected_index
            content_area.content = pages[idx]()
            page.update()

        nav_bar = ft.NavigationBar(
            ref=current_idx,
            selected_index=0,
            on_change=on_nav,
            bgcolor=WHITE,
            indicator_color=PL,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.BOOK_OUTLINED,
                    selected_icon=ft.Icons.BOOK, label="Journal"),
                ft.NavigationBarDestination(icon=ft.Icons.CHECK_BOX_OUTLINED,
                    selected_icon=ft.Icons.CHECK_BOX, label="To-Do"),
                ft.NavigationBarDestination(icon=ft.Icons.MONITOR_HEART_OUTLINED,
                    selected_icon=ft.Icons.MONITOR_HEART, label="Track"),
                ft.NavigationBarDestination(icon=ft.Icons.MORE_HORIZ,
                    selected_icon=ft.Icons.MORE_HORIZ, label="More"),
            ],
        )

        content_area.content = pg_dashboard()

        page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.AppBar(
                    title=ft.Row(spacing=8, controls=[
                        ft.Image(src="/assets/logo.png", width=28, height=28),
                        ft.Text("WellBeing", size=16, weight=ft.FontWeight.BOLD, color=DARK),
                    ]),
                    bgcolor=WHITE,
                    elevation=1,
                    actions=[
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT_ROUNDED,
                            icon_color=RED,
                            tooltip="Logout",
                            on_click=lambda e: (
                                session.update({"token": None, "username": None}),
                                page.clean(),
                                page.add(build_login()),
                            ),
                        ),
                    ],
                ),
                ft.Container(
                    content=content_area,
                    expand=True,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                nav_bar,
            ]),
        )

    # ── Splash ─────────────────────────────────────────────
    import threading, time

    def splash_then_login():
        splash = ft.Container(
            expand=True, bgcolor=WHITE,
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Image(src="/assets/logo.png", width=140, height=140),
                    ft.Container(height=16),
                    ft.Text("WellBeing Tracker", size=20,
                            weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ft.Container(height=12),
                    ft.ProgressRing(width=32, height=32, color=PRIMARY),
                ],
            ),
        )
        page.add(splash)
        page.update()
        time.sleep(2)
        page.clean()
        page.add(build_login())

    threading.Thread(target=splash_then_login, daemon=True).start()

if WEB_PORT:
    ft.app(main, port=WEB_PORT)
else:
    ft.app(main)
