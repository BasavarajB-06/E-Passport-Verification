import serial
import time
import threading
import tkinter as tk
from PIL import Image, ImageTk
import re, sys, folium, webbrowser, os

# ---------------- Serial Port Configuration ----------------
serial_port = 'COM3'     # Change to your Arduino port
baud_rate = 9600

try:
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    print(f"✅ Connected to {serial_port}")
except serial.SerialException as e:
    print(f"❌ Error connecting to {serial_port}: {e}")
    ser = None

# ---------------- Passenger Data (UID → Details + Travel) ----------------
passenger_data = {
    "3365e924": {  # Ajaykumar
        "passport_number": "ARG246844",
        "full_name": "Ajaykumar C Mendigeri",
        "date_of_birth": "August 27, 2003",
        "nationality": "INDIAN",
        "date_of_issue": "March 05, 2024",
        "date_of_expiry": "March 05, 2034",
        "image_path": "D:\\ajay.jpg",  # ✅ Updated image path
        "travel_history": [
            ("Bengaluru", [12.9716, 77.5946]),
            ("Sydney", [-33.8688, 151.2093]),
            ("California", [36.7783, -119.4179])
        ]
    },
    "13799af7": {  # Basu
        "passport_number": "BRX221144",
        "full_name": "Basu R",
        "date_of_birth": "July 10, 2003",
        "nationality": "INDIAN",
        "date_of_issue": "March 10, 2024",
        "date_of_expiry": "March 10, 2034",
        "image_path": "basu_image.jpg",
        "travel_history": [
            ("Bengaluru", [12.9716, 77.5946]),
            ("Sydney", [-33.8688, 151.2093]),
            ("California", [36.7783, -119.4179])
        ]
    }
}

# ---------------- Helper: Normalize UID ----------------
def normalize_uid(raw_uid: str) -> str:
    return re.sub(r'[^0-9a-f]', '', raw_uid.strip().lower())

# ---------------- GUI Setup ----------------
root = tk.Tk()
root.title("E-PASSPORT VERIFICATION SYSTEM")
root.configure(bg="#fff6d1")

status_lbl = tk.Label(root, text="Waiting for RFID scan...", bg="#fff6d1", font=("Helvetica", 11))
status_lbl.pack(pady=10)

def on_quit():
    try:
        if ser and ser.is_open:
            ser.close()
    except Exception:
        pass
    root.quit(); sys.exit(0)

quit_btn = tk.Button(root, text="Quit (Esc)", command=on_quit)
quit_btn.pack(pady=5)
root.bind("<Escape>", lambda e: on_quit())

# ---------------- Display Passport Window ----------------
def display_passport(passenger):
    top = tk.Toplevel(root)
    top.title("E-PASSPORT VERIFICATION")
    top.configure(bg="#fff6d1")
    top.attributes('-fullscreen', True)
    top.bind("<Escape>", lambda e: top.attributes('-fullscreen', False))

    # ---------- HEADER ----------
    tk.Label(top, text="Republic of India", fg="blue", bg="#fff6d1",
             font=("Helvetica", 22, "bold")).place(relx=0.5, y=40, anchor="center")
    tk.Label(top, text="E-PASSPORT VERIFICATION", fg="black", bg="#fff6d1",
             font=("Helvetica", 26, "bold")).place(relx=0.5, y=90, anchor="center")

    # ---------- PHOTO ----------
    try:
        img = Image.open(passenger.get("image_path", "")).resize((240, 280))
        img_tk = ImageTk.PhotoImage(img)
        tk.Label(top, image=img_tk, bg="#fff6d1").place(x=150, y=200)
        top.img_tk = img_tk
    except Exception as e:
        tk.Label(top, text="No Image Found", bg="#fff6d1", fg="red",
                 font=("Helvetica", 13, "bold")).place(x=170, y=320)
        print("Image error:", e)

    # ---------- DETAILS ----------
    labels = ["Passport Number", "Full Name", "Date of Birth",
               "Nationality", "Date of Issue", "Date of Expiry"]
    values = [passenger["passport_number"], passenger["full_name"],
               passenger["date_of_birth"], passenger["nationality"],
               passenger["date_of_issue"], passenger["date_of_expiry"]]
    start_x, start_y, step = 520, 220, 70
    for i,(lab,val) in enumerate(zip(labels,values)):
        y = start_y + i*step
        tk.Label(top, text=f"{lab}:", font=("Helvetica", 16, "bold"), bg="#fff6d1").place(x=start_x, y=y)
        tk.Label(top, text=val, font=("Helvetica", 15), bg="white",
                 relief="solid", bd=2, anchor="w").place(x=start_x+260, y=y-3, width=420, height=38)

    # ---------- ACCESS APPROVED ----------
    tk.Label(top, text="ACCESS APPROVED", fg="green", bg="#fff6d1",
             font=("Helvetica", 20, "bold")).place(relx=0.5, y=start_y+len(labels)*step+60, anchor="center")

    # ---------- TRAVEL HISTORY BUTTON ----------
    def show_travel_history():
        print(f"Opening travel map for {passenger['full_name']}")
        travel = passenger.get("travel_history", [])
        if not travel:
            return
        m = folium.Map(location=travel[0][1], zoom_start=3, tiles="CartoDB positron")
        for loc,coords in travel:
            folium.Marker(location=coords, popup=loc).add_to(m)
        folium.PolyLine([coords for _,coords in travel], color="blue", weight=3).add_to(m)
        map_file = os.path.abspath("travel_history.html")
        m.save(map_file)
        webbrowser.open(f"file://{map_file}")

    tk.Button(top, text="View Travel History", font=("Helvetica", 14, "bold"),
              bg="#007BFF", fg="white", padx=15, pady=5,
              command=show_travel_history).place(relx=0.5, y=start_y+len(labels)*step+120, anchor="center")

    # ---------- WAITING FOR SCAN ----------
    tk.Label(top, text="WAITING FOR SCAN", fg="white", bg="gray",
             font=("Helvetica", 16, "bold"), padx=20, pady=5).place(relx=0.5, rely=0.93, anchor="center")

# ---------------- Serial Listener Thread ----------------
def serial_listener():
    print("Serial listener running...")
    while True:
        try:
            if ser and ser.in_waiting > 0:
                raw = ser.readline().decode(errors='ignore').strip()
                if not raw: time.sleep(0.1); continue
                uid = normalize_uid(raw)
                print(f"Scanned UID: {uid}")
                root.after(0, status_lbl.config, {"text": f"Scanned UID: {uid}"})
                if uid in passenger_data:
                    root.after(0, display_passport, passenger_data[uid])
                else:
                    root.after(0, status_lbl.config, {"text": "Access Denied – Unknown UID"})
                time.sleep(0.5)
            else:
                time.sleep(0.2)
        except Exception as e:
            print("Serial error:", e); time.sleep(1)

# ---------------- Start Thread & Run App ----------------
if ser:
    threading.Thread(target=serial_listener, daemon=True).start()
else:
    status_lbl.config(text="No serial connection detected.")

root.mainloop()