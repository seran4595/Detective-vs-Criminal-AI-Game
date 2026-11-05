import random
import tkinter as tk
from tkinter import font as tkfont
SIZE = 8
CELL = 64  # pixel size of each board cell

DETECTIVE_ICON = "👮"
CRIMINAL_ICON = "🕵️"
ESCAPE_ICON = "🚪"
OBSTACLE_ICON = "⛰️"

obstacles = {(1, 1), (1, 2), (4, 3), (4, 4), (1, 5), (2, 5), (3, 6), (6, 5), (6, 6)}
escape_points = {(0, 7), (7, 0), (7, 7)}
COL_BG = "#1b1f2a"
COL_PANEL = "#252a3a"
COL_TILE_LIGHT = "#3a4152"
COL_TILE_DARK = "#333a4a"
COL_OBSTACLE = "#5c4a3a"
COL_ESCAPE = "#2f9e5b"
COL_ESCAPE_GLOW = "#49c97a"
COL_DETECTIVE = "#3b82f6"
COL_DETECTIVE_RING = "#93c5fd"
COL_CRIMINAL = "#ef4444"
COL_CRIMINAL_RING = "#fca5a5"
COL_TEXT = "#e5e7eb"
COL_SUBTEXT = "#9aa3b5"
COL_ACCENT = "#f2c14e"
COL_BTN = "#2f3648"
COL_BTN_HOVER = "#3c4560"


def rounded_rect(canvas, x1, y1, x2, y2, r=14, **kwargs):
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Detective vs Criminal")
        self.root.configure(bg=COL_BG)
        self.root.resizable(False, False)

        self.title_font = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        self.status_font = tkfont.Font(family="Segoe UI", size=12)
        self.btn_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.cell_font = tkfont.Font(family="Segoe UI Emoji", size=int(CELL * 0.42))

        self.board_state = [["" for _ in range(SIZE)] for _ in range(SIZE)]
        for (r, c) in obstacles:
            self.board_state[r][c] = "obstacle"
        for (r, c) in escape_points:
            self.board_state[r][c] = "escape"

        self.detective_pos = (0, 0)
        self.criminal_pos = (3, 3)
        self.game_over = False
        self._popup_shapes = []
        self._popup_widgets = []

        # Detective powers
        self.freeze_charges = 2
        self.teleport_charges = 1
        self.trap_charges = 2
        self.active_trap = None  # (pos, previous_kind) while a trap is live

        self._build_layout()
        self._draw_board()

        self.root.bind("<w>", lambda e: self.player_move(-1, 0))
        self.root.bind("<s>", lambda e: self.player_move(1, 0))
        self.root.bind("<a>", lambda e: self.player_move(0, -1))
        self.root.bind("<d>", lambda e: self.player_move(0, 1))
        self.root.bind("<Up>", lambda e: self.player_move(-1, 0))
        self.root.bind("<Down>", lambda e: self.player_move(1, 0))
        self.root.bind("<Left>", lambda e: self.player_move(0, -1))
        self.root.bind("<Right>", lambda e: self.player_move(0, 1))

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_layout(self):
        header = tk.Frame(self.root, bg=COL_BG)
        header.pack(fill="x", padx=18, pady=(16, 4))

        tk.Label(
            header, text="Detective vs Criminal", font=self.title_font,
            bg=COL_BG, fg=COL_TEXT,
        ).pack(side="left")

        self.status_label = tk.Label(
            self.root, text="Your move — catch the criminal before it escapes.",
            font=self.status_font, bg=COL_BG, fg=COL_SUBTEXT,
        )
        self.status_label.pack(fill="x", padx=18, pady=(0, 10))

        board_wrap = tk.Frame(self.root, bg=COL_PANEL, padx=10, pady=10)
        board_wrap.pack(padx=18)

        self.canvas = tk.Canvas(
            board_wrap, width=SIZE * CELL, height=SIZE * CELL,
            bg=COL_PANEL, highlightthickness=0,
        )
        self.canvas.pack()

        controls = tk.Frame(self.root, bg=COL_BG)
        controls.pack(pady=16)

        legend = tk.Frame(self.root, bg=COL_BG)
        legend.pack(pady=(0, 4))
        self._legend_item(legend, DETECTIVE_ICON, "Detective (you)", COL_DETECTIVE)
        self._legend_item(legend, CRIMINAL_ICON, "Criminal (AI)", COL_CRIMINAL)
        self._legend_item(legend, ESCAPE_ICON, "Escape point", COL_ESCAPE)
        self._legend_item(legend, OBSTACLE_ICON, "Obstacle", COL_OBSTACLE)

        self._make_dpad(controls)
        self._make_powers_ui(self.root)

        self.restart_btn = self._make_button(
            self.root, "Restart Game", self.restart, pady_out=(4, 18)
        )

    def _legend_item(self, parent, icon, text, color):
        item = tk.Frame(parent, bg=COL_BG)
        item.pack(side="left", padx=10)
        dot = tk.Canvas(item, width=16, height=16, bg=COL_BG, highlightthickness=0)
        dot.create_oval(2, 2, 14, 14, fill=color, outline="")
        dot.pack(side="left", padx=(0, 6))
        tk.Label(item, text=text, font=("Segoe UI", 9), bg=COL_BG, fg=COL_SUBTEXT).pack(side="left")

    def _make_button(self, parent, text, command, pady_out=(0, 0)):
        btn = tk.Button(
            parent, text=text, command=command, font=self.btn_font,
            bg=COL_BTN, fg=COL_TEXT, activebackground=COL_BTN_HOVER,
            activeforeground=COL_TEXT, relief="flat", bd=0,
            padx=16, pady=8, cursor="hand2",
        )
        btn.pack(pady=pady_out)
        btn.bind("<Enter>", lambda e: btn.config(bg=COL_BTN_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=COL_BTN))
        return btn

    def _make_dpad(self, parent):
        grid = tk.Frame(parent, bg=COL_BG)
        grid.grid(row=0, column=0)

        def dbtn(r, c, text, dr, dc):
            b = tk.Button(
                grid, text=text, font=self.btn_font, width=4, height=2,
                bg=COL_BTN, fg=COL_TEXT, activebackground=COL_BTN_HOVER,
                activeforeground=COL_TEXT, relief="flat", bd=0, cursor="hand2",
                command=lambda: self.player_move(dr, dc),
            )
            b.grid(row=r, column=c, padx=4, pady=4)
            b.bind("<Enter>", lambda e: b.config(bg=COL_BTN_HOVER))
            b.bind("<Leave>", lambda e: b.config(bg=COL_BTN))

        dbtn(0, 1, "▲ W", -1, 0)
        dbtn(1, 0, "◀ A", 0, -1)
        dbtn(1, 2, "D ▶", 0, 1)
        dbtn(2, 1, "▼ S", 1, 0)

    def _make_powers_ui(self, parent):
        wrap = tk.Frame(parent, bg=COL_BG)
        wrap.pack(pady=(2, 6))
        tk.Label(
            wrap, text="Detective Powers", font=("Segoe UI", 10, "bold"),
            bg=COL_BG, fg=COL_ACCENT,
        ).pack()
        row = tk.Frame(wrap, bg=COL_BG)
        row.pack(pady=(4, 0))
        self.freeze_btn = self._make_power_button(row, self.use_freeze)
        self.teleport_btn = self._make_power_button(row, self.use_teleport)
        self.trap_btn = self._make_power_button(row, self.use_trap)
        self._refresh_power_buttons()

    def _make_power_button(self, parent, command):
        btn = tk.Button(
            parent, font=self.btn_font, bg=COL_BTN, fg=COL_TEXT,
            activebackground=COL_BTN_HOVER, activeforeground=COL_TEXT,
            disabledforeground=COL_SUBTEXT, relief="flat", bd=0,
            padx=10, pady=6, cursor="hand2", command=command,
        )
        btn.pack(side="left", padx=6)

        def on_enter(_e):
            if btn["state"] != "disabled":
                btn.config(bg=COL_BTN_HOVER)

        def on_leave(_e):
            if btn["state"] != "disabled":
                btn.config(bg=COL_BTN)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _refresh_power_buttons(self):
        active = not self.game_over
        self.freeze_btn.config(
            text=f"⚡ Freeze ({self.freeze_charges})",
            state=tk.NORMAL if active and self.freeze_charges > 0 else tk.DISABLED,
        )
        self.teleport_btn.config(
            text=f"🧲 Teleport ({self.teleport_charges})",
            state=tk.NORMAL if active and self.teleport_charges > 0 else tk.DISABLED,
        )
        self.trap_btn.config(
            text=f"🚧 Trap ({self.trap_charges})",
            state=tk.NORMAL if active and self.trap_charges > 0 else tk.DISABLED,
        )

    # ------------------------------------------------------------------
    # Detective powers
    # ------------------------------------------------------------------
    def use_freeze(self):
        """Skip the criminal's next turn entirely."""
        if self.game_over or self.freeze_charges <= 0:
            return
        self.freeze_charges -= 1
        self._refresh_power_buttons()
        self._set_status("⚡ Criminal frozen! It loses its turn.", COL_ACCENT)

    def use_teleport(self):
        """Blink the detective to a random free tile right next to the criminal."""
        if self.game_over or self.teleport_charges <= 0:
            return
        candidates = []
        cr, cc = self.criminal_pos
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                if abs(dr) + abs(dc) > 2:
                    continue
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    if self.board_state[nr][nc] != "obstacle" and (nr, nc) != self.criminal_pos:
                        candidates.append((nr, nc))

        if not candidates:
            self._set_status("🧲 Teleport failed — no clear tile nearby!", "#f87171")
            return

        self.teleport_charges -= 1
        self._refresh_power_buttons()
        self.detective_pos = random.choice(candidates)
        self._draw_board()

        if self.detective_pos == self.criminal_pos:
            self._show_result_popup(win=True)
            return

        self._set_status("🧲 Teleported next to the criminal!", COL_ACCENT)
        self.root.update()
        self.root.after(300, self.criminal_turn)

    def use_trap(self):
        """Block the criminal's single best escape tile for its next move."""
        if self.game_over or self.trap_charges <= 0:
            return
        if self.active_trap is not None:
            self._set_status("🚧 A trap is already active!", "#f87171")
            return

        neighbors = [n for n in self.get_neighbors(self.criminal_pos) if n != self.detective_pos]
        if not neighbors:
            self._set_status("🚧 No tile available to trap!", "#f87171")
            return

        best_cell, best_score = None, float("-inf")
        for n in neighbors:
            score = self.heuristic(n, self.detective_pos)
            if score > best_score:
                best_score, best_cell = score, n

        self.trap_charges -= 1
        self._refresh_power_buttons()
        self.active_trap = (best_cell, self.board_state[best_cell[0]][best_cell[1]])
        self.board_state[best_cell[0]][best_cell[1]] = "obstacle"
        self._draw_board()
        self._set_status("🚧 Trap set! The criminal's best route is blocked.", COL_ACCENT)
        self.root.update()
        self.root.after(300, self.criminal_turn)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _draw_board(self):
        self.canvas.delete("all")
        for r in range(SIZE):
            for c in range(SIZE):
                x1, y1 = c * CELL, r * CELL
                x2, y2 = x1 + CELL, y1 + CELL
                base = COL_TILE_LIGHT if (r + c) % 2 == 0 else COL_TILE_DARK
                kind = self.board_state[r][c]

                if kind == "obstacle":
                    rounded_rect(self.canvas, x1 + 3, y1 + 3, x2 - 3, y2 - 3, r=10,
                                 fill=COL_OBSTACLE, outline="")
                    self.canvas.create_text(x1 + CELL / 2, y1 + CELL / 2,
                                             text=OBSTACLE_ICON, font=self.cell_font)
                elif kind == "escape":
                    rounded_rect(self.canvas, x1 + 3, y1 + 3, x2 - 3, y2 - 3, r=10,
                                 fill=COL_ESCAPE, outline=COL_ESCAPE_GLOW, width=2)
                    self.canvas.create_text(x1 + CELL / 2, y1 + CELL / 2,
                                             text=ESCAPE_ICON, font=self.cell_font)
                else:
                    rounded_rect(self.canvas, x1 + 3, y1 + 3, x2 - 3, y2 - 3, r=10,
                                 fill=base, outline="")

        # Detective
        self._draw_token(self.detective_pos, COL_DETECTIVE, COL_DETECTIVE_RING, DETECTIVE_ICON)
        # Criminal
        self._draw_token(self.criminal_pos, COL_CRIMINAL, COL_CRIMINAL_RING, CRIMINAL_ICON)

    def _draw_token(self, pos, color, ring_color, icon):
        r, c = pos
        cx, cy = c * CELL + CELL / 2, r * CELL + CELL / 2
        rad = CELL * 0.38
        self.canvas.create_oval(cx - rad - 3, cy - rad - 3, cx + rad + 3, cy + rad + 3,
                                 outline=ring_color, width=3)
        self.canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                                 fill=color, outline="")
        self.canvas.create_text(cx, cy, text=icon, font=self.cell_font)

    def _set_status(self, text, color=COL_SUBTEXT):
        self.status_label.config(text=text, fg=color)

    # ------------------------------------------------------------------
    # Game logic
    # ------------------------------------------------------------------
    def player_move(self, dr, dc):
        if self.game_over:
            return
        nr, nc = self.detective_pos[0] + dr, self.detective_pos[1] + dc
        if not (0 <= nr < SIZE and 0 <= nc < SIZE):
            return
        if self.board_state[nr][nc] == "obstacle":
            return

        self.detective_pos = (nr, nc)

        if self.detective_pos == self.criminal_pos:
            self._draw_board()
            self._show_result_popup(win=True)
            return

        self._draw_board()
        self._set_status("Criminal is thinking...", COL_ACCENT)
        self.root.update()
        self.root.after(250, self.criminal_turn)

    def criminal_turn(self):
        best_move = self.minimax(
            self.criminal_pos, self.detective_pos, depth=3,
            alpha=float("-inf"), beta=float("inf"), maximizing=True,
        )[1]

        # release a temporary trap now that the AI has planned around it
        if self.active_trap is not None:
            (tr, tc), prev_kind = self.active_trap
            self.board_state[tr][tc] = prev_kind
            self.active_trap = None

        if best_move is None:
            self._show_result_popup(win=True)
            return

        self.criminal_pos = best_move

        if self.criminal_pos in escape_points:
            self._draw_board()
            self._show_result_popup(win=False)
            return

        if self.criminal_pos == self.detective_pos:
            self._draw_board()
            self._show_result_popup(win=True)
            return

        self._draw_board()
        self._set_status("Your move — catch the criminal before it escapes.")

    # ------------------------------------------------------------------
    # Result popup animation
    # ------------------------------------------------------------------
    def _show_result_popup(self, win):
        self.game_over = True
        self._refresh_power_buttons()
        title = "Detective Wins!" if win else "Criminal Wins!"
        icon = "🎉" if win else "💀"
        sub = "You caught the criminal." if win else "The criminal slipped away."
        accent = COL_ESCAPE_GLOW if win else "#f87171"
        self._set_status(title, accent)

        w, h = SIZE * CELL, SIZE * CELL
        backdrop = self.canvas.create_rectangle(0, 0, w, h, fill="black",
                                                 stipple="gray50", outline="")
        self._popup_shapes = [backdrop]
        self._animate_popup(0, title, sub, icon, accent, win)

    def _animate_popup(self, step, title, sub, icon, accent, win, steps=14):
        # clear previously drawn popup shapes/widgets, keep the backdrop
        backdrop = self._popup_shapes[0]
        for item in self._popup_shapes[1:]:
            self.canvas.delete(item)
        for widget in self._popup_widgets:
            widget.destroy()
        self._popup_shapes = [backdrop]
        self._popup_widgets = []

        t = step / steps
        # ease-out-back: slight overshoot for a springy "pop" feel
        c1, c3 = 1.70158, 2.70158
        eased = 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
        eased = max(0.0, eased)

        box_w, box_h = 300, 220
        cur_w, cur_h = max(box_w * eased, 0), max(box_h * eased, 0)
        cx, cy = SIZE * CELL / 2, SIZE * CELL / 2
        x1, y1 = cx - cur_w / 2, cy - cur_h / 2
        x2, y2 = cx + cur_w / 2, cy + cur_h / 2

        if cur_w > 6 and cur_h > 6:
            radius = max(2, min(18, cur_w / 2 - 1, cur_h / 2 - 1))
            box = rounded_rect(self.canvas, x1, y1, x2, y2, r=radius,
                                fill=COL_PANEL, outline=accent, width=3)
            self._popup_shapes.append(box)

            fscale = min(eased, 1.15)
            if cur_h > 60:
                icon_font = tkfont.Font(family="Segoe UI Emoji", size=max(1, int(46 * fscale)))
                title_font = tkfont.Font(family="Segoe UI", size=max(1, int(17 * fscale)), weight="bold")
                icon_item = self.canvas.create_text(cx, cy - cur_h * 0.24, text=icon, font=icon_font)
                title_item = self.canvas.create_text(cx, cy - cur_h * 0.02, text=title,
                                                       font=title_font, fill=COL_TEXT)
                self._popup_shapes += [icon_item, title_item]
            if cur_h > 120:
                sub_font = tkfont.Font(family="Segoe UI", size=max(1, int(11 * fscale)))
                sub_item = self.canvas.create_text(cx, cy + cur_h * 0.16, text=sub,
                                                     font=sub_font, fill=COL_SUBTEXT)
                self._popup_shapes.append(sub_item)

        if step < steps:
            self.root.after(18, lambda: self._animate_popup(step + 1, title, sub, icon, accent, win, steps))
        else:
            play_btn = tk.Button(
                self.canvas, text="Play Again", font=self.btn_font,
                bg=accent, fg="#1b1f2a", activebackground=accent,
                activeforeground="#1b1f2a", relief="flat", bd=0,
                padx=14, pady=6, cursor="hand2", command=self._restart_from_popup,
            )
            btn_window = self.canvas.create_window(cx, cy + box_h * 0.32, window=play_btn)
            self._popup_shapes.append(btn_window)
            self._popup_widgets.append(play_btn)

    def _clear_popup(self):
        for item in self._popup_shapes:
            self.canvas.delete(item)
        for widget in self._popup_widgets:
            widget.destroy()
        self._popup_shapes = []
        self._popup_widgets = []

    def _restart_from_popup(self):
        self._clear_popup()
        self.restart()

    def get_neighbors(self, pos):
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        result = []
        for dr, dc in moves:
            nr, nc = pos[0] + dr, pos[1] + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                if self.board_state[nr][nc] != "obstacle":
                    result.append((nr, nc))
        return result

    def heuristic(self, criminal_pos, detective_pos):
        def manhattan(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        dist_det = manhattan(criminal_pos, detective_pos)
        dist_escape = min(manhattan(criminal_pos, e) for e in escape_points)
        return dist_det * 10 - dist_escape * 8

    def minimax(self, criminal_pos, detective_pos, depth, alpha, beta, maximizing):
        if depth == 0 or criminal_pos == detective_pos:
            return self.heuristic(criminal_pos, detective_pos), None

        if maximizing:  # Criminal tries to maximize its score
            max_eval = float("-inf")
            best_move = None
            for move in self.get_neighbors(criminal_pos):
                if move == detective_pos:
                    continue
                eval_score = self.minimax(move, detective_pos, depth - 1, alpha, beta, False)[0]
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:  # Detective tries to minimize criminal's score
            min_eval = float("inf")
            for move in self.get_neighbors(detective_pos):
                if move == criminal_pos:
                    return float("-inf"), None
                eval_score = self.minimax(criminal_pos, move, depth - 1, alpha, beta, True)[0]
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, None

    # ------------------------------------------------------------------
    # Restart
    # ------------------------------------------------------------------
    def restart(self):
        self._clear_popup()
        self.board_state = [["" for _ in range(SIZE)] for _ in range(SIZE)]
        for (r, c) in obstacles:
            self.board_state[r][c] = "obstacle"
        for (r, c) in escape_points:
            self.board_state[r][c] = "escape"
        self.detective_pos = (0, 0)
        self.criminal_pos = (3, 3)
        self.game_over = False
        self.freeze_charges = 2
        self.teleport_charges = 1
        self.trap_charges = 2
        self.active_trap = None
        self._refresh_power_buttons()
        self._draw_board()
        self._set_status("Your move — catch the criminal before it escapes.")


if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()
