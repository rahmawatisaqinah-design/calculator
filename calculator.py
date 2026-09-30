import ast
import operator
import re
import tkinter as tk

# ------------------------------------------------------------------
# Warna tema (gelap)
# ------------------------------------------------------------------
WARNA_BG = "#F3B5BA"          # latar jendela
WARNA_LAYAR = "#E1688B"       # latar layar
WARNA_TEKS = "#FFFFFF"
WARNA_RIWAYAT = "#893941"

WARNA_ANGKA = "#912B48"
WARNA_ANGKA_HOVER = "#610027"
WARNA_OPERATOR = "#5F6B2E"
WARNA_OPERATOR_HOVER = "#7A8A3B"
WARNA_FUNGSI = "#670626"
WARNA_FUNGSI_HOVER = "#B01050"
WARNA_SAMA = "#2F7F7A"
WARNA_SAMA_HOVER = "#3FA39C"
WARNA_HAPUS = "#5D0703"
WARNA_HAPUS_HOVER = "#4F2B1F"

# ------------------------------------------------------------------
# Evaluator matematika yang aman
# ------------------------------------------------------------------
OPERATOR_AMAN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def hitung_aman(ekspresi: str):
    """Menghitung ekspresi matematika sederhana secara aman."""

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATOR_AMAN:
            return OPERATOR_AMAN[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATOR_AMAN:
            return OPERATOR_AMAN[type(node.op)](_eval(node.operand))
        raise ValueError("Ekspresi tidak valid")

    return _eval(ast.parse(ekspresi, mode="eval"))


def format_hasil(angka) -> str:
    """Merapikan tampilan hasil (hilangkan .0 dan desimal berlebih)."""
    if isinstance(angka, float):
        if angka.is_integer() and abs(angka) < 1e15:
            return str(int(angka))
        if abs(angka) < 1e15:
            return f"{angka:.10f}".rstrip("0").rstrip(".")
        return f"{angka:.10g}"
    return str(angka)


def format_tampilan(teks: str) -> str:
    """
    Mengubah angka di dalam teks ke format Indonesia:
    titik (.) sebagai pemisah ribuan dan koma (,) sebagai desimal.
    Contoh: 1234567.89 -> 1.234.567,89
    """

    def _ubah(cocok):
        angka = cocok.group(0)
        bagian_bulat, titik, bagian_desimal = angka.partition(".")
        bagian_bulat = f"{int(bagian_bulat):,}".replace(",", ".") if bagian_bulat else "0"
        return bagian_bulat + ("," + bagian_desimal if titik else "")

    return re.sub(r"\d+\.?\d*|\.\d+", _ubah, teks)


# ------------------------------------------------------------------
# Kelas utama aplikasi
# ------------------------------------------------------------------
class Kalkulator:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.ekspresi = ""
        self.sudah_hasil = False   # True jika layar sedang menampilkan hasil "="

        self._atur_jendela()
        self._buat_ikon()
        self._buat_layar()
        self._buat_tombol()
        self._atur_keyboard()
        self.root.after(100, self._sesuaikan_tampilan)

    # ---------------- Jendela ----------------
    def _atur_jendela(self):
        self.root.title("Kalkulator Python")
        # Ukuran awal nyaman, tetapi sekarang jendela bisa diperbesar/maximize.
        self.root.geometry("420x680")
        self.root.minsize(340, 540)
        self.root.resizable(True, True)
        self.root.configure(bg=WARNA_BG)

        # Saat ukuran jendela berubah, tampilan kalkulator ikut menyesuaikan.
        self.root.bind("<Configure>", self._sesuaikan_tampilan)

    # ---------------- Ikon ----------------
    def _buat_ikon(self):
        """Menggambar ikon kalkulator 64x64 langsung dari kode."""
        ikon = tk.PhotoImage(width=64, height=64)

        def kotak(warna, x1, y1, x2, y2):
            ikon.put(warna, to=(x1, y1, x2, y2))

        kotak(WARNA_BG, 0, 0, 64, 64)                # latar
        kotak("#2e303a", 8, 4, 56, 60)               # badan kalkulator
        kotak("#2ec4b6", 13, 9, 51, 21)              # layar
        # 3 baris x 4 kolom tombol
        warna_baris = ["#ff9f1c", "#565a6e", "#565a6e"]
        for baris in range(3):
            for kolom in range(4):
                x = 13 + kolom * 10
                y = 26 + baris * 11
                warna = "#ff9f1c" if kolom == 3 else warna_baris[baris]
                kotak(warna, x, y, x + 8, y + 8)
        self.root.iconphoto(True, ikon)
        self._ikon = ikon   # simpan referensi agar tidak dihapus garbage collector

    # ---------------- Layar ----------------
    def _buat_layar(self):
        frame = tk.Frame(self.root, bg=WARNA_LAYAR, padx=10, pady=10)
        frame.pack(fill="x", padx=15, pady=(20, 10))
        self.frame_layar = frame

        self.label_riwayat = tk.Label(
            frame, text="", anchor="e", bg=WARNA_LAYAR,
            fg=WARNA_RIWAYAT, font=("Segoe UI", 12),
        )
        self.label_riwayat.pack(fill="x")

        self.label_layar = tk.Label(
            frame, text="0", anchor="e", bg=WARNA_LAYAR,
            fg=WARNA_TEKS, font=("Segoe UI", 34, "bold"),
        )
        self.label_layar.pack(fill="x")

    # ---------------- Tombol ----------------
    def _buat_tombol(self):
        frame = tk.Frame(self.root, bg=WARNA_BG)
        frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.frame_tombol = frame

        # (teks, warna normal, warna hover)
        F = (WARNA_FUNGSI, WARNA_FUNGSI_HOVER)
        H = (WARNA_HAPUS, WARNA_HAPUS_HOVER)
        O = (WARNA_OPERATOR, WARNA_OPERATOR_HOVER)
        A = (WARNA_ANGKA, WARNA_ANGKA_HOVER)
        S = (WARNA_SAMA, WARNA_SAMA_HOVER)

        susunan = [
            [("C", *H), ("⌫", *F), ("%", *F), ("÷", *O)],
            [("7", *A), ("8", *A), ("9", *A), ("×", *O)],
            [("4", *A), ("5", *A), ("6", *A), ("-", *O)],
            [("1", *A), ("2", *A), ("3", *A), ("+", *O)],
            [("±", *F), ("0", *A), (",", *A), ("=", *S)],
        ]

        for r, baris in enumerate(susunan):
            frame.rowconfigure(r, weight=1)
            for c, (teks, warna, hover) in enumerate(baris):
                frame.columnconfigure(c, weight=1)
                tombol = tk.Button(
                    frame, text=teks, bg=warna, fg=WARNA_TEKS,
                    activebackground=hover, activeforeground=WARNA_TEKS,
                    font=("Segoe UI", 16, "bold"), bd=0, relief="flat",
                    cursor="hand2", command=lambda t=teks: self.tekan(t),
                )
                tombol._warna_normal = warna
                tombol._warna_hover = hover
                tombol._teks_asli = teks
                tombol.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
                # efek hover
                tombol.bind("<Enter>", lambda e, b=tombol, h=hover: b.config(bg=h))
                tombol.bind("<Leave>", lambda e, b=tombol, w=warna: b.config(bg=w))

    # ---------------- Tampilan Responsif ----------------
    def _sesuaikan_tampilan(self, event=None):
        """Menyesuaikan ukuran font dan jarak saat jendela diperbesar/diperkecil."""
        # Abaikan event dari widget lain dan hanya proses ukuran jendela utama.
        if event is not None and event.widget is not self.root:
            return

        lebar = max(self.root.winfo_width(), 340)
        tinggi = max(self.root.winfo_height(), 540)

        # Font tombol mengikuti ukuran layar, tetapi tetap dibatasi agar nyaman.
        font_tombol = max(16, min(34, int(min(lebar / 24, tinggi / 28))))
        font_riwayat = max(12, min(22, int(lebar / 32)))
        font_layar = max(34, min(72, int(lebar / 10)))

        # Padding tombol juga membesar pada layar besar.
        padding = max(3, min(10, int(min(lebar, tinggi) / 80)))

        if hasattr(self, "label_riwayat"):
            self.label_riwayat.config(
                font=("Segoe UI", font_riwayat)
            )

        if hasattr(self, "label_layar"):
            teks = self.label_layar.cget("text")
            if teks in ("Error", "Tidak bisa dibagi 0"):
                font_layar = max(18, min(30, int(lebar / 18)))
            self.label_layar.config(
                font=("Segoe UI", font_layar, "bold")
            )

        if hasattr(self, "frame_tombol"):
            for widget in self.frame_tombol.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.config(
                        font=("Segoe UI", font_tombol, "bold")
                    )
                    info = widget.grid_info()
                    widget.grid_configure(
                        padx=padding,
                        pady=padding
                    )

        if hasattr(self, "frame_layar"):
            # Jarak layar ikut menyesuaikan, tetapi tetap tidak terlalu besar.
            jarak_x = max(15, min(35, int(lebar / 25)))
            jarak_atas = max(15, min(30, int(tinggi / 30)))
            self.frame_layar.pack_configure(
                padx=jarak_x,
                pady=(jarak_atas, 10)
            )

    # ---------------- Keyboard ----------------
    def _atur_keyboard(self):
        self.root.bind("<Key>", self._tombol_keyboard)
        self.root.bind("<Return>", lambda e: self.tekan("="))
        self.root.bind("<KP_Enter>", lambda e: self.tekan("="))
        self.root.bind("<BackSpace>", lambda e: self.tekan("⌫"))
        self.root.bind("<Escape>", lambda e: self.tekan("C"))

    def _tombol_keyboard(self, event):
        peta = {"*": "×", "/": "÷", ",": "."}
        ch = peta.get(event.char, event.char)
        if ch in "0123456789.+-×÷%" and ch != "":
            self.tekan(ch)

    # ---------------- Logika ----------------
    def tekan(self, tombol: str):
        operator_simbol = "+-×÷"
        if tombol == ",":
            tombol = "."   # secara internal desimal memakai titik

        if tombol == "C":
            self.ekspresi = ""
            self.label_riwayat.config(text="")
            self.sudah_hasil = False

        elif tombol == "⌫":
            if self.sudah_hasil:
                self.ekspresi = ""
                self.sudah_hasil = False
            else:
                self.ekspresi = self.ekspresi[:-1]

        elif tombol == "=":
            self._hitung()
            return

        elif tombol == "±":
            if self.ekspresi.startswith("-(") and self.ekspresi.endswith(")"):
                self.ekspresi = self.ekspresi[2:-1]
            elif self.ekspresi:
                self.ekspresi = f"-({self.ekspresi})"

        elif tombol in operator_simbol:
            if not self.ekspresi:
                if tombol == "-":          # boleh mulai dengan angka negatif
                    self.ekspresi = "-"
            elif self.ekspresi[-1] in operator_simbol:
                self.ekspresi = self.ekspresi[:-1] + tombol   # ganti operator
            else:
                self.ekspresi += tombol
            self.sudah_hasil = False

        else:  # angka, titik, persen
            if self.sudah_hasil and tombol != "%":
                self.ekspresi = ""          # mulai perhitungan baru
            self.sudah_hasil = False
            if tombol == "." and self._sudah_ada_titik():
                pass
            else:
                self.ekspresi += tombol

        self._perbarui_layar()

    def _sudah_ada_titik(self) -> bool:
        """Cek apakah angka terakhir sudah memiliki titik desimal."""
        angka_terakhir = self.ekspresi
        for op in "+-×÷()%":
            angka_terakhir = angka_terakhir.replace(op, " ")
        return "." in angka_terakhir.split(" ")[-1]

    def _hitung(self):
        if not self.ekspresi:
            return
        teks = self.ekspresi.replace("×", "*").replace("÷", "/").replace("%", "/100")
        try:
            hasil = format_hasil(hitung_aman(teks))
            self.label_riwayat.config(text=f"{format_tampilan(self.ekspresi)} =")
            self.ekspresi = hasil
            self.sudah_hasil = True
            self._perbarui_layar()
        except ZeroDivisionError:
            self._tampilkan_error("Tidak bisa dibagi 0")
        except Exception:
            self._tampilkan_error("Error")

    def _tampilkan_error(self, pesan: str):
        self.ekspresi = ""
        self.sudah_hasil = False
        self.label_riwayat.config(text="")
        lebar = max(self.root.winfo_width(), 340)
        ukuran_error = max(18, min(30, int(lebar / 18)))
        self.label_layar.config(
            text=pesan,
            font=("Segoe UI", ukuran_error, "bold")
        )

    def _perbarui_layar(self):
        teks = format_tampilan(self.ekspresi) if self.ekspresi else "0"

        # Font dasar mengikuti ukuran jendela.
        lebar = max(self.root.winfo_width(), 340)
        ukuran_besar = max(34, min(72, int(lebar / 10)))

        # Kalau angka terlalu panjang, font diperkecil agar tidak terpotong.
        if len(teks) <= 9:
            ukuran = ukuran_besar
        elif len(teks) <= 14:
            ukuran = max(24, int(ukuran_besar * 0.72))
        else:
            ukuran = max(16, int(ukuran_besar * 0.50))

        self.label_layar.config(
            text=teks,
            font=("Segoe UI", ukuran, "bold")
        )
        self.root.update_idletasks()


# ------------------------------------------------------------------
# Jalankan aplikasi
# ------------------------------------------------------------------
if __name__ == "__main__":
    jendela = tk.Tk()
    Kalkulator(jendela)
    jendela.mainloop()