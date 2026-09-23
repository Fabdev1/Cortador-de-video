"""
Cortador de Vídeos – By GA Suporte Tech
Interface fiel à referência original · CustomTkinter + MoviePy v2
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

# ── Configura o ffmpeg bundled ANTES de qualquer import do moviepy ────────────
import imageio_ffmpeg as _iio_ffmpeg
from imageio.plugins.ffmpeg import get_exe as _get_ffmpeg_exe
os.environ["FFMPEG_BINARY"] = _get_ffmpeg_exe()

import customtkinter as ctk
import proglog
from moviepy import VideoFileClip

# ── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Paleta de cores ───────────────────────────────────────────────────────────
BG_COLOR     = "#1e1e1e"
FRAME_BG     = "#2d2d2d"
BUTTON_BG    = "#3c3c3c"
BUTTON_HOVER = "#505050"
BLUE_BTN     = "#1a7fe8"
BLUE_HOVER   = "#1565c0"
TEXT_COLOR   = "#e8e8e8"
MUTED_COLOR  = "#909090"
BORDER_COLOR = "#484848"
PROGRESS_FG  = "#1a7fe8"


class CortadorApp(ctk.CTk):
    """Janela principal do Cortador de Vídeos."""

    def __init__(self):
        super().__init__()

        self.title("Cortador de Vídeos – By FabDev")
        self.geometry("480x520")
        self.minsize(480, 520)
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self._video_path: str = ""
        self._output_dir: str = ""
        self._running: bool = False

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # Construção da UI
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Container principal com padding
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=18, pady=10)

        # ── Selecionar Vídeo ──────────────────────────────────────────────
        self._btn_select = ctk.CTkButton(
            main,
            text="Selecionar Vídeo",
            height=38,
            corner_radius=5,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=13),
            command=self._selecionar_video,
        )
        self._btn_select.pack(fill="x", pady=(0, 4))

        # Label arquivo selecionado
        self._lbl_arquivo = ctk.CTkLabel(
            main,
            text="Arquivo: Nenhum vídeo selecionado",
            anchor="w",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=12),
        )
        self._lbl_arquivo.pack(fill="x", pady=(0, 6))

        # ── Duração de cada trecho ────────────────────────────────────────
        ctk.CTkLabel(
            main,
            text="Duração de cada trecho (segundos):",
            anchor="w",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", pady=(0, 3))

        self._duracao_var = tk.IntVar(value=12)
        self._build_spinbox(main)

        # ── Salvar em ─────────────────────────────────────────────────────
        self._btn_salvar_em = ctk.CTkButton(
            main,
            text="Salvar em",
            height=38,
            corner_radius=5,
            fg_color=BUTTON_BG,
            hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=13),
            command=self._selecionar_pasta,
        )
        self._btn_salvar_em.pack(fill="x", pady=(8, 4))

        # Label pasta selecionada
        self._lbl_pasta = ctk.CTkLabel(
            main,
            text="Nenhuma pasta selecionada",
            anchor="w",
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=12),
        )
        self._lbl_pasta.pack(fill="x", pady=(0, 8))

        # Separador
        ctk.CTkFrame(main, height=1, fg_color=BORDER_COLOR).pack(fill="x", pady=(0, 8))

        # ── CORTAR AGORA ──────────────────────────────────────────────────
        self._btn_cortar = ctk.CTkButton(
            main,
            text="CORTAR AGORA",
            height=46,
            corner_radius=5,
            fg_color=BLUE_BTN,
            hover_color=BLUE_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._iniciar_corte,
        )
        self._btn_cortar.pack(fill="x", pady=(0, 8))

        # ── Barra de progresso + % ────────────────────────────────────────
        prog_row = ctk.CTkFrame(main, fg_color="transparent")
        prog_row.pack(fill="x")

        self._progressbar = ctk.CTkProgressBar(
            prog_row,
            height=14,
            corner_radius=3,
            fg_color=FRAME_BG,
            progress_color=PROGRESS_FG,
        )
        self._progressbar.set(0)
        self._progressbar.pack(side="left", fill="x", expand=True, pady=(0, 2))

        self._lbl_pct = ctk.CTkLabel(
            prog_row,
            text=" 0%",
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=12),
            width=42,
            anchor="e",
        )
        self._lbl_pct.pack(side="left")

        # Label de status (ex: "Cortando parte 2 de 5...")
        self._lbl_status = ctk.CTkLabel(
            main,
            text="",
            anchor="w",
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=11),
        )
        self._lbl_status.pack(fill="x", pady=(2, 0))

    # ─────────────────────────────────────────────────────────────────────────
    # Spinbox customizado
    # ─────────────────────────────────────────────────────────────────────────

    def _build_spinbox(self, parent):
        """Entry numérico com botões ▲▼ laterais."""
        frame = ctk.CTkFrame(
            parent,
            fg_color=FRAME_BG,
            corner_radius=5,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        frame.pack(fill="x")

        vcmd = (self.register(self._validar_int), "%P")
        self._entry_duracao = ctk.CTkEntry(
            frame,
            textvariable=self._duracao_var,
            validate="key",
            validatecommand=vcmd,
            height=34,
            corner_radius=0,
            border_width=0,
            fg_color=FRAME_BG,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=13),
        )
        self._entry_duracao.pack(side="left", fill="both", expand=True, padx=(6, 0))

        col = ctk.CTkFrame(frame, fg_color="transparent", width=30)
        col.pack(side="right", fill="y")
        col.pack_propagate(False)

        btn_cfg = dict(
            width=30, height=17, corner_radius=0,
            fg_color=BUTTON_BG, hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR, font=ctk.CTkFont(size=9),
            border_width=0,
        )
        ctk.CTkButton(col, text="▲", command=self._inc, **btn_cfg).pack(fill="x")
        ctk.CTkButton(col, text="▼", command=self._dec, **btn_cfg).pack(fill="x")

    # ─────────────────────────────────────────────────────────────────────────
    # Handlers spinbox
    # ─────────────────────────────────────────────────────────────────────────

    def _validar_int(self, valor: str) -> bool:
        return valor.isdigit() or valor == ""

    def _inc(self):
        self._duracao_var.set(max(1, self._duracao_var.get() + 1))

    def _dec(self):
        self._duracao_var.set(max(1, self._duracao_var.get() - 1))

    # ─────────────────────────────────────────────────────────────────────────
    # Seleção de arquivos / pasta
    # ─────────────────────────────────────────────────────────────────────────

    def _selecionar_video(self):
        path = filedialog.askopenfilename(
            title="Selecionar Vídeo",
            filetypes=[
                ("Vídeos", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if path:
            self._video_path = path
            nome = os.path.basename(path)
            self._lbl_arquivo.configure(text=f"Arquivo: {nome}")

    def _selecionar_pasta(self):
        path = filedialog.askdirectory(title="Selecionar pasta de saída")
        if path:
            self._output_dir = path
            exibir = path if len(path) <= 52 else "…" + path[-49:]
            self._lbl_pasta.configure(text=exibir, text_color=TEXT_COLOR)

    # ─────────────────────────────────────────────────────────────────────────
    # Lógica de corte
    # ─────────────────────────────────────────────────────────────────────────

    def _iniciar_corte(self):
        if self._running:
            return

        if not self._video_path:
            messagebox.showwarning("Aviso", "Selecione um vídeo antes de cortar.")
            return
        if not self._output_dir:
            messagebox.showwarning("Aviso", "Selecione a pasta de saída antes de cortar.")
            return

        duracao = self._duracao_var.get()
        if duracao <= 0:
            messagebox.showwarning("Aviso", "A duração deve ser maior que zero.")
            return

        self._atualizar_progresso(0, "Iniciando corte…")
        self._set_ui_estado(False)
        threading.Thread(target=self._executar_corte, args=(duracao,), daemon=True).start()

    def _executar_corte(self, segundos_por_trecho: int):
        try:
            import subprocess
            from imageio.plugins.ffmpeg import get_exe as _ffmpeg_exe
            ffmpeg = _ffmpeg_exe()

            # Usa MoviePy só para ler a duração — sem write, sem problema
            video = VideoFileClip(self._video_path)
            duracao_total = video.duration
            video.close()

            total_partes = int(duracao_total // segundos_por_trecho) + (
                1 if duracao_total % segundos_por_trecho > 0 else 0
            )

            for i in range(total_partes):
                inicio = i * segundos_por_trecho
                fim = min((i + 1) * segundos_por_trecho, duracao_total)

                status = f"Cortando parte {i + 1} de {total_partes}…"
                self.after(0, self._atualizar_progresso, i / total_partes, status)

                nome_saida = os.path.join(self._output_dir, f"parte_{i + 1:03d}.mp4")

                # Corta via ffmpeg direto — stream copy, sem re-codificar (rápido!)
                cmd = [
                    ffmpeg,
                    "-y",                       # sobrescreve se existir
                    "-i", self._video_path,     # arquivo de entrada
                    "-ss", str(inicio),         # início do trecho
                    "-to", str(fim),            # fim do trecho
                    "-c", "copy",               # cópia direta, sem re-encoding
                    nome_saida,
                ]
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=0x08000000,   # sem janela extra no Windows
                )
                if result.returncode != 0:
                    erro_ffmpeg = result.stderr.decode("utf-8", errors="replace")[-800:]
                    raise RuntimeError(f"FFmpeg retornou erro:\n{erro_ffmpeg}")

                progresso = (i + 1) / total_partes
                self.after(0, self._atualizar_progresso, progresso, status)

            self.after(0, self._corte_finalizado, total_partes)

        except Exception as exc:
            import traceback
            self.after(0, self._corte_erro, traceback.format_exc())

    def _atualizar_progresso(self, valor: float, status: str = ""):
        self._progressbar.set(valor)
        self._lbl_pct.configure(text=f" {int(valor * 100)}%")
        if status:
            self._lbl_status.configure(text=status)

    def _corte_finalizado(self, total: int):
        self._set_ui_estado(True)
        self._atualizar_progresso(1.0, f"✔ {total} parte(s) salva(s) com sucesso!")
        self._lbl_pct.configure(text=" 100%")
        messagebox.showinfo(
            "Concluído",
            f"Corte finalizado!\n{total} parte(s) salva(s) em:\n{self._output_dir}",
        )

    def _corte_erro(self, mensagem: str):
        self._set_ui_estado(True)
        self._lbl_status.configure(text="✖ Erro ao cortar o vídeo.")
        messagebox.showerror("Erro", f"Ocorreu um erro:\n\n{mensagem}")

    def _set_ui_estado(self, ativo: bool):
        self._running = not ativo
        estado = "normal" if ativo else "disabled"
        self._btn_select.configure(state=estado)
        self._btn_salvar_em.configure(state=estado)
        self._btn_cortar.configure(state=estado)
        self._entry_duracao.configure(state=estado)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CortadorApp()
    app.mainloop()
