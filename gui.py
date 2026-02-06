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
        self.grid_rowconfigure(6, weight=1) # Log area expands

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
        self.check_trim_var = ctk.BooleanVar(value=False)
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

        # --- main/tab 再生成セクション ---
        self.maintab_frame = ctk.CTkFrame(self)
        self.maintab_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.maintab_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.maintab_frame, text="main/tab 再生成", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # 選択した画像のパス表示
        self.selected_img_var = ctk.StringVar(value="画像を選択してください")
        self.selected_img_label = ctk.CTkLabel(self.maintab_frame, textvariable=self.selected_img_var, anchor="w")
        self.selected_img_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 画像選択ボタン
        self.select_img_btn = ctk.CTkButton(self.maintab_frame, text="画像選択", width=80, command=self.select_image_for_maintab)
        self.select_img_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 生成ボタン
        self.gen_maintab_btn = ctk.CTkButton(self.maintab_frame, text="生成", width=60, command=self.generate_maintab)
        self.gen_maintab_btn.grid(row=0, column=3, padx=5, pady=5)

        # --- 完成後調整セクション ---
        self.finish_frame = ctk.CTkFrame(self)
        self.finish_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.finish_frame.grid_columnconfigure(1, weight=1)
        
        # 行0: ラベルとボタン群
        ctk.CTkLabel(self.finish_frame, text="完成後調整", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.finish_btns_frame = ctk.CTkFrame(self.finish_frame, fg_color="transparent")
        self.finish_btns_frame.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # 出力フォルダを開くボタン
        self.open_folder_btn = ctk.CTkButton(self.finish_btns_frame, text="出力フォルダを開く", width=140, command=self.open_output_folder)
        self.open_folder_btn.pack(side="left", padx=5, pady=5)
        
        # ZIP作成ボタン
        self.create_zip_btn = ctk.CTkButton(self.finish_btns_frame, text="ZIPファイル作成", width=120, command=self.create_zip)
        self.create_zip_btn.pack(side="left", padx=5, pady=5)
        
        # ウォーターマーク削除ボタン (9の倍数)
        self.delete_watermark_btn = ctk.CTkButton(self.finish_btns_frame, text="🍌💣", width=60, command=self.delete_watermark_files)
        self.delete_watermark_btn.pack(side="left", padx=5, pady=5)
        
        # 行1: プレフィックスと日付オプション
        self.zip_opts_frame = ctk.CTkFrame(self.finish_frame, fg_color="transparent")
        self.zip_opts_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(self.zip_opts_frame, text="プレフィックス:").pack(side="left", padx=5)
        self.prefix_var = ctk.StringVar(value="")
        self.prefix_entry = ctk.CTkEntry(self.zip_opts_frame, textvariable=self.prefix_var, width=120, placeholder_text="例: cat, dog")
        self.prefix_entry.pack(side="left", padx=5)
        
        self.date_var = ctk.BooleanVar(value=True)  # デフォルトON
        self.date_check = ctk.CTkCheckBox(self.zip_opts_frame, text="ファイル名に日付を入れる", variable=self.date_var)
        self.date_check.pack(side="left", padx=15)

        # --- 4. Log Area ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")
        
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

    def select_image_for_maintab(self):
        """main/tab生成用の画像をファイルダイアログで選択"""
        # 出力フォルダをデフォルトの開始位置にする
        initial_dir = self.output_path_var.get()
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
        
        file_path = ctk.filedialog.askopenfilename(
            title="main/tab生成用の画像を選択",
            initialdir=initial_dir,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_img_var.set(os.path.basename(file_path))
            self._selected_img_path = file_path  # フルパスを保持
            print(f"選択: {file_path}")
    
    def generate_maintab(self):
        """選択した画像からmain.pngとtab.pngを生成"""
        import cv2
        import numpy as np
        from line_stamp_formatter import resize_and_pad, resize_exact
        
        # 画像が選択されているか確認
        if not hasattr(self, '_selected_img_path') or not os.path.exists(self._selected_img_path):
            print("エラー: 画像を選択してください。")
            return
        
        # 出力フォルダを確認
        output_dir = self.output_path_var.get()
        if not output_dir or not os.path.exists(output_dir):
            print("エラー: 出力フォルダが存在しません。")
            return
        
        try:
            # 画像読み込み
            img = cv2.imdecode(np.fromfile(self._selected_img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if img is None:
                print("エラー: 画像を読み込めませんでした。")
                return
            
            # 4チャンネル確認
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
            elif img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            
            # main.png生成 (240x240)
            main_img = resize_and_pad(img, 240, 240, margin=0)
            main_path = os.path.join(output_dir, "main.png")
            cv2.imencode(".png", main_img)[1].tofile(main_path)
            print(f"生成: {main_path}")
            
            # tab.png生成 (96x74)
            tab_img = resize_exact(img, 96, 74)
            tab_path = os.path.join(output_dir, "tab.png")
            cv2.imencode(".png", tab_img)[1].tofile(tab_path)
            print(f"生成: {tab_path}")
            
            print("main/tab 再生成完了！")
            
        except Exception as e:
            print(f"エラー: {e}")

    def open_output_folder(self):
        """出力フォルダをエクスプローラで開く"""
        import subprocess
        output_dir = self.output_path_var.get()
        
        if not output_dir or not os.path.exists(output_dir):
            print("エラー: 出力フォルダが存在しません。")
            return
        
        # Windowsでエクスプローラを開く
        subprocess.Popen(['explorer', os.path.abspath(output_dir)])
        print(f"フォルダを開きました: {os.path.abspath(output_dir)}")
    
    def create_zip(self):
        """出力フォルダをZIPファイルに圧縮（連番リネーム付き）+ フォルダも同時出力"""
        import zipfile
        from datetime import datetime
        import re
        
        output_dir = self.output_path_var.get()
        
        if not output_dir or not os.path.exists(output_dir):
            print("エラー: 出力フォルダが存在しません。")
            return
        
        # 基本名を生成
        prefix = self.prefix_var.get().strip()
        include_date = self.date_var.get()
        
        # 基本パーツを組み立て
        name_parts = []
        if prefix:
            name_parts.append(prefix)
        if include_date:
            name_parts.append(datetime.now().strftime("%Y%m%d"))
        
        base_name = "_".join(name_parts) if name_parts else ""
        
        # 連番を計算 (既存ファイル/フォルダをチェック)
        parent_dir = os.path.dirname(output_dir)
        set_num = 1
        
        while True:
            if base_name:
                full_name = f"{base_name}_Set{set_num:02d}"
            else:
                full_name = f"Set{set_num:02d}"
            
            zip_path = os.path.join(parent_dir, f"{full_name}.zip")
            folder_path = os.path.join(parent_dir, full_name)
            
            if not os.path.exists(zip_path) and not os.path.exists(folder_path):
                break
            set_num += 1
        
        try:
            # ファイルを取得してソート
            all_files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
            
            # main.pngとtab.pngを分離
            special_files = [f for f in all_files if f.lower() in ['main.png', 'tab.png']]
            stamp_files = [f for f in all_files if f.lower() not in ['main.png', 'tab.png'] and f.lower().endswith('.png')]
            stamp_files.sort()  # ソート
            
            # フォルダ作成
            os.makedirs(folder_path, exist_ok=True)
            
            # スタンプ画像を連番リネームしてフォルダにコピー
            for i, file in enumerate(stamp_files, start=1):
                src_path = os.path.join(output_dir, file)
                new_name = f"{i:02d}.png"  # 01.png, 02.png...
                dst_path = os.path.join(folder_path, new_name)
                shutil.copy2(src_path, dst_path)
            
            # main.pngとtab.pngはそのままコピー
            for file in special_files:
                src_path = os.path.join(output_dir, file)
                dst_path = os.path.join(folder_path, file)
                shutil.copy2(src_path, dst_path)
            
            # ZIPファイル作成（フォルダの中身を圧縮）
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    zipf.write(file_path, file)
            
            total_count = len(stamp_files) + len(special_files)
            print(f"\n出力完了!")
            print(f"  ZIP: {zip_path}")
            print(f"  フォルダ: {folder_path}")
            print(f"  スタンプ: {len(stamp_files)}個 (01.png〜{len(stamp_files):02d}.png にリネーム)")
            print(f"  合計: {total_count}個のファイル")
            
            # ZIPファイルの場所を開く
            import subprocess
            subprocess.Popen(['explorer', '/select,', os.path.abspath(zip_path)])
            
        except Exception as e:
            print(f"ZIP作成エラー: {e}")

    def delete_watermark_files(self):
        """9の倍数のウォーターマーク画像を削除 (09.png, 18.png, 27.png, 36.png, 45.png...)"""
        output_dir = self.output_path_var.get()
        
        if not output_dir or not os.path.exists(output_dir):
            print("エラー: 出力フォルダが存在しません。")
            return
        
        deleted_files = []
        
        # 9の倍数のファイルを検索して削除
        for i in range(9, 1000, 9):  # 9, 18, 27, 36, 45, ...
            filename = f"{i:02d}.png"
            file_path = os.path.join(output_dir, filename)
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(filename)
                except Exception as e:
                    print(f"削除エラー ({filename}): {e}")
        
        if deleted_files:
            print(f"🍌💣 削除完了: {', '.join(deleted_files)}")
            print(f"合計 {len(deleted_files)} 個のウォーターマーク画像を削除しました。")
        else:
            print("削除対象のウォーターマーク画像が見つかりませんでした。")

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

            # 一時フォルダを削除
            temp_folders = ["temp_split", "temp_bg", "temp_trim"]
            for folder in temp_folders:
                temp_path = os.path.join(final_output_dir, folder)
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path)
                    print(f"一時フォルダ削除: {folder}")

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
