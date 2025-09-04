import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk, scrolledtext
import json
import os
import re
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import gspread
from google.oauth2.service_account import Credentials

CHROME_DRIVER_PATH = "" # CHROME DRIVER PATH HERE
# LINKS_FILE = "youtube_video_links.json"

class YTCommentScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Bengali Comment Scraper")
        self.root.geometry("750x600")

        self.video_links = []
        self.api_file = None
        self.sheet_id = None
        self.bengali_pattern = re.compile(r"[\u0980-\u09FF]+(?:[\s\u0980-\u09FF.,!?;()\-\"]*[\u0980-\u09FF]+)*")
        self.bengali_comments = []
        self.celeb_name = ""
        self.uploader_name = ""
        self.headless_mode = False 
        self.driver_path = None  


        self.create_menu()
        self.create_widgets()
        # self.load_video_links()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Video Links", command=self.load_video_links_from_file)
        file_menu.add_command(label="Select ChromeDriver", command=self.select_driver_path)
        file_menu.add_separator()
        file_menu.add_command(label="Insert API File", command=self.load_api_file)

        file_menu.add_command(label="Insert Sheet ID", command=self.insert_sheet_id)
        file_menu.add_separator()
        file_menu.add_command(label="Reset API & Sheet ID", command=self.reset_api_credentials)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="Tasks", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="Headless Mode", command=self.toggle_headless, variable=tk.BooleanVar(value=self.headless_mode))
        menubar.add_cascade(label="Settings", menu=view_menu)

        self.root.config(menu=menubar)

    def create_widgets(self):
        tk.Label(self.root, text="YouTube Bengali Comment Scraper", font=("Arial", 14, "bold")).pack(pady=5)
        tk.Label(self.root, text="Developed by Saqib", font=("Arial", 10)).pack(pady=2)
        tk.Label(self.root, text="v0.2", font=("Arial", 8)).pack(pady=2)

        self.status_label = tk.Label(self.root, text="No operation running.", font=("Arial", 10), fg="red")
        self.status_label.pack(pady=5)

        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=5)

        self.driver_canvas, self.driver_led = self.create_indicator(status_frame, "ChromeDriver")
        self.api_canvas, self.api_led = self.create_indicator(status_frame, "API File")
        self.sheet_canvas, self.sheet_led = self.create_indicator(status_frame, "Sheet ID")

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        self.start_btn = tk.Button(btn_frame, text="Start Scraping", command=self.start_scraping, state=tk.DISABLED, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = tk.Button(btn_frame, text="Save to JSON", command=self.save_to_json, state=tk.DISABLED, bg="#2196F3", fg="white", font=("Arial", 12))
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = tk.Button(btn_frame, text="Export to Google Sheet", command=self.append_to_google_sheet, state=tk.DISABLED, bg="#FF9800", fg="white", font=("Arial", 12))
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = tk.Button(self.root, text="Clear Text", command=self.clear_text, bg="#607D8B", fg="white", font=("Arial", 12))
        self.clear_btn.pack(pady=5)

        self.progress = ttk.Progressbar(self.root, length=600, mode='determinate')
        self.progress.pack(pady=5)

        self.text_area = scrolledtext.ScrolledText(self.root, width=85, height=18, font=("Arial", 10))
        self.text_area.pack(pady=10)

        self.update_indicator(self.driver_canvas, self.driver_led, False)
        self.update_indicator(self.api_canvas, self.api_led, False)
        self.update_indicator(self.sheet_canvas, self.sheet_led, False)


    def create_indicator(self, parent, label_text):
        frame = tk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=10)

        label = tk.Label(frame, text=label_text)
        label.pack()

        canvas = tk.Canvas(frame, width=20, height=20, bg=self.root["bg"], highlightthickness=0)
        canvas.pack()
        indicator = canvas.create_oval(2, 2, 18, 18, fill="red")

        return canvas, indicator

    def update_indicator(self, canvas, led, status):
        color = "green" if status else "red"
        canvas.itemconfig(led, fill=color)

    def select_driver_path(self):
        path = filedialog.askopenfilename(title="Select ChromeDriver Executable", filetypes=[("Executable", "*.exe")])
        if path and os.path.isfile(path):
            self.driver_path = path
            self.update_indicator(self.driver_canvas, self.driver_led, True)
            messagebox.showinfo("Driver Selected", f"ChromeDriver path set to:\n{path}")
        else:
            messagebox.showerror("Invalid", "Please select a valid ChromeDriver executable.")

    def toggle_headless(self):
        self.headless_mode = not self.headless_mode
        state = "ON" if self.headless_mode else "OFF"
        messagebox.showinfo("Headless Mode", f"Headless mode is now {state}.")

    # def load_video_links(self):
    #     if os.path.exists(LINKS_FILE):
    #         with open(LINKS_FILE, "r", encoding="utf-8") as f:
    #             self.video_links = json.load(f)
    #     else:
    #         messagebox.showerror("Missing File", f"Cannot find {LINKS_FILE}")

    def load_api_file(self):
        self.api_file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        self.update_indicator(self.api_canvas, self.api_led, True)
        if self.api_file:
            messagebox.showinfo("Loaded", "Google API credentials loaded.")

    def insert_sheet_id(self):
        self.sheet_id = simpledialog.askstring("Input", "Enter Google Sheet ID:")
        self.update_indicator(self.sheet_canvas, self.sheet_led, True)
        if self.sheet_id:
            messagebox.showinfo("Success", "Sheet ID saved.")

    def reset_api_credentials(self):
        self.api_file = None
        self.sheet_id = None
        self.update_indicator(self.api_canvas, self.api_led, False)
        self.update_indicator(self.sheet_canvas, self.sheet_led, False)
        self.export_btn.config(state=tk.DISABLED)
        messagebox.showinfo("Reset", "API credentials reset.")

    def setup_driver(self):
        if not self.driver_path:
            messagebox.showerror("Driver Not Set", "Please select the ChromeDriver file first.")
            raise Exception("ChromeDriver path not set.")

        s = Service(self.driver_path)

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        if self.headless_mode:
            options.add_argument("--headless=new")
        options.add_argument("user-agent=Mozilla/5.0")
        return webdriver.Chrome(service=s, options=options)
    
    def load_video_links_from_file(self):
        file_path = filedialog.askopenfilename(title="Select JSON File", filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.video_links = json.load(f)
                self.start_btn.config(state=tk.NORMAL)
                messagebox.showinfo("Success", f"Loaded {len(self.video_links)} video links.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")


    def start_scraping(self):
        threading.Thread(target=self.scrape_all_videos, daemon=True).start()

    def scrape_all_videos(self):
        self.bengali_comments = []
        self.progress['value'] = 0
        self.status_label.config(text="Scraping in progress...", fg="blue")
        self.text_area.delete("1.0", tk.END)

        try:
            browser = self.setup_driver()
            for idx, entry in enumerate(self.video_links):
                url = entry.get("url", "")
                if not url:
                    continue
                browser.get(url)
                time.sleep(2)

                for _ in range(30):
                    browser.execute_script("window.scrollBy(0,500)")
                    time.sleep(0.4)

                time.sleep(2)
                elements = browser.find_elements(By.CSS_SELECTOR, '.style-scope.ytd-item-section-renderer')
                for el in elements:
                    text = el.text.strip()
                    if self.bengali_pattern.search(text):
                        clean = " ".join(self.bengali_pattern.findall(text))
                        if clean not in self.bengali_comments:
                            self.bengali_comments.append(clean)

                self.progress['value'] = (idx + 1) / len(self.video_links) * 100
                self.root.update_idletasks()

            browser.quit()

            self.text_area.insert(tk.END, "\n".join(f"{i+1}. {c}" for i, c in enumerate(self.bengali_comments[:20])))
            messagebox.showinfo("Done", f"Scraping finished. Found {len(self.bengali_comments)} Bengali comments.")
            self.save_btn.config(state=tk.NORMAL)
            self.export_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Scraping complete.", fg="green")

        except Exception as e:
            self.status_label.config(text="Error occurred.", fg="red")
            messagebox.showerror("Error", str(e))

    def save_to_json(self):
        if not self.bengali_comments:
            messagebox.showerror("No Data", "No comments to save.")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.bengali_comments, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Saved", f"Saved to {save_path}")

    def append_to_google_sheet(self):
        if not self.api_file or not self.sheet_id:
            messagebox.showerror("Missing Info", "Please insert API file and Sheet ID first.")
            return

        self.celeb_name = simpledialog.askstring("Celeb Name", "Enter Celeb name:")
        self.uploader_name = simpledialog.askstring("Uploader Name", "Enter Uploader name:")
        if not self.celeb_name or not self.uploader_name:
            messagebox.showerror("Missing", "Both fields are required.")
            return

        threading.Thread(target=self._append_to_sheet_thread, daemon=True).start()

    def _append_to_sheet_thread(self):
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_file(self.api_file, scopes=scopes)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(self.sheet_id)
            ws = sheet.sheet1

            upload_cnt = 0

            popup = tk.Toplevel()
            popup.title("Uploading Comments")
            popup.geometry("300x100")
            tk.Label(popup, text="Uploading comments...").pack(pady=10)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(popup, variable=progress_var, maximum=100)
            progress_bar.pack(pady=5, padx=10, fill=tk.X)

            progress_step = float(100.0 / len(self.bengali_comments))

            for comment in self.bengali_comments:
                popup.update()
                if upload_cnt == 10:
                    time.sleep(10)
                    upload_cnt = 0
                else:
                    ws.append_row([self.celeb_name, comment, self.uploader_name])
                    progress_var.set(progress_var.get() + progress_step)
                    upload_cnt += 1

            popup.destroy()
            messagebox.showinfo("Success", "Comments appended to Google Sheet!")

        except Exception as e:
            popup.destroy()
            messagebox.showerror("Error", f"Failed to append to Google Sheet: {e}")

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self.status_label.config(text="Text area cleared.", fg="black")

if __name__ == "__main__":
    root = tk.Tk()
    app = YTCommentScraperApp(root)
    root.mainloop()
