import customtkinter as ctk
try:
    app = ctk.CTk()
    app.after(1000, app.destroy)
    app.mainloop()
    print("GUI loop finished")
except Exception as e:
    print(f"GUI Error: {e}")
