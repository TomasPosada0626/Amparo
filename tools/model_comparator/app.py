"""GUI de escritorio (Tkinter) para comparar modelos de lenguaje candidatos.

Flujo: elegir modelos -> elegir fuente de consultas (manual / dataset privado /
archivo Word-PDF) -> elegir numero de pasadas -> Comparar. Mientras corre se ve
una tabla en vivo, una barra de progreso y un cronometro. Al terminar se
habilitan los botones "Conclusion" (abre el informe resumido) y "Cerrar".
"""

from __future__ import annotations

import queue
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from . import config, report
from .dataset_loader import DatasetItem, DatasetParseError, parse_dataset
from .run_manager import ComparisonRun, RunResult

LARGE_RUN_WARNING_THRESHOLD = 50


def _fmt_mmss(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class ModelComparatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Amparo - Comparador de modelos")
        self.root.geometry("1080x720")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)

        self.model_vars: dict[str, tk.BooleanVar] = {}
        self.source_var = tk.StringVar(value="manual")
        self.selected_file: Optional[Path] = None
        self.passes_var = tk.IntVar(value=1)

        self.run: Optional[ComparisonRun] = None
        self.running = False
        self.start_time = 0.0
        self.completed = 0
        self.total = 0
        self.row_results: dict[str, RunResult] = {}

        self._build_layout()

    # ---------------------------------------------------------------- layout

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        top = ttk.PanedWindow(outer, orient="horizontal")
        top.pack(fill="x", pady=(0, 10))
        model_pane = ttk.Frame(top)
        query_pane = ttk.Frame(top)
        top.add(model_pane, weight=0)
        top.add(query_pane, weight=1)
        self._build_model_frame(model_pane)
        self._build_query_frame(query_pane)

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 10))
        self._build_controls(controls)

        progress = ttk.Frame(outer)
        progress.pack(fill="x", pady=(0, 10))
        self._build_progress(progress)

        table = ttk.Frame(outer)
        table.pack(fill="both", expand=True)
        self._build_table(table)

    def _build_model_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Modelos a comparar", padding=10)
        frame.pack(fill="both", expand=True)

        header = ttk.Frame(frame)
        header.pack(fill="x", pady=(0, 8))
        ttk.Button(header, text="Todos", width=8, command=lambda: self._set_all_models(True)).pack(side="left")
        ttk.Button(header, text="Ninguno", width=8, command=lambda: self._set_all_models(False)).pack(side="left", padx=(4, 0))
        ttk.Button(header, text="Detalles...", command=self._show_model_details).pack(side="left", padx=(4, 0))

        grid = ttk.Frame(frame)
        grid.pack(fill="both", expand=True)
        per_column = 5
        for i, model in enumerate(config.DEFAULT_MODELS):
            var = tk.BooleanVar(value=False)
            self.model_vars[model.id] = var
            row, col = i % per_column, i // per_column
            ttk.Checkbutton(grid, text=model.label, variable=var).grid(
                row=row, column=col, sticky="w", padx=(0, 16), pady=3
            )

    def _set_all_models(self, value: bool) -> None:
        for var in self.model_vars.values():
            var.set(value)

    def _show_model_details(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Detalles de los modelos")
        win.geometry("640x360")

        columns = ("modelo", "comando", "notas")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        tree.heading("modelo", text="Modelo")
        tree.heading("comando", text="Como conseguirlo")
        tree.heading("notas", text="Notas")
        tree.column("modelo", width=170, anchor="w")
        tree.column("comando", width=210, anchor="w")
        tree.column("notas", width=230, anchor="w")
        for model in config.DEFAULT_MODELS:
            comando = f"ollama pull {model.slug}"
            tree.insert("", "end", values=(model.label, comando, model.notes or "-"))
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=(0, 8))

    def _build_query_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Consulta", padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Radiobutton(
            frame, text="Consulta manual", value="manual", variable=self.source_var,
            command=self._on_source_change,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            frame, text="Dataset completo (buscar archivo .docx / .pdf / .md)", value="archivo",
            variable=self.source_var, command=self._on_source_change,
        ).grid(row=1, column=0, sticky="w")

        self.manual_text = tk.Text(frame, height=5, width=60, wrap="word")
        self.manual_text.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        file_row = ttk.Frame(frame)
        file_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.browse_button = ttk.Button(file_row, text="Buscar archivo...", command=self._browse_file, state="disabled")
        self.browse_button.pack(side="left")
        self.file_label = ttk.Label(file_row, text="Ningun archivo seleccionado")
        self.file_label.pack(side="left", padx=8)

        passes_row = ttk.Frame(frame)
        passes_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Label(passes_row, text="Pasadas por consulta:").pack(side="left")
        ttk.Spinbox(passes_row, from_=1, to=20, width=5, textvariable=self.passes_var).pack(side="left", padx=6)

    def _on_source_change(self) -> None:
        source = self.source_var.get()
        self.manual_text.configure(state="normal" if source == "manual" else "disabled")
        self.browse_button.configure(state="normal" if source == "archivo" else "disabled")

    def _browse_file(self) -> None:
        initial_dir = config.PRIVATE_DATASET_PATH.parent if config.PRIVATE_DATASET_PATH.parent.exists() else config.PROJECT_ROOT
        path = filedialog.askopenfilename(
            title="Selecciona el dataset completo",
            initialdir=str(initial_dir),
            filetypes=[("Documentos", "*.docx *.pdf *.md *.txt"), ("Todos los archivos", "*.*")],
        )
        if path:
            self.selected_file = Path(path)
            self.file_label.configure(text=self.selected_file.name)

    def _build_controls(self, parent: ttk.Frame) -> None:
        left = ttk.Frame(parent)
        left.pack(side="left")
        self.compare_button = ttk.Button(left, text="Comparar", command=self._start_comparison)
        self.compare_button.pack(side="left")
        self.cancel_button = ttk.Button(left, text="Cancelar", command=self._cancel_comparison, state="disabled")
        self.cancel_button.pack(side="left", padx=(8, 0))
        self.conclusion_button = ttk.Button(left, text="Conclusion", command=self._open_conclusion, state="disabled")
        self.conclusion_button.pack(side="left", padx=(8, 0))

        self.close_button = ttk.Button(parent, text="Cerrar", command=self._close_app)
        self.close_button.pack(side="right")

    def _build_progress(self, parent: ttk.Frame) -> None:
        status_row = ttk.Frame(parent)
        status_row.pack(fill="x", pady=(0, 4))
        self.status_label = ttk.Label(status_row, text="Listo.", font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left")
        self.timer_label = ttk.Label(status_row, text="Transcurrido 00:00 | Restante --:--")
        self.timer_label.pack(side="right")

        bar_row = ttk.Frame(parent)
        bar_row.pack(fill="x")
        self.progress_bar = ttk.Progressbar(bar_row, mode="determinate")
        self.progress_bar.pack(fill="x", side="left", expand=True)
        self.progress_label = ttk.Label(bar_row, text="0 / 0", width=10, anchor="e")
        self.progress_label.pack(side="left", padx=(8, 0))

    def _build_table(self, parent: ttk.Frame) -> None:
        hint = ttk.Label(parent, text="Doble clic en una fila para ver la respuesta completa.", foreground="#666666")
        hint.pack(anchor="w", pady=(0, 4))

        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)

        columns = ("modelo", "pregunta", "pasada", "tiempo", "tok_in", "tok_out", "tok_s", "similitud", "costo", "estado")
        headings = {
            "modelo": "Modelo", "pregunta": "Consulta #", "pasada": "Pasada", "tiempo": "Tiempo (s)",
            "tok_in": "Tok. entrada", "tok_out": "Tok. salida", "tok_s": "Tok/s",
            "similitud": "Similitud %", "costo": "Costo (USD)", "estado": "Estado",
        }
        widths = {
            "modelo": 170, "pregunta": 80, "pasada": 60, "tiempo": 80, "tok_in": 90,
            "tok_out": 90, "tok_s": 70, "similitud": 90, "costo": 90, "estado": 160,
        }

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center" if col != "modelo" and col != "estado" else "w")
        self.tree.tag_configure("error", foreground="#b00020")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        self.tree.bind("<Double-1>", self._show_row_detail)

    # ------------------------------------------------------------- utilities

    def _selected_models(self) -> list:
        return [m for m in config.DEFAULT_MODELS if self.model_vars[m.id].get()]

    def _resolve_items(self) -> tuple[Optional[list[DatasetItem]], str]:
        """Devuelve (items, descripcion_de_la_fuente) o (None, mensaje_de_error)."""
        source = self.source_var.get()
        if source == "manual":
            text = self.manual_text.get("1.0", "end").strip()
            if not text:
                return None, "Escribe una consulta manual antes de comparar."
            return [DatasetItem(query=text, expected=None)], "consulta manual"

        if source == "archivo":
            if self.selected_file is None:
                return None, "Selecciona un archivo con el dataset completo."
            try:
                items = parse_dataset(self.selected_file)
            except DatasetParseError as exc:
                return None, str(exc)
            return items, f"archivo {self.selected_file.name} ({len(items)} ejemplos)"

        return None, "Fuente de consulta desconocida."

    # ------------------------------------------------------------ start/stop

    def _start_comparison(self) -> None:
        models = self._selected_models()
        if not models:
            messagebox.showwarning("Sin modelos", "Selecciona al menos un modelo para comparar.")
            return

        items, info = self._resolve_items()
        if items is None:
            messagebox.showwarning("Consulta invalida", info)
            return

        passes = max(1, int(self.passes_var.get()))
        total_calls = len(models) * len(items) * passes
        if total_calls > LARGE_RUN_WARNING_THRESHOLD:
            proceed = messagebox.askyesno(
                "Confirmar corrida grande",
                f"Esto va a hacer {total_calls} llamadas. Si no tienes GPU, esto puede "
                "tardar bastante. Continuar?",
            )
            if not proceed:
                return

        self.source_desc = info
        self.n_queries = len(items)
        self.passes = passes

        self.tree.delete(*self.tree.get_children())
        self.row_results.clear()

        self.run = ComparisonRun(models, items, passes)
        self.running = True
        self.start_time = time.monotonic()
        self.completed = 0
        self.total = total_calls

        self.compare_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.conclusion_button.configure(state="disabled")
        self.close_button.configure(state="disabled")
        self.status_label.configure(text="Comparando...")

        self.run.start()
        self.root.after(150, self._tick)

    def _cancel_comparison(self) -> None:
        if self.run is not None:
            self.run.cancel()
            self.status_label.configure(text="Cancelando...")

    def _tick(self) -> None:
        if self.run is None:
            return
        try:
            while True:
                event = self.run.events.get_nowait()
                if event.kind == "result" and event.result is not None:
                    self._add_result_row(event.result)
                    self.completed = event.completed
                    self.total = event.total
                elif event.kind == "done":
                    self._on_run_done()
                    return
        except queue.Empty:
            pass

        self._update_progress_and_timer()
        self.root.after(150, self._tick)

    def _update_progress_and_timer(self) -> None:
        self.progress_bar.configure(maximum=max(1, self.total), value=self.completed)
        self.progress_label.configure(text=f"{self.completed} / {self.total}")
        elapsed = time.monotonic() - self.start_time
        if self.completed > 0 and self.total > 0:
            remaining = (elapsed / self.completed) * max(0, self.total - self.completed)
            remaining_txt = _fmt_mmss(remaining)
        else:
            remaining_txt = "--:--"
        self.timer_label.configure(text=f"Transcurrido {_fmt_mmss(elapsed)} | Restante {remaining_txt}")

    def _on_run_done(self) -> None:
        self.running = False
        self._update_progress_and_timer()
        cancelled = self.run.cancelled if self.run else False
        n_results = len(self.run.results) if self.run else 0

        self.compare_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.close_button.configure(state="normal")
        self.conclusion_button.configure(state="normal" if n_results > 0 else "disabled")
        self.status_label.configure(text="Cancelado (parcial)." if cancelled else "Completado.")

    # ------------------------------------------------------------------ table

    def _add_result_row(self, result: RunResult) -> None:
        estado = f"Error: {result.error}" if result.error else "OK"
        values = (
            result.model_label,
            result.query_index + 1,
            result.pass_index + 1,
            f"{result.latency_s:.2f}",
            result.prompt_tokens,
            result.completion_tokens,
            f"{result.tokens_per_s:.1f}",
            f"{result.similarity:.1f}" if result.similarity is not None else "-",
            f"{result.cost_usd:.5f}" if result.cost_usd is not None else "-",
            estado,
        )
        tags = ("error",) if result.error else ()
        item_id = self.tree.insert("", "end", values=values, tags=tags)
        self.row_results[item_id] = result
        self.tree.see(item_id)

    def _show_row_detail(self, _event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        result = self.row_results.get(selection[0])
        if result is None:
            return

        win = tk.Toplevel(self.root)
        win.title(f"Detalle - {result.model_label}")
        win.geometry("640x480")

        def add_block(label: str, text: str) -> None:
            ttk.Label(win, text=label, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=8, pady=(8, 0))
            box = scrolledtext.ScrolledText(win, height=6, wrap="word")
            box.pack(fill="both", expand=True, padx=8, pady=(0, 4))
            box.insert("1.0", text or "(vacio)")
            box.configure(state="disabled")

        add_block("Consulta:", result.query)
        add_block("Respuesta esperada:", result.expected or "")
        add_block("Respuesta del modelo:", result.response or (result.error or ""))
        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=8)

    # ------------------------------------------------------------- conclusion

    def _open_conclusion(self) -> None:
        if self.run is None or not self.run.results:
            return
        summaries = report.summarize(self.run.results)
        narrative = report.build_narrative(summaries, self.source_desc, self.passes, self.n_queries)
        ConclusionWindow(self.root, self.run, summaries, narrative, self.source_desc, self.passes, self.n_queries, self._close_app)

    # ------------------------------------------------------------------ close

    def _on_close_request(self) -> None:
        if self.running:
            if messagebox.askyesno("Comparacion en curso", "Hay una comparacion en curso. Cancelar y cerrar?"):
                if self.run is not None:
                    self.run.cancel()
                self.root.after(300, self.root.destroy)
            return
        self.root.destroy()

    def _close_app(self) -> None:
        self.root.destroy()


class ConclusionWindow(tk.Toplevel):
    def __init__(self, parent, run: ComparisonRun, summaries, narrative: str, source_desc: str, passes: int, n_queries: int, close_app_callback) -> None:
        super().__init__(parent)
        self.run = run
        self.summaries = summaries
        self.narrative = narrative
        self.source_desc = source_desc
        self.passes = passes
        self.n_queries = n_queries
        self._close_app_callback = close_app_callback

        self.title("Conclusion - Informe de comparacion")
        self.geometry("900x650")

        meta = ttk.Label(
            self,
            text=f"Fuente: {source_desc}  |  Consultas: {n_queries}  |  Pasadas: {passes}  |  "
                 f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            padding=8,
        )
        meta.pack(anchor="w")

        columns = ("modelo", "llamadas", "errores", "similitud", "desviacion", "tok_s", "costo")
        headings = {
            "modelo": "Modelo", "llamadas": "Llamadas", "errores": "Errores",
            "similitud": "Similitud prom. %", "desviacion": "Desv. similitud",
            "tok_s": "Tok/s prom.", "costo": "Costo total (USD)",
        }
        tree = ttk.Treeview(self, columns=columns, show="headings", height=min(10, max(3, len(summaries))))
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=140, anchor="center" if col != "modelo" else "w")
        for s in summaries:
            tree.insert(
                "", "end",
                values=(
                    s.model_label,
                    s.n_calls,
                    s.n_errors,
                    f"{s.avg_similarity:.1f}" if s.avg_similarity is not None else "N/A",
                    f"{s.stdev_similarity:.1f}" if s.stdev_similarity is not None else "N/A",
                    f"{s.avg_tokens_per_s:.1f}",
                    f"{s.total_cost_usd:.4f}" if s.total_cost_usd is not None else "N/A",
                ),
            )
        tree.pack(fill="x", padx=8, pady=4)

        ttk.Label(self, text="Conclusion:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(8, 0))
        text_box = scrolledtext.ScrolledText(self, height=10, wrap="word")
        text_box.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        text_box.insert("1.0", narrative)
        text_box.configure(state="disabled")

        btns = ttk.Frame(self, padding=8)
        btns.pack(fill="x")
        ttk.Button(btns, text="Exportar informe (.md)", command=self._export_md).pack(side="left")
        ttk.Button(btns, text="Exportar detalle (.csv)", command=self._export_csv).pack(side="left", padx=6)
        ttk.Button(btns, text="Volver", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Cerrar", command=self._close_all).pack(side="right", padx=6)

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _export_md(self) -> None:
        config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        path = config.ARTIFACTS_DIR / f"comparacion_modelos_{self._timestamp()}.md"
        report.export_markdown(path, self.summaries, self.narrative, self.source_desc, self.passes, self.n_queries)
        messagebox.showinfo("Exportado", f"Informe guardado en:\n{path}")

    def _export_csv(self) -> None:
        config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        path = config.ARTIFACTS_DIR / f"comparacion_modelos_{self._timestamp()}_detalle.csv"
        self.run.export_csv(path)
        messagebox.showinfo("Exportado", f"Detalle guardado en:\n{path}")

    def _close_all(self) -> None:
        self.destroy()
        self._close_app_callback()


def main() -> None:
    root = tk.Tk()
    ModelComparatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
