import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import threading
import sys
import shutil
from datetime import datetime

# Import tool functions
from stamp_splitter_v2 import process_splitter
from background_remover import process_remover
from auto_trimmer import process_auto_trimmer
from line_stamp_formatter import process_formatter

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RedirectText(object):
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class StampMakerGUI(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        self.title("LINE Stamp Maker Banana")
        self.geometry("700x850")
        
        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Log area expands

        # --- 1. Input & Output Section ---
        self.io_frame = ctk.CTkFrame(self)
        self.io_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.io_frame.grid_columnconfigure(1, weight=1)

        # Input
        ctk.CTkLabel(self.io_frame, text="入力フォルダ:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.input_path_var = ctk.StringVar()
        self.input_entry = ctk.CTkEntry(self.io_frame, textvariable=self.input_path_var, placeholder_text="ここにフォルダをドラッグ＆ドロップ")
        self.input_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.input_entry.drop_target_register(DND_FILES)
        self.input_entry.dnd_bind('<<Drop>>', self.drop_input)

        self.browse_in_btn = ctk.CTkButton(self.io_frame, text="参照", width=80, command=self.browse_input)
        self.browse_in_btn.grid(row=0, column=2, padx=10, pady=5)

        # Output
        ctk.CTkLabel(self.io_frame, text="出力フォルダ:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.output_path_var = ctk.StringVar(value="output_final")
        self.output_entry = ctk.CTkEntry(self.io_frame, textvariable=self.output_path_var, placeholder_text="出力先フォルダを選択")
        self.output_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.browse_out_btn = ctk.CTkButton(self.io_frame, text="参照", width=80, command=self.browse_output)
        self.browse_out_btn.grid(row=1, column=2, padx=10, pady=5)

        # --- 2. Pipeline Options ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.options_frame.grid_columnconfigure(1, weight=1)

        # Step 1: Split
        self.check_split_var = ctk.BooleanVar(value=True)
        self.check_split = ctk.CTkCheckBox(self.options_frame, text="1. スタンプ分割 (シート→個別)", variable=self.check_split_var, font=("Arial", 12, "bold"))
        self.check_split.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.split_opts = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.split_opts.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(self.split_opts, text="分割数:").pack(side="left", padx=5)
        self.grid_var = ctk.StringVar(value="auto")
        self.grid_combo = ctk.CTkComboBox(self.split_opts, values=["auto", "4x2", "3x3", "4x4"], variable=self.grid_var, width=80)
        self.grid_combo.pack(side="left", padx=5)

        # Step 2: BG Remove
        self.check_bg_var = ctk.BooleanVar(value=False)
        self.check_bg = ctk.CTkCheckBox(self.options_frame, text="2. 背景透過 (単体処理)", variable=self.check_bg_var, font=("Arial", 12, "bold"))
        self.check_bg.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.bg_opts = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.bg_opts.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        # Use grid for better layout control
        ctk.CTkLabel(self.bg_opts, text="モード:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.mode_var = ctk.StringVar(value="flood")
        self.mode_combo = ctk.CTkComboBox(self.bg_opts, values=["flood", "auto_color", "color"], variable=self.mode_var, width=100)
        self.mode_combo.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ctk.CTkLabel(self.bg_opts, text="許容値:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.tol_val_label = ctk.CTkLabel(self.bg_opts, text="30", width=30)
        self.tol_val_label.grid(row=1, column=2, padx=5, pady=2)
        self.tol_slider = ctk.CTkSlider(self.bg_opts, from_=0, to=100, number_of_steps=100, width=120, command=lambda v: self.tol_val_label.configure(text=str(int(v))))
        self.tol_slider.set(30)
        self.tol_slider.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ctk.CTkLabel(self.bg_opts, text="フチ除去:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.ero_val_label = ctk.CTkLabel(self.bg_opts, text="0", width=30)
        self.ero_val_label.grid(row=2, column=2, padx=5, pady=2)
        self.bg_ero_slider = ctk.CTkSlider(self.bg_opts, from_=0, to=10, number_of_steps=10, width=120, command=lambda v: self.ero_val_label.configure(text=str(int(v))))
        self.bg_ero_slider.set(0)
        self.bg_ero_slider.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        # Step 3: Trim
        self.check_trim_var = ctk.BooleanVar(value=True)
        self.check_trim = ctk.CTkCheckBox(self.options_frame, text="3. 自動トリミング (透明部分カット)", variable=self.check_trim_var, font=("Arial", 12, "bold"))
        self.check_trim.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.trim_opts = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.trim_opts.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(self.trim_opts, text="余白:").pack(side="left", padx=5)
        self.pad_var = ctk.StringVar(value="10")
        self.pad_entry = ctk.CTkEntry(self.trim_opts, textvariable=self.pad_var, width=50)
        self.pad_entry.pack(side="left", padx=5)
        ctk.CTkLabel(self.trim_opts, text="px").pack(side="left")

        # Step 4: Format
        self.check_fmt_var = ctk.BooleanVar(value=True)
        self.check_fmt = ctk.CTkCheckBox(self.options_frame, text="4. LINEスタンプ整形 (リサイズ・配置)", variable=self.check_fmt_var, font=("Arial", 12, "bold"))
        self.check_fmt.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(self.options_frame, text="(370x320pxにリサイズ, main/tab画像生成)").grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # --- 3. Execution ---
        self.run_btn = ctk.CTkButton(self, text="処理開始 (RUN)", font=("Arial", 16, "bold"), height=50, command=self.start_process)
        self.run_btn.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

        # --- 4. Log Area ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        
        self.log_text = ctk.CTkTextbox(self.log_frame, state="disabled", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Redirect stdout
        sys.stdout = RedirectText(self.log_text)

    def drop_input(self, event):
        path = event.data
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]
        self.input_path_var.set(path)

    def browse_input(self):
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.input_path_var.set(folder)

    def browse_output(self):
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.output_path_var.set(folder)

    def start_process(self):
        input_dir = self.input_path_var.get()
        output_dir = self.output_path_var.get()

        if not input_dir or not os.path.exists(input_dir):
            print("エラー: 入力フォルダを選択してください。")
            return
        
        if not output_dir:
            print("エラー: 出力フォルダを選択してください。")
            return

        self.run_btn.configure(state="disabled", text="処理中...")
        
        # Run in thread
        thread = threading.Thread(target=self.run_pipeline, args=(input_dir, output_dir))
        thread.start()

    def run_pipeline(self, input_dir, final_output_dir):
        try:
            print(f"--- 処理開始 {datetime.now().strftime('%H:%M:%S')} ---")
            
            current_input = input_dir
            
            # 1. Split
            if self.check_split_var.get():
                output_split = os.path.join(final_output_dir, "temp_split")
                if os.path.exists(output_split): shutil.rmtree(output_split)
                
                print("\n[Step 1] スタンプ画像を分割中...")
                # Splitter defaults: tolerance=50, erosion=1 (hidden from UI)
                # remove_bg=False because we have a separate BG removal step
                process_splitter(
                    current_input, 
                    output_split, 
                    tolerance=50, 
                    erosion=1, 
                    grid=self.grid_var.get(),
                    remove_bg=False
                )
                current_input = output_split

            # 2. BG Remove
            if self.check_bg_var.get():
                output_bg = os.path.join(final_output_dir, "temp_bg")
                if os.path.exists(output_bg): shutil.rmtree(output_bg)
                
                print("\n[Step 2] 背景を透過中...")
                process_remover(
                    current_input, 
                    output_bg, 
                    mode=self.mode_var.get(), 
                    tolerance=int(self.tol_slider.get()),
                    erosion=int(self.bg_ero_slider.get())
                )
                current_input = output_bg

            # 3. Trim
            if self.check_trim_var.get():
                output_trim = os.path.join(final_output_dir, "temp_trim")
                if os.path.exists(output_trim): shutil.rmtree(output_trim)
                
                print("\n[Step 3] 透明部分をトリミング中...")
                try:
                    padding = int(self.pad_var.get())
                except:
                    padding = 10
                
                process_auto_trimmer(current_input, output_trim, padding=padding)
                current_input = output_trim

            # 4. Format
            if self.check_fmt_var.get():
                print("\n[Step 4] LINEスタンプ形式に整形中...")
                process_formatter(current_input, final_output_dir)
                print(f"\n完了！ 出力先: {os.path.abspath(final_output_dir)}")
            else:
                print(f"\n処理完了。 最終出力: {os.path.abspath(current_input)}")

        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.run_btn.configure(state="normal", text="処理開始 (RUN)")
            print("\n--- 終了 ---")

if __name__ == "__main__":
    app = StampMakerGUI()
    app.mainloop()
