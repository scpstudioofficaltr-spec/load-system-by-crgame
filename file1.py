import tkinter as tk
import urllib.request
import io
import ctypes

# Windows Gezgini ve Görev Çubuğu için özel uygulama kimliği (ikonun düzgün görünmesi için)
try:
    myappid = 'scpstudio.selamuygulamasi.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

pencere = tk.Tk()
pencere.title("Selam Uygulaması")
pencere.geometry("300x200")

# İnternetten görseli indirip harici kütüphane (Pillow) kullanmadan ekleme
try:
    url = "https://github.com/scpstudioofficaltr-spec/load-system-by-crgame/raw/refs/heads/main/icoimg"
    
    # GitHub'ın engellememesi için tarayıcı gibi istek atıyoruz
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    with urllib.request.urlopen(req) as connection:
        raw_data = connection.read()
    
    # Tkinter'ın doğrudan okuyabileceği formatta görsel nesnesi oluşturuyoruz
    icon_image = tk.PhotoImage(data=raw_data)
    
    # Hem pencereye hem görev çubuğuna ikonu uyguluyoruz
    pencere.iconphoto(True, icon_image)
    
except Exception as e:
    print(f"İkon yüklenirken hata oluştu: {e}")

etiket = tk.Label(pencere, text="Selam", font=("Arial", 24))
etiket.pack(expand=True)

pencere.mainloop()
